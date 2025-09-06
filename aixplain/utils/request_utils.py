from requests.adapters import HTTPAdapter, Retry
import requests
from typing import Text


def _request_with_retry(method: Text, url: Text, **params) -> requests.Response:
    """Wrapper around requests with Session to retry in case it fails

    Args:
        method (Text): HTTP method, such as 'GET' or 'HEAD'.
        url (Text): The URL of the resource to fetch.
        **params: Params to pass to request function.

    Returns:
        requests.Response: Response object of the request.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    response = session.request(method=method.upper(), url=url, **params)
    return response
