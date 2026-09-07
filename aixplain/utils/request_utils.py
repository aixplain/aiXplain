from requests.adapters import HTTPAdapter, Retry
import requests
from typing import Text

# One session for the process instead of one per call. A 5-minute v1 job polls
# ~44 times, and a per-call Session meant ~44 TLS handshakes where keep-alive
# needs one (BUG-942 item 3). ``requests.Session`` is safe for this use: it is
# configured here at import and never mutated afterwards, and it carries no
# credentials (every caller passes its own headers).
#
# Sized explicitly, matching ``aixplain.v2.client``. Now that the session is
# shared, urllib3's 10/10 default would bite at concurrency: above 10 in-flight
# requests the adapter opens a connection, uses it once and *discards* it
# instead of pooling it, logging "Connection pool is full" each time -- which
# would cancel out the reuse this module now exists to provide. Duplicated here
# rather than imported so importing v1 does not drag in v2.
_POOL_CONNECTIONS = 32
_POOL_MAXSIZE = 64

_RETRIES = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
_SESSION = requests.Session()
_SESSION.mount(
    "https://",
    HTTPAdapter(max_retries=_RETRIES, pool_connections=_POOL_CONNECTIONS, pool_maxsize=_POOL_MAXSIZE),
)


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
