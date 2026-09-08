import threading
from typing import Text

import requests
from requests.adapters import HTTPAdapter, Retry

# One session per *thread* instead of one per call. A 5-minute v1 job polls ~44
# times, and a per-call Session meant ~44 TLS handshakes where keep-alive needs
# one (BUG-942 item 3).
#
# Per-thread rather than per-process: ``requests`` documents ``Session`` as not
# thread-safe, and v1 reaches this module from ``ThreadPoolExecutor`` pools
# (``agent_factory/utils.py``, ``team_agent_factory/utils.py``). A single shared
# Session would also share ``session.cookies``, so a ``Set-Cookie`` from any host
# would persist process-wide and ride along on later requests to that host --
# state that did not exist when every call built its own Session. Pool workers
# are long-lived, so connection reuse is preserved.
_POOL_CONNECTIONS = 32
_POOL_MAXSIZE = 64

_RETRIES = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
_THREAD_STATE = threading.local()


def _new_session() -> requests.Session:
    """Build a retrying session for the calling thread."""
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(max_retries=_RETRIES, pool_connections=_POOL_CONNECTIONS, pool_maxsize=_POOL_MAXSIZE),
    )
    return session


def get_session() -> requests.Session:
    """Return this thread's session, creating it on first use.

    Returns:
        requests.Session: A session owned exclusively by the calling thread.
    """
    session = getattr(_THREAD_STATE, "session", None)
    if session is None:
        session = _new_session()
        _THREAD_STATE.session = session
    return session


def _request_with_retry(method: Text, url: Text, **params) -> requests.Response:
    """Wrapper around requests with Session to retry in case it fails

    Args:
        method (Text): HTTP method, such as 'GET' or 'HEAD'.
        url (Text): The URL of the resource to fetch.
        **params: Params to pass to request function.

    Returns:
        requests.Response: Response object of the request.

    Raises:
        UnsafeURLError: If a configured endpoint failed the config-URL policy at
            import time. Importing ``aixplain`` only warns about that (BUG-946);
            this is the choke point where it becomes a refusal, before a socket
            is opened (BUG-939).
    """
    from aixplain.utils.config import ensure_config_urls_safe

    ensure_config_urls_safe()
    return get_session().request(method=method.upper(), url=url, **params)
