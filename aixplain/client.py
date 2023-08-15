from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin


DEFAULT_RETRY_TOTAL = 5
DEFAULT_RETRY_BACKOFF_FACTOR = 0.1
DEFAULT_RETRY_STATUS_FORCELIST = [500, 502, 503, 504]


def create_retry_session(total=None,
                         backoff_factor=None,
                         status_forcelist=None,
                         **kwargs):
    """
    Creates a requests.Session with a specified retry strategy.

    :param total: Total number of retries allowed (default is 5).
    :param backoff_factor: Backoff factor to apply between retry attempts
                           (default is 0.1).
    :param status_forcelist: List of HTTP status codes to force a retry on
                             (default is [500, 502, 503, 504]).
    :param kwargs: Additional keyword arguments for internal Retry object
    :return: A requests.Session object with the specified retry strategy.
    """
    total = total or DEFAULT_RETRY_TOTAL
    backoff_factor = backoff_factor or DEFAULT_RETRY_BACKOFF_FACTOR
    status_forcelist = status_forcelist or DEFAULT_RETRY_STATUS_FORCELIST
    retry_strategy = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        **kwargs
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


class AixplainClient:

    def __init__(self, base_url: str,
                 aixplain_api_key: str = None,
                 team_api_key: str = None,
                 max_retries: int = 5,
                 retry_total=None,
                 retry_backoff_factor=None,
                 retry_status_forcelist=None):
        """
        Initialize AixplainClient with authentication and retry configuration.

        :param base_url: The base URL for the API.
        :param aixplain_api_key: The individual API key.
        :param team_api_key: The team API key.
        :param retry_total: Total number of retries allowed
                            (default is None, uses DEFAULT_RETRY_TOTAL).
        :param retry_backoff_factor: Backoff factor to apply between retry
                                     attempts (default is None,
                                     uses DEFAULT_RETRY_BACKOFF_FACTOR).
        :param retry_status_forcelist: List of HTTP status codes to force a
                                       retry on (default is None,
                                       uses DEFAULT_RETRY_STATUS_FORCELIST).
        """
        self.base_url = base_url
        self.team_api_key = team_api_key
        self.aixplain_api_key = aixplain_api_key

        if not (self.aixplain_api_key or self.team_api_key):
            raise ValueError(
                'Either `aixplain_api_key` or `team_api_key` should be set')

        headers = {'Content-Type': 'application/json'}
        if self.aixplain_api_key:
            headers['x-aixplain-key'] = self.aixplain_api_key
        else:
            headers['x-api-key'] = self.team_api_key

        self.session = create_retry_session(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=retry_status_forcelist)
        self.session.headers.update(headers)

    def request(self, method: str, path: str,
                **kwargs: Any) -> requests.Response:
        """
        Send an HTTP request.

        :param method: HTTP method (e.g. 'GET', 'POST')
        :param path: URL path
        :param kwargs: Additional keyword arguments for the request
        :return: requests.Response
        """
        url = urljoin(self.base_url, path)
        response = self.session.request(method=method, url=url, **kwargs)
        response.raise_for_status()
        return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        """
        Send an HTTP GET request.

        :param path: URL path
        :param kwargs: Additional keyword arguments for the request
        :return: requests.Response
        """
        return self.request('GET', path, **kwargs)
