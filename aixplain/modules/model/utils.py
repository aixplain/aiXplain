__author__ = "thiagocastroferreira"

import json
import logging
from aixplain.utils.file_utils import _request_with_retry
from typing import Dict, Text, Union


def build_payload(data: Union[Text, Dict], parameters: Dict = {}):
    from aixplain.factories import FileFactory

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
        if r.status_code == 401:
            error = f"Unauthorized API key: Please verify the spelling of the API key and its current validity. Details: {resp}"
        elif 460 <= r.status_code < 470:
            error = f"Subscription-related error: Please ensure that your subscription is active and has not expired. Details: {resp}"
        elif 470 <= r.status_code < 480:
            error = f"Billing-related error: Please ensure you have enough credits to run this model. Details: {resp}"
        elif 480 <= r.status_code < 490:
            error = f"Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access. Details: {resp}"
        elif 490 <= r.status_code < 500:
            error = f"Validation-related error: Please ensure all required fields are provided and correctly formatted. Details: {resp}"
        else:
            status_code = str(r.status_code)
            error = f"Status {status_code} - Unspecified error: {resp}"
        response = {"status": "FAILED", "error_message": error, "completed": True}
        logging.error(f"Error in request: {r.status_code}: {error}")
    return response
