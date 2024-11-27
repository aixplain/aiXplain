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
import logging
import time
from datetime import datetime, timedelta
import json
import os

CACHE_FILE = ".aixplain_cache/functions.json"
CACHE_DURATION = timedelta(hours=24)

def save_to_cache(functions, functions_input_output):
    def convert_sets(obj):
        if isinstance(obj, dict): return {k: convert_sets(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [convert_sets(i) for i in obj]
        elif isinstance(obj, set): return list(obj)
        else: return obj
    cache_data = {"timestamp": time.time(), "functions": {"enum": {name: value for name, value in functions.__members__.items()}, "input_output": convert_sets(functions_input_output)}}
    temp_file = CACHE_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True); json_str = json.dumps(cache_data); logging.info(f"Serialized JSON size: {len(json_str)} bytes")
        with open(temp_file, "w") as f:
            f.write(json_str); f.flush(); os.fsync(f.fileno())
        os.replace(temp_file, CACHE_FILE); logging.info("Cache saved successfully.")
    except Exception as e: logging.error(f"Failed to save cache: {e}")

def convert_lists_to_sets(obj):
    if isinstance(obj, dict): return {k: convert_lists_to_sets(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if all(isinstance(i, (str, int, float, bool, tuple)) for i in obj): return set(obj)
        else: return [convert_lists_to_sets(i) for i in obj]
    else: return obj

def load_from_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f); timestamp = cache_data["timestamp"]
            functions_enum = Enum("Function", {name: value for name, value in cache_data["functions"]["enum"].items()}, type=str)
            functions_input_output = convert_lists_to_sets(cache_data["functions"]["input_output"])
            logging.info(functions_enum); return functions_enum, functions_input_output, timestamp
    except json.JSONDecodeError as e:
        logging.error(f"Cache file is incomplete or corrupted: {e}"); raise e
def load_functions():
    if os.path.exists(CACHE_FILE):
        try:
            functions, functions_input_output, timestamp = load_from_cache(); cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time < CACHE_DURATION: return functions, functions_input_output
        except Exception as e: logging.warning(f"Failed to load cache: {e}. Refreshing functions.")

    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    url = urljoin(backend_url, "sdk/functions")

    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    r = _request_with_retry("get", url, headers=headers)
    if not 200 <= r.status_code < 300:
        raise Exception(
            f'Functions could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
        )
    resp = r.json()
    functions = Enum("Function", {w["id"].upper().replace("-", "_"): w["id"] for w in resp["items"]}, type=str)
    functions_input_output = {
        function["id"]: {
            "input": {
                input_data_object["dataType"]
                for input_data_object in function["params"]
                if input_data_object["required"] is True
            },
            "output": {output_data_object["dataType"] for output_data_object in function["output"]},
            "spec": function,
        }
        for function in resp["items"]
    }
    save_to_cache(functions, functions_input_output)
    return functions, functions_input_output

Function, FunctionInputOutput = load_functions()
