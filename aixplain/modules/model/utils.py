__author__ = "thiagocastroferreira"

import json
import logging
from aixplain.utils.file_utils import _request_with_retry
from typing import Callable, Dict, List, Text, Tuple, Union, Optional


def build_payload(data: Union[Text, Dict], parameters: Optional[Dict] = None):
    from aixplain.factories import FileFactory

    if parameters is None:
        parameters = {}

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
            payload = {"data": data}
    payload.update(parameters)
    payload = json.dumps(payload)
    return payload


def call_run_endpoint(url: Text, api_key: Text, payload: Dict) -> Dict:
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    resp = "unspecified error"
    try:
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
        resp = resp["error"] if isinstance(resp, dict) and "error" in resp else resp
        if r.status_code == 401:
            error = f"Unauthorized API key: Please verify the spelling of the API key and its current validity. Details: {resp}"
        elif 460 <= r.status_code < 470:
            error = f"Subscription-related error: Please ensure that your subscription is active and has not expired. Details: {resp}"
        elif 470 <= r.status_code < 480:
            error = f"Billing-related error: Please ensure you have enough credits to run this model. Details: {resp}"
        elif 480 <= r.status_code < 490:
            error = f"Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access. Details: {resp}"
        elif 490 <= r.status_code < 500:
            error = f"{resp}"
        else:
            status_code = str(r.status_code)
            error = f"Status {status_code} - Unspecified error: {resp}"
        response = {"status": "FAILED", "error_message": error, "completed": True}
        logging.error(f"Error in request: {r.status_code}: {error}")
    return response


def parse_code(code: Union[Text, Callable]) -> Tuple[Text, List, Text]:
    import inspect
    import os
    import re
    import requests
    import validators
    from aixplain.enums import DataType
    from aixplain.modules.model.utility_model import UtilityModelInput
    from aixplain.factories.file_factory import FileFactory
    from uuid import uuid4

    inputs, description = [], ""

    if isinstance(code, Callable):
        str_code = inspect.getsource(code)
        description = code.__doc__.strip() if code.__doc__ else ""
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

    f = re.findall(r"main\((.*?(?:\s*=\s*[^,)]+)?(?:\s*,\s*.*?(?:\s*=\s*[^,)]+)?)*)\)", str_code)
    parameters = f[0].split(",") if len(f) > 0 else []

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
    return code, inputs, description
