__author__ = "aiXplain"

"""
Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: March 20th 2023
Description:
    Function Enum
"""
import logging
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from enum import Enum
from urllib.parse import urljoin
from aixplain.utils.asset_cache import AssetCache, CACHE_FOLDER
from typing import Tuple, Dict
from aixplain.base.parameters import BaseParameters, Parameter
import os

CACHE_FILE = f"{CACHE_FOLDER}/functions.json"
LOCK_FILE = f"{CACHE_FILE}.lock"

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class FunctionMetadata:
    id: str
    name: str
    description: Optional[str] = None
    params: List[Dict[str, Any]] = field(default_factory=list)
    output: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "params": self.params,
            "output": self.output,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            params=data.get("params", []),
            output=data.get("output", []),
            metadata={k: v for k, v in data.items() if k not in {"id", "name", "description", "params", "output"}},
        )


def load_functions():
    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    os.makedirs(CACHE_FOLDER, exist_ok=True)

    url = urljoin(backend_url, "sdk/functions")
    cache = AssetCache(FunctionMetadata, cache_filename="functions")
    if cache.has_valid_cache():
        logging.info("Loading functions from cache...")
        function_objects = list(cache.store.data.values())
    else:
        logging.info("Fetching functions from backend...")
        url = urljoin(backend_url, "sdk/functions")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        if not 200 <= r.status_code < 300:
            raise Exception(
                f'Functions could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
            )
        resp = r.json()
        results = resp.get("results")
        function_objects = [FunctionMetadata.from_dict(f) for f in results]
        cache.add_list(function_objects)

    class Function(str, Enum):
        def __new__(cls, value):
            obj = str.__new__(cls, value)
            obj._value_ = value
            obj._parameters = None  # Initialize _parameters as None
            return obj

        def get_input_output_params(self) -> Tuple[Dict, Dict]:
            """Gets the input and output parameters for this function

            Returns:
                Tuple[Dict, Dict]: A tuple containing (input_params, output_params)
            """
            function_io = FunctionInputOutput.get(self.value, None)
            if function_io is None:
                return {}, {}
            input_params = {
                param["code"]: param for param in function_io["spec"]["params"]
            }
            output_params = {
                param["code"]: param for param in function_io["spec"]["output"]
            }
            return input_params, output_params

        def get_parameters(self) -> "FunctionParameters":
            """Gets a FunctionParameters object for this function

            Returns:
                FunctionParameters: Object containing the function's parameters
            """
            if self._parameters is None:
                input_params, _ = self.get_input_output_params()
                self._parameters = FunctionParameters(input_params)
            return self._parameters

    functions = Function(
        "Function", {f.id.upper().replace("-", "_"): f.id for f in function_objects}
    )
    functions_input_output = {
        f.id: {
            "input": {p["dataType"] for p in f.params if p.get("required")},
            "output": {o["dataType"] for o in f.output},
            "spec": f.to_dict(),
        }
        for f in function_objects
    }

    return functions, functions_input_output


class FunctionParameters(BaseParameters):
    """Class to store and manage function parameters"""

    def __init__(self, input_params: Dict):
        """Initialize FunctionParameters with input parameters

        Args:
            input_params (Dict): Dictionary of input parameters
        """
        super().__init__()
        for param_code, param_config in input_params.items():
            self.parameters[param_code] = Parameter(
                name=param_code,
                required=param_config.get("required", False),
                value=None,
            )


Function, FunctionInputOutput = load_functions()