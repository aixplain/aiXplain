from requests.adapters import HTTPAdapter, Retry
import requests
from typing import Text

# One session for the process instead of one per call. A 5-minute v1 job polls
# ~44 times, and a per-call Session meant ~44 TLS handshakes where keep-alive
# needs one (BUG-942 item 3). ``requests.Session`` is safe for this use: it is
# configured here at import and never mutated afterwards, and it carries no
# credentials (every caller passes its own headers).
_RETRIES = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
_SESSION = requests.Session()
_SESSION.mount("https://", HTTPAdapter(max_retries=_RETRIES))


def _request_with_retry(method: Text, url: Text, **params) -> requests.Response:
    """Wrapper around requests with Session to retry in case it fails

    Args:
        method (Text): HTTP method, such as 'GET' or 'HEAD'.
        url (Text): The URL of the resource to fetch.
        **params: Params to pass to request function.

    Returns:
        requests.Response: Response object of the request.
    """
    return _SESSION.request(method=method.upper(), url=url, **params)
