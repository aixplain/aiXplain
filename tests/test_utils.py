from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin
import logging
from aixplain.utils import config


def delete_asset(model_id, api_key):
    delete_url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
    logging.debug(f"URL: {delete_url}")
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    _ = _request_with_retry("delete", delete_url, headers=headers)


def delete_service_account(api_key):
    delete_url = urljoin(config.BACKEND_URL, "sdk/ecr/logout")
    logging.debug(f"URL: {delete_url}")
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    _ = _request_with_retry("post", delete_url, headers=headers)
