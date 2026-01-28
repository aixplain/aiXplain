"""Generate static enum modules from backend API data."""

import re
import os
import requests
from urllib.parse import urljoin
from jinja2 import Environment, BaseLoader
from dotenv import load_dotenv

load_dotenv()

# Note: We don't import anything from aixplain.* here to avoid circular
# dependency. All configuration is handled via environment variables.


def enumify(s):
    """Slugify a string and convert to uppercase."""
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[-.]+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9-_.]+", "", s)
    s = s.upper()

    # Handle numeric-only strings by prefixing with underscore
    if s.isdigit():
        s = f"_{s}"

    return s


def none_to_none(value):
    """Convert None to string 'None' for Python code generation."""
    if value is None:
        return "None"
    return value


def escape_quotes(value):
    """Escape double quotes in strings for Python code generation."""
    if value is None:
        return ""
    return value.replace('"', '\\"')


SEGMENTOR_FUNCTIONS = [
    "split-on-linebreak",
    "speaker-diarization-audio",
    "voice-activity-detection",
]

RECONSTRUCTOR_FUNCTIONS = ["text-reconstruction", "audio-reconstruction"]

# Centralized enum generation - only generate in main enums directory
ENUMS_MODULE_PATH = "aixplain/enums/generated_enums.py"
PIPELINE_MODULE_PATH = "aixplain/modules/pipeline/pipeline.py"

ENUMS_MODULE_TEMPLATE = """\"\"\"Auto-generated enum module containing static values from the backend API.\"\"\"

# This is an auto generated module. PLEASE DO NOT EDIT
# This module contains static enums that were previously loaded dynamically

from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from aixplain.base.parameters import BaseParameters, Parameter


class Function(str, Enum):
    \"\"\"Enum representing available functions in the aiXplain platform.\"\"\"

    {% for function in functions %}
    {{ function.id|enumify }} = "{{ function.id }}"
    {% endfor %}

    def get_input_output_params(self) -> Tuple[Dict, Dict]:
        \"\"\"Get the input and output parameters for this function.

        Returns:
            Tuple[Dict, Dict]: A tuple containing (input_params, output_params).
        \"\"\"
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
        \"\"\"Get a FunctionParameters object for this function.

        Returns:
            FunctionParameters: Object containing the function's parameters.
        \"\"\"
        if not hasattr(self, '_parameters') or self._parameters is None:
            input_params, _ = self.get_input_output_params()
            self._parameters = FunctionParameters(input_params)
        return self._parameters

# Static FunctionInputOutput dictionary
FunctionInputOutput = {
    {% for function in functions %}
    "{{ function.id }}": {
        "input": {
            {% for param in function.params %}
            {% if param.required %}"{{ param.dataType }}"{% if not loop.last %}, {% endif %}{% endif %}
            {% endfor %}
        },
        "output": {
            {% for output in function.output %}"{{ output.dataType }}"{% if not loop.last %}, {% endif %}{% endfor %}
        },
        "spec": {
            "id": "{{ function.id }}",
            "name": "{{ function.name }}",
            "description": "{{ function.metaData.description|escape_quotes }}",
            "params": [
                {% for param in function.params %}
                {
                    "code": "{{ param.code }}",
                    "dataType": "{{ param.dataType }}",
                    "required": {{ param.required }},
                    "multipleValues": {{ param.multipleValues|default(false) }},
                    "defaultValues": {{ param.defaultValues|none_to_none|default("None") }},
                    "isFixed": {{ param.isFixed|default(false) }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ],
            "output": [
                {% for output in function.output %}
                {
                    "code": "{{ output.code }}",
                    "dataType": "{{ output.dataType }}",
                    "defaultValue": {{ output.defaultValue|none_to_none|default("None") }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
}

class FunctionParameters(BaseParameters):
    \"\"\"Class to store and manage function parameters.\"\"\"

    def __init__(self, input_params: Dict):
        \"\"\"Initialize FunctionParameters with input parameters.

        Args:
            input_params (Dict): Dictionary of input parameters.
        \"\"\"
        super().__init__()
        for param_code, param_config in input_params.items():
            self.parameters[param_code] = Parameter(
                name=param_code,
                required=param_config.get("required", False),
                value=None,
            )


class Supplier(Enum):
    \"\"\"Enum representing available suppliers in the aiXplain platform.\"\"\"

    {% for supplier in suppliers %}
    {{ supplier.code|enumify }} = {
        "id": {{ supplier.id }},
        "name": "{{ supplier.name }}",
        "code": "{{ supplier.code }}"
    }
    {% endfor %}

    def __str__(self):
        \"\"\"Return the supplier name.\"\"\"
        return self.value["name"]


class Language(Enum):
    \"\"\"Enum representing available languages in the aiXplain platform.\"\"\"

    {% for language in languages %}
    {{ language.label|enumify }} = {
        "language": "{{ language.value }}",
        "dialect": ""
    }
    {% for dialect in language.dialects %}
    {{ language.label|enumify }}_{{ dialect.label|enumify }} = {
        "language": "{{ language.value }}",
        "dialect": "{{ dialect.value }}"
    }
    {% endfor %}
    {% endfor %}


class License(str, Enum):
    \"\"\"Enum representing available licenses in the aiXplain platform.\"\"\"

    {% for license in licenses %}
    {{ license.name|enumify }} = "{{ license.id }}"
    {% endfor %}

"""

PIPELINE_MODULE_TEMPLATE = """\"\"\"Auto-generated pipeline module containing node classes and Pipeline factory methods.\"\"\"

# This is an auto generated module. PLEASE DO NOT EDIT


from typing import Union, Type
from aixplain.enums import DataType

from .designer import (
    InputParam,
    OutputParam,
    Inputs,
    Outputs,
    TI,
    TO,
    AssetNode,
    BaseReconstructor,
    BaseSegmentor,
    BaseMetric
)
from .default import DefaultPipeline
from aixplain.modules import asset

{% for spec in specs %}

class {{ spec.class_name }}Inputs(Inputs):
    \"\"\"Input parameters for {{ spec.class_name }}.\"\"\"

{% for input in spec.inputs %}
    {{ input.name }}: InputParam = None
{% endfor %}

    def __init__(self, node=None):
        \"\"\"Initialize {{ spec.class_name }}Inputs.\"\"\"
        super().__init__(node=node)
{% for input in spec.inputs %}
        self.{{ input.name }} = self.create_param(
            code="{{ input.name }}",
            data_type=DataType.{{ input.data_type | upper }},
            is_required={{ input.is_required }}
        )
{% endfor %}


class {{ spec.class_name }}Outputs(Outputs):
    \"\"\"Output parameters for {{ spec.class_name }}.\"\"\"

{% for output in spec.outputs %}
    {{ output.name }}: OutputParam = None
{% endfor %}
{% if spec.is_segmentor %}
    audio: OutputParam = None
{% endif %}

    def __init__(self, node=None):
        \"\"\"Initialize {{ spec.class_name }}Outputs.\"\"\"
        super().__init__(node=node)
{% for output in spec.outputs %}
        self.{{ output.name }} = self.create_param(
            code="{{ output.name }}",
            data_type=DataType.{{ output.data_type | upper }}
        )
{% endfor %}
{% if spec.is_segmentor %}
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)
{% endif %}


class {{ spec.class_name }}({{spec.base_class}}[{{ spec.class_name }}Inputs, {{ spec.class_name }}Outputs]):
    \"\"\"{{ spec.class_name }} node.

    {{ spec.description | wordwrap }}

    InputType: {{ spec.input_type }}
    OutputType: {{ spec.output_type }}
    \"\"\"
    function: str = "{{ spec.id }}"
    input_type: str = DataType.{{ spec.input_type | upper }}
    output_type: str = DataType.{{ spec.output_type | upper }}

    inputs_class: Type[TI] = {{ spec.class_name }}Inputs
    outputs_class: Type[TO] = {{ spec.class_name }}Outputs

{% endfor %}


class Pipeline(DefaultPipeline):
    \"\"\"Pipeline class for creating and managing AI processing pipelines.\"\"\"

{% for spec in specs %}
    def {{ spec.function_name }}(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> {{ spec.class_name }}:
        \"\"\"Create a {{ spec.class_name }} node.

        {{ spec.description | wordwrap }}
        \"\"\"
        return {{ spec.class_name }}(*args, asset_id=asset_id, pipeline=self, **kwargs)

{% endfor %}
"""


def get_config():
    """Get configuration from environment variables."""
    return {
        "TEAM_API_KEY": os.getenv("TEAM_API_KEY"),
        "BACKEND_URL": os.getenv("BACKEND_URL", "https://api.aixplain.com/"),
    }


def api_request(path: str):
    """Fetch functions from the backend."""
    config = get_config()
    api_key = config["TEAM_API_KEY"]
    backend_url = config["BACKEND_URL"]

    if not api_key:
        raise ValueError("TEAM_API_KEY environment variable is required")

    url = urljoin(backend_url, f"sdk/{path}")
    headers = {
        "Content-Type": "application/json",
    }

    headers["x-api-key"] = api_key

    r = requests.get(url, headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"{path} could not be loaded, see error below")
        raise e
    return r.json()


def fetch_functions():
    """Fetch functions from the backend."""
    return api_request("functions")["items"]


def fetch_suppliers():
    """Fetch suppliers from the backend."""
    return api_request("suppliers")


def fetch_languages():
    """Fetch languages from the backend."""
    return api_request("languages")


def fetch_licenses():
    """Fetch licenses from the backend."""
    return api_request("licenses")


def populate_data_types(functions: list):
    """Populate the data types."""
    data_types = set()
    for function in functions:
        for param in function["params"]:
            data_types.add(param["dataType"])
        for output in function["output"]:
            data_types.add(output["dataType"])
    return data_types


def populate_specs(functions: list):
    """Populate the function class specs."""
    function_class_specs = []
    for function in functions:
        # Utility functions has dynamic input parameters so they are not
        # subject to static class generation
        if function["id"] == "utilities":
            continue

        # slugify function name by trimming some special chars and
        # transforming it to snake case
        function_name = function["id"].replace("-", "_").replace("(", "_").replace(")", "_")
        base_class = "AssetNode"
        is_segmentor = function["id"] in SEGMENTOR_FUNCTIONS
        is_reconstructor = function["id"] in RECONSTRUCTOR_FUNCTIONS
        if is_segmentor:
            base_class = "BaseSegmentor"
        elif is_reconstructor:
            base_class = "BaseReconstructor"
        elif "metric" in function_name.split("_"):  # TODO: Advise a better distinguisher please
            base_class = "BaseMetric"

        spec = {
            "id": function["id"],
            "is_segmentor": function["id"] in SEGMENTOR_FUNCTIONS,
            "is_reconstructor": function["id"] in RECONSTRUCTOR_FUNCTIONS,
            "function_name": function_name,
            "base_class": base_class,
            "class_name": "".join([w.title() for w in function_name.split("_")]),
            "description": function["metaData"]["description"],
            "input_type": function["metaData"]["InputType"],
            "output_type": function["metaData"]["OutputType"],
            "inputs": [
                {
                    "name": param["code"],
                    "data_type": param["dataType"],
                    "is_required": param["required"],
                    "is_list": param.get("multipleValues", False),
                    "default": param.get("defaultValues"),
                    "is_fixed": param.get("isFixed", False),
                }
                for param in function["params"]
            ],
            "outputs": [
                {
                    "name": output["code"],
                    "data_type": output["dataType"],
                    "default": output.get("defaultValue"),
                }
                for output in function["output"]
            ],
        }

        function_class_specs.append(spec)

    return function_class_specs


if __name__ == "__main__":
    print("Fetching function specs")

    functions = fetch_functions()
    suppliers = fetch_suppliers()
    languages = fetch_languages()
    licenses = fetch_licenses()
    data_types = populate_data_types(functions)
    specs = populate_specs(functions)

    print(f"Populating module with {len(data_types)} data types and {len(specs)} specs")
    env = Environment(
        loader=BaseLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["enumify"] = enumify
    env.filters["none_to_none"] = none_to_none
    env.filters["escape_quotes"] = escape_quotes

    # Generate pipeline module
    pipeline_template = env.from_string(PIPELINE_MODULE_TEMPLATE)
    pipeline_output = pipeline_template.render(data_types=data_types, specs=specs)

    print(f"Writing module to file: {PIPELINE_MODULE_PATH}")
    with open(PIPELINE_MODULE_PATH, "w") as f:
        f.write(pipeline_output)

    # Generate centralized enums file
    enums_template = env.from_string(ENUMS_MODULE_TEMPLATE)
    enums_output = enums_template.render(
        functions=functions, suppliers=suppliers, languages=languages, licenses=licenses
    )
    print(f"Writing centralized enums module to file: {ENUMS_MODULE_PATH}")
    with open(ENUMS_MODULE_PATH, "w") as f:
        f.write(enums_output)

    print("Modules generated successfully")
