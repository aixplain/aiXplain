__author__ = "thiagocastroferreira"

import json
import logging
from aixplain.utils.file_utils import _request_with_retry
from typing import Callable, Dict, List, Text, Tuple, Union, Optional
from aixplain.exceptions import get_error_from_status_code


def build_payload(data: Union[Text, Dict], parameters: Optional[Dict] = None, stream: Optional[bool] = None):
    from aixplain.factories import FileFactory

    if parameters is None:
        parameters = {}

    if stream is not None:
        if "options" not in parameters:
            parameters["options"] = {}
        parameters["options"]["stream"] = stream

    data = FileFactory.to_link(data)
    if isinstance(data, dict):
        payload = data
    else:
        try:
            payload = json.loads(data)
            if isinstance(payload, dict) is False:
                if isinstance(payload, int) is True or isinstance(payload, float) is True:
                    payload = str(payload)
                payload = {"data": payload}
        except Exception:
            parameters["data"] = data
            payload = {"data": data}
    payload.update(parameters)
    payload = json.dumps(payload)
    return payload


def call_run_endpoint(url: Text, api_key: Text, payload: Dict) -> Dict:
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    resp = "unspecified error"
    try:
        logging.debug(f"Calling {url} with payload: {payload}")
        r = _request_with_retry("post", url, headers=headers, data=payload)
        resp = r.json()
    except Exception as e:
        logging.error(f"Error in request: {e}")
        response = {
            "status": "FAILED",
            "completed": True,
            "error_message": "Model Run: An error occurred while processing your request.",
        }

    if 200 <= r.status_code < 300:
        logging.info(f"Result of request: {r.status_code} - {resp}")
        status = resp.get("status", "IN_PROGRESS")
        data = resp.get("data", None)
        if status == "IN_PROGRESS":
            if data is not None:
                response = {"status": status, "url": data, "completed": True}
            else:
                response = {
                    "status": "FAILED",
                    "completed": True,
                    "error_message": "Model Run: An error occurred while processing your request.",
                }
        else:
            response = resp
    else:
        error_details = resp["error"] if isinstance(resp, dict) and "error" in resp else resp
        status_code = r.status_code
        error = get_error_from_status_code(status_code, error_details)

        logging.error(f"Error in request: {r.status_code}: {error}")
        response = {"status": "FAILED", "error_message": error.message, "completed": True}
    return response


def parse_code(code: Union[Text, Callable]) -> Tuple[Text, List, Text, Text]:
    import inspect
    import os
    import re
    import requests
    import validators
    from aixplain.enums import DataType
    from aixplain.modules.model.utility_model import UtilityModelInput
    from aixplain.factories.file_factory import FileFactory
    from uuid import uuid4

    inputs, description, name = [], "", ""

    if isinstance(code, Callable):
        str_code = inspect.getsource(code)
        description = code.__doc__.strip() if code.__doc__ else ""
        name = code.__name__
    elif os.path.exists(code):
        with open(code, "r") as f:
            str_code = f.read()
    elif validators.url(code):
        str_code = requests.get(code).text
    else:
        str_code = code
    # assert str_code has a main function
    if "def main(" not in str_code:
        raise Exception("Utility Model Error: Code must have a main function")
    # get name of the function
    name = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", str_code).group(1)
    if not description:
        # if the description is not provided, get the docstring of the function from string code after defining the function
        # the docstring is the first line after the function definition
        regex = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\).*?(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|\#\s*(.*?)(?:\n|$)|$)'
        match = re.search(regex, str_code, re.DOTALL)
        if match:
            function_name, params, triple_double_quote_doc, triple_single_quote_doc, single_line_comment = match.groups()
            # Use the first non-None docstring found
            description = (triple_double_quote_doc or triple_single_quote_doc or single_line_comment or "").strip()
        else:
            raise Exception(
                "Utility Model Error:If the function is not decorated with @utility_tool, the description must be provided in the docstring"
            )
    # get parameters of the function
    params_match = re.search(r"def\s+\w+\s*\((.*?)\)\s*(?:->.*?)?:", str_code)
    parameters = params_match.group(1).split(",") if params_match else []

    for input in parameters:
        assert (
            len(input.split(":")) > 1
        ), "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"
        input_name, input_type = input.split(":")
        input_name = input_name.strip()
        input_type = input_type.split("=")[0].strip()

        if input_type in ["int", "float"]:
            input_type = "number"
            inputs.append(
                UtilityModelInput(name=input_name, type=DataType.NUMBER, description=f"The {input_name} input is a number")
            )
        elif input_type == "bool":
            input_type = "boolean"
            inputs.append(
                UtilityModelInput(name=input_name, type=DataType.BOOLEAN, description=f"The {input_name} input is a boolean")
            )
        elif input_type == "str":
            input_type = "text"
            inputs.append(
                UtilityModelInput(name=input_name, type=DataType.TEXT, description=f"The {input_name} input is a text")
            )
        else:
            raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")

    local_path = str(uuid4())
    with open(local_path, "w") as f:
        f.write(str_code)
    code = FileFactory.upload(local_path=local_path, is_temp=True)
    os.remove(local_path)
    return code, inputs, description, name


def parse_code_decorated(code: Union[Text, Callable]) -> Tuple[Text, List, Text]:
    import inspect
    import os
    import re
    import requests
    import validators
    from uuid import uuid4
    from aixplain.enums import DataType
    from aixplain.modules.model.utility_model import UtilityModelInput

    from typing import Callable
    from aixplain.factories.file_factory import FileFactory

    inputs, description, name = [], "", ""
    str_code = ""

    # Add explicit type checking for class instances
    if inspect.isclass(code) or (not isinstance(code, (str, Callable)) and hasattr(code, "__class__")):
        raise TypeError(
            f"Code must be either a string or a callable function, not a class or class instance. You tried to pass a class or class instance: {code}"
        )

    if isinstance(code, Callable) and hasattr(code, "_is_utility_tool"):
        str_code = inspect.getsource(code)
        # Use the information directly from the decorated callable
        description = (
            getattr(code, "_tool_description", None)
            if hasattr(code, "_tool_description")
            else code.__doc__.strip()
            if code.__doc__
            else ""
        )
        name = getattr(code, "_tool_name", None) if hasattr(code, "_tool_name") else ""
        if hasattr(code, "_tool_inputs") and code._tool_inputs != []:
            inputs = getattr(code, "_tool_inputs", [])
        else:
            inputs_sig = inspect.signature(code).parameters
            inputs = []
            for input_name, param in inputs_sig.items():
                if param.annotation != inspect.Parameter.empty:
                    input_type = param.annotation.__name__
                    if input_type in ["int", "float"]:
                        input_type = DataType.NUMBER
                    elif input_type == "bool":
                        input_type = DataType.BOOLEAN
                    elif input_type == "str":
                        input_type = DataType.TEXT
                    inputs.append(
                        UtilityModelInput(
                            name=input_name, type=input_type, description=f"The '{input_name}' input is a {input_type}"
                        )
                    )
    elif isinstance(code, Callable):
        # Handle case of non-decorated callable
        str_code = inspect.getsource(code)
        description = code.__doc__.strip() if code.__doc__ else ""
        name = code.__name__
        # Try to infer parameters
        params_match = re.search(r"def\s+\w+\s*\((.*?)\)\s*(?:->.*?)?:", str_code)
        parameters = params_match.group(1).split(",") if params_match else []

        for input in parameters:
            if not input:
                continue
            assert (
                len(input.split(":")) > 1
            ), "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"
            input_name, input_type = input.split(":")
            input_name = input_name.strip()
            input_type = input_type.split("=")[0].strip()

            if input_type in ["int", "float"]:
                input_type = "number"
                inputs.append(
                    UtilityModelInput(name=input_name, type=DataType.NUMBER, description=f"The {input_name} input is a number")
                )
            elif input_type == "bool":
                input_type = "boolean"
                inputs.append(
                    UtilityModelInput(
                        name=input_name, type=DataType.BOOLEAN, description=f"The {input_name} input is a boolean"
                    )
                )
            elif input_type == "str":
                input_type = "text"
                inputs.append(
                    UtilityModelInput(name=input_name, type=DataType.TEXT, description=f"The {input_name} input is a text")
                )
            else:
                raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")
    elif isinstance(code, str):
        # if code is string do the parsing and parameter extraction as before
        if os.path.exists(code):
            with open(code, "r") as f:
                str_code = f.read()
        elif validators.url(code):
            str_code = requests.get(code).text
        else:
            str_code = code

        # New regex with capture groups
        # regex = r"@utility_tool\s*\((.*?)\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*->\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:"
        regex = r"@utility_tool\s*\((.*?)\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)"
        matches = re.findall(regex, str_code, re.DOTALL)

        if not matches:
            return parse_code(code)

        tool_match = matches[0]  # we expect only 1 match
        decorator_params = tool_match[0]
        parameters_str = tool_match[2]

        # Extract name and description
        name_match = re.search(r"name\s*=\s*[\"'](.*?)[\"']", decorator_params)
        name = name_match.group(1) if name_match else ""

        description_match = re.search(r"description\s*=\s*[\"'](.*?)[\"']", decorator_params)
        description = description_match.group(1) if description_match else ""
        # Extract parameters
        parameters = [param.strip() for param in parameters_str.split(",")] if parameters_str else []

        # Process parameters if 'inputs' are not explicitly defined in decorator.
        # Process parameters for inputs
        if "inputs" not in decorator_params:  # <-- Check here
            parameters = [param.strip() for param in parameters_str.split(",")] if parameters_str else []
            for input_str in parameters:
                if not input_str:
                    continue
                assert (
                    len(input_str.split(":")) > 1
                ), "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"
                input_name, input_type = input_str.split(":")
                input_name = input_name.strip()
                input_type = input_type.split("=")[0].strip()

                if input_type in ["int", "float"]:
                    inputs.append(
                        UtilityModelInput(
                            name=input_name, type=DataType.NUMBER, description=f"The {input_name} input is a number"
                        )
                    )
                elif input_type == "bool":
                    inputs.append(
                        UtilityModelInput(
                            name=input_name, type=DataType.BOOLEAN, description=f"The {input_name} input is a boolean"
                        )
                    )
                elif input_type == "str":
                    inputs.append(
                        UtilityModelInput(name=input_name, type=DataType.TEXT, description=f"The {input_name} input is a text")
                    )
                else:
                    raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")
        else:
            # try to parse from the decorator inputs
            input_matches = re.finditer(
                r"UtilityModelInput\s*\(\s*name\s*=\s*[\"'](.*?)[\"']\s*,\s*type\s*=\s*DataType\.([A-Z]+)\s*,\s*description\s*=\s*[\"'](.*?)[\"']\s*\)",
                decorator_params,
            )
            for match in input_matches:
                input_name = match.group(1)
                input_type = match.group(2)
                input_description = match.group(3)
                input_type = DataType(input_type.lower())
                try:
                    inputs.append(UtilityModelInput(name=input_name, type=input_type, description=input_description))
                except ValueError:
                    raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")

    # ! rempves the decorator from the code for the backend to be able to run the code and rename the function as main
    str_code = re.sub(
        r"(@utility_tool\(.*?\)\s*)?def\s+\w+", "def main", str_code, flags=re.DOTALL
    )  # TODO: this should be corrected on the backend side and updated in later versions
    if "utility_tool" in str_code:
        raise Exception("Utility Model Error: Code must be decorated with @utility_tool and have a function defined.")
    if "def main" not in str_code:
        raise Exception("Utility Model Error: Code must have a function defined.")
    local_path = str(uuid4())
    with open(local_path, "w") as f:
        f.write(str_code)
    code = FileFactory.upload(local_path=local_path, is_temp=True)
    os.remove(local_path)

    return code, inputs, description, name


def is_supported_image_type(value: str) -> bool:
    return any(value.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"])
