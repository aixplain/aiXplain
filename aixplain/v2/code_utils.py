"""Code parsing utilities for v2 utility models.

Adapted from aixplain.modules.model.utils to avoid v1 import chain
that triggers env var validation.
"""

import ast
import inspect
import logging
import os
import re
from dataclasses import dataclass
from typing import Callable, List, Text, Tuple, Union, Optional
from uuid import uuid4

import requests
import validators

from .enums import DataType
from .upload_utils import FileUploader

logger = logging.getLogger(__name__)


@dataclass
class UtilityModelInput:
    """Input parameter for a utility model.

    Attributes:
        name: The name of the input parameter.
        description: A description of what this input parameter represents.
        type: The data type of the input parameter.
    """

    name: Text
    description: Text
    type: DataType = DataType.TEXT

    def validate(self):
        """Validate that the input type is one of TEXT, BOOLEAN, or NUMBER."""
        if self.type not in [DataType.TEXT, DataType.BOOLEAN, DataType.NUMBER]:
            raise ValueError("Utility Model Input type must be TEXT, BOOLEAN or NUMBER")

    def to_dict(self):
        """Convert to dictionary representation."""
        return {"name": self.name, "description": self.description, "type": self.type.value}


def _extract_function_parameters(func: Callable) -> List[Tuple[str, str]]:
    """Extract function parameters using AST parsing for robust handling of multiline functions."""
    try:
        sig = inspect.signature(func)
        parameters = []

        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                if hasattr(param.annotation, "__name__"):
                    param_type = param.annotation.__name__
                else:
                    param_type = str(param.annotation)
            else:
                raise ValueError(f"Parameter '{param_name}' missing type annotation")

            parameters.append((param_name, param_type))

        return parameters

    except Exception as e:
        try:
            source = inspect.getsource(func)
            tree = ast.parse(source)

            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
                    func_def = node
                    break

            if not func_def:
                raise ValueError(f"Could not find function definition for {func.__name__}")

            parameters = []
            for arg in func_def.args.args:
                param_name = arg.arg

                if arg.annotation:
                    if isinstance(arg.annotation, ast.Name):
                        param_type = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Constant):
                        param_type = str(arg.annotation.value)
                    else:
                        param_type = ast.unparse(arg.annotation)
                else:
                    raise ValueError(f"Parameter '{param_name}' missing type annotation")

                parameters.append((param_name, param_type))

            return parameters

        except Exception as ast_error:
            raise ValueError(f"Failed to extract parameters: {e}. AST fallback also failed: {ast_error}")


def _upload_code(str_code: str, backend_url: str, api_key: str) -> str:
    """Write code to a temp file and upload via FileUploader."""
    local_path = str(uuid4())
    with open(local_path, "w") as f:
        f.write(str_code)
    try:
        uploader = FileUploader(backend_url=backend_url, api_key=api_key)
        return uploader.upload(local_path, is_temp=True)
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)


def _type_to_input(input_name: str, input_type: str) -> UtilityModelInput:
    """Map a Python type string to a UtilityModelInput."""
    if input_type in ["int", "float"]:
        return UtilityModelInput(
            name=input_name,
            type=DataType.NUMBER,
            description=f"The {input_name} input is a number",
        )
    elif input_type == "bool":
        return UtilityModelInput(
            name=input_name,
            type=DataType.BOOLEAN,
            description=f"The {input_name} input is a boolean",
        )
    elif input_type == "str":
        return UtilityModelInput(
            name=input_name,
            type=DataType.TEXT,
            description=f"The {input_name} input is a text",
        )
    else:
        raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")


def parse_code(
    code: Union[Text, Callable],
    api_key: Optional[Text] = None,
    backend_url: Optional[Text] = None,
) -> Tuple[Text, List, Text, Text]:
    """Parse and process code for utility model creation.

    Args:
        code: The code to parse (callable, file path, URL, or raw code string).
        api_key: API key for authentication when uploading code.
        backend_url: Backend URL for file upload.

    Returns:
        Tuple of (code_url, inputs, description, name).
    """
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

    if "def main(" not in str_code:
        raise Exception("Utility Model Error: Code must have a main function")

    name = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\(", str_code).group(1)
    if not description:
        regex = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\).*?(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|\#\s*(.*?)(?:\n|$)|$)'
        match = re.search(regex, str_code, re.DOTALL)
        if match:
            (
                function_name,
                params,
                triple_double_quote_doc,
                triple_single_quote_doc,
                single_line_comment,
            ) = match.groups()
            description = (triple_double_quote_doc or triple_single_quote_doc or single_line_comment or "").strip()
        else:
            raise Exception(
                "Utility Model Error:If the function is not decorated with @utility_tool, the description must be provided in the docstring"
            )

    params_match = re.search(r"def\s+\w+\s*\((.*?)\)\s*(?:->.*?)?:", str_code)
    parameters = params_match.group(1).split(",") if params_match else []

    for input_str in parameters:
        assert len(input_str.split(":")) > 1, (
            "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"
        )
        input_name, input_type = input_str.split(":")
        input_name = input_name.strip()
        input_type = input_type.split("=")[0].strip()
        inputs.append(_type_to_input(input_name, input_type))

    code = _upload_code(str_code, backend_url=backend_url, api_key=api_key)
    return code, inputs, description, name


def parse_code_decorated(
    code: Union[Text, Callable],
    api_key: Optional[Text] = None,
    backend_url: Optional[Text] = None,
) -> Tuple[Text, List, Text, Text]:
    """Parse and process code that may be decorated with @utility_tool.

    Args:
        code: The code to parse (decorated/non-decorated callable, file path, URL, or raw string).
        api_key: API key for authentication when uploading code.
        backend_url: Backend URL for file upload.

    Returns:
        Tuple of (code_url, inputs, description, name).
    """
    inputs, description, name = [], "", ""
    str_code = ""

    if inspect.isclass(code) or (not isinstance(code, (str, Callable)) and hasattr(code, "__class__")):
        raise TypeError(
            f"Code must be either a string or a callable function, not a class or class instance. You tried to pass a class or class instance: {code}"
        )

    if isinstance(code, Callable) and hasattr(code, "_is_utility_tool"):
        str_code = inspect.getsource(code)
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
                            name=input_name,
                            type=input_type,
                            description=f"The '{input_name}' input is a {input_type}",
                        )
                    )
    elif isinstance(code, Callable):
        str_code = inspect.getsource(code)
        description = code.__doc__.strip() if code.__doc__ else ""
        name = code.__name__

        parameters = _extract_function_parameters(code)
        inputs = []

        for input_name, input_type in parameters:
            inputs.append(_type_to_input(input_name, input_type))
    elif isinstance(code, str):
        if os.path.exists(code):
            with open(code, "r") as f:
                str_code = f.read()
        elif validators.url(code):
            str_code = requests.get(code).text
        else:
            str_code = code

        regex = r"@utility_tool\s*\((.*?)\)\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)"
        matches = re.findall(regex, str_code, re.DOTALL)

        if not matches:
            return parse_code(code, api_key=api_key, backend_url=backend_url)

        tool_match = matches[0]
        decorator_params = tool_match[0]
        parameters_str = tool_match[2]

        name_match = re.search(r"name\s*=\s*[\"'](.*?)[\"']", decorator_params)
        name = name_match.group(1) if name_match else ""

        description_match = re.search(r"description\s*=\s*[\"'](.*?)[\"']", decorator_params)
        description = description_match.group(1) if description_match else ""

        if "inputs" not in decorator_params:
            parameters = [param.strip() for param in parameters_str.split(",")] if parameters_str else []
            for input_str in parameters:
                if not input_str:
                    continue
                assert len(input_str.split(":")) > 1, (
                    "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"
                )
                input_name, input_type = input_str.split(":")
                input_name = input_name.strip()
                input_type = input_type.split("=")[0].strip()
                inputs.append(_type_to_input(input_name, input_type))
        else:
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
                    inputs.append(
                        UtilityModelInput(
                            name=input_name,
                            type=input_type,
                            description=input_description,
                        )
                    )
                except ValueError:
                    raise Exception(f"Utility Model Error: Unsupported input type: {input_type}")

    # Remove decorator and rename function to main
    str_code = re.sub(r"(@utility_tool\(.*?\)\s*)?def\s+\w+", "def main", str_code, flags=re.DOTALL)
    if "utility_tool" in str_code:
        raise Exception("Utility Model Error: Code must be decorated with @utility_tool and have a function defined.")
    if "def main" not in str_code:
        raise Exception("Utility Model Error: Code must have a function defined.")

    code = _upload_code(str_code, backend_url=backend_url, api_key=api_key)

    return code, inputs, description, name
