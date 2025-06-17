from typing import Any

import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin


DEFAULT_RETRY_TOTAL = 5
DEFAULT_RETRY_BACKOFF_FACTOR = 0.1
DEFAULT_RETRY_STATUS_FORCELIST = [500, 502, 503, 504]


def create_retry_session(total=None, backoff_factor=None, status_forcelist=None, **kwargs):
    """
    Creates a requests.Session with a specified retry strategy.

    Args:
        total (int, optional): Total number of retries allowed. Defaults to 5.
        backoff_factor (float, optional): Backoff factor to apply between retry attempts. Defaults to 0.1.
        status_forcelist (list, optional): List of HTTP status codes to force a retry on. Defaults to [500, 502, 503, 504].
        kwargs (dict, optional): Additional keyword arguments for internal Retry object.

    Returns:
        requests.Session: A requests.Session object with the specified retry strategy.
    """
    total = total or DEFAULT_RETRY_TOTAL
    backoff_factor = backoff_factor or DEFAULT_RETRY_BACKOFF_FACTOR
    status_forcelist = status_forcelist or DEFAULT_RETRY_STATUS_FORCELIST
    retry_strategy = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset({"GET", "POST"}),
        **kwargs,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class AixplainClient:
    def __init__(
        self,
        base_url: str,
        aixplain_api_key: str = None,
        team_api_key: str = None,
        retry_total=DEFAULT_RETRY_TOTAL,
        retry_backoff_factor=DEFAULT_RETRY_BACKOFF_FACTOR,
        retry_status_forcelist=DEFAULT_RETRY_STATUS_FORCELIST,
    ):
        """
        Initializes AixplainClient with authentication and retry configuration.

        Args:
            base_url (str): The base URL for the API.
            aixplain_api_key (str, optional): The individual API key.
            team_api_key (str, optional): The team API key.
            retry_total (int, optional): Total number of retries allowed. Defaults to None, uses DEFAULT_RETRY_TOTAL.
            retry_backoff_factor (float, optional): Backoff factor to apply between retry attempts. Defaults to None, uses DEFAULT_RETRY_BACKOFF_FACTOR.
            retry_status_forcelist (list, optional): List of HTTP status codes to force a retry on. Defaults to None, uses DEFAULT_RETRY_STATUS_FORCELIST.
        """
        self.base_url = base_url
        self.team_api_key = team_api_key
        self.aixplain_api_key = aixplain_api_key

        if not (self.aixplain_api_key or self.team_api_key):
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        if self.aixplain_api_key and self.team_api_key:
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        headers = {"Content-Type": "application/json"}
        if self.aixplain_api_key:
            headers["x-aixplain-key"] = self.aixplain_api_key
        else:
            headers["x-api-key"] = self.team_api_key

        self.session = create_retry_session(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=retry_status_forcelist,
        )
        self.session.headers.update(headers)

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """
        Sends an HTTP request.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The response from the request
        """
        url = urljoin(self.base_url, path)
        response = self.session.request(method=method, url=url, **kwargs)
        response.raise_for_status()
        return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        """
        Sends an HTTP GET request.

        Args:
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The response from the request
        """
        return self.request("GET", path, **kwargs)

    def get_obj(self, path: str, **kwargs: Any) -> dict:
        """
        Sends an HTTP GET request and returns the object.
        """
        response = self.get(path, **kwargs)
        return response.json()
