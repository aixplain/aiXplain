"""Client module for making HTTP requests to the aiXplain API."""

from typing import Any, Iterable, Optional, Tuple, Union, List, FrozenSet
import logging
import os
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin, urlparse

from .exceptions import APIError, UntrustedURLError

logger = logging.getLogger(__name__)


DEFAULT_RETRY_TOTAL = 5
DEFAULT_RETRY_BACKOFF_FACTOR = 0.1
DEFAULT_RETRY_STATUS_FORCELIST = [500, 502, 503, 504]

# Methods urllib3 may retry once a request has actually been put on the wire.
# Dropping POST is what closes BUG-1090: with POST listed, a single ``/execute``
# could become up to ``total + 1`` billable submissions as soon as a default read
# timeout existed, because a model slower than DEFAULT_TIMEOUT_READ raises
# ReadTimeout inside urllib3, which then silently re-POSTs below the SDK.
#
# Scope of the guarantee, since urllib3 consults ``allowed_methods`` for only
# some retry classes: ``status_forcelist`` responses and *read* errors
# (ReadTimeoutError, ProtocolError) are now method-gated, so POST gets neither.
# *Connect* errors (ConnectTimeoutError, NewConnectionError) are still retried
# for every method — urllib3 skips the method check there by design, and safely
# so: the connection was never established, so no request bytes reached the
# backend and no run was submitted.
#
# Retrying a submission that may have landed belongs to the SDK layer, which
# knows what one costs — see ``RunnableResourceMixin._submit_with_retries`` and
# the ``run_retries`` param.
RETRY_ALLOWED_METHODS = frozenset({"GET"})

# Default (connect, read) timeout applied to every request that doesn't pass
# its own ``timeout=``.  Without one, ``requests`` waits forever: a backend
# that accepts the connection and then goes quiet blocks the calling thread
# indefinitely (observed in production: a LIST_INPUTS POST to
# /api/v2/execute hung for 938s after a RemoteDisconnected).  The read
# timeout is generous because this session also carries synchronous model
# executions; it bounds a hang, it does not schedule work.  For streaming
# requests the read timeout applies per chunk, not to the whole stream.
DEFAULT_TIMEOUT_CONNECT = 10.0
DEFAULT_TIMEOUT_READ = 300.0
TimeoutType = Union[float, Tuple[float, float]]


def _timeout_from_env(name: str, default: float) -> float:
    """Read a positive float timeout from ``name``, falling back to ``default``.

    A malformed value must not silently remove the bound the variable exists
    to configure, so it logs and keeps the default.
    """
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning(f"Ignoring non-numeric {name}={raw!r}; using {default}s")
        return default
    if value <= 0:
        logger.warning(f"Ignoring non-positive {name}={raw!r}; using {default}s")
        return default
    return value


def default_timeout() -> Tuple[float, float]:
    """Resolve the default (connect, read) timeout, honouring env overrides.

    ``AIXPLAIN_HTTP_CONNECT_TIMEOUT`` / ``AIXPLAIN_HTTP_READ_TIMEOUT`` (seconds)
    override the built-in defaults per environment without a code change.
    """
    return (
        _timeout_from_env("AIXPLAIN_HTTP_CONNECT_TIMEOUT", DEFAULT_TIMEOUT_CONNECT),
        _timeout_from_env("AIXPLAIN_HTTP_READ_TIMEOUT", DEFAULT_TIMEOUT_READ),
    )


# Hosts the SDK is willing to send ``TEAM_API_KEY`` to, on top of whatever the
# running configuration points at.  Poll URLs are chosen by a response body, so
# without an allowlist any JSON field can name the host that receives the
# credential (BUG-937).
DEFAULT_TRUSTED_URLS = (
    "https://platform-api.aixplain.com",
    "https://models.aixplain.com",
)

# Every header that carries an aiXplain credential.  These are custom headers,
# so ``requests`` does not strip them across a redirect the way it does
# ``Authorization`` -- ``_AixplainSession`` has to do it.
AUTH_HEADER_NAMES = ("x-api-key", "x-aixplain-key")

# Comma-separated ``host[:port]`` or full URLs, for on-prem/regional deployments
# whose poll hosts are not derivable from the configured endpoints.
TRUSTED_HOSTS_ENV_VAR = "AIXPLAIN_TRUSTED_HOSTS"

Origin = Tuple[str, str, int]


def normalize_origin(url: str) -> Optional[Origin]:
    """Return the normalized ``(scheme, host, port)`` triple for *url*, or None.

    Uses ``hostname``/``port`` rather than ``netloc`` so that userinfo
    (``https://platform-api.aixplain.com@evil.example.com/x``) cannot disguise the
    real target and so ``:443`` compares equal to the implicit default. Returns
    ``None`` for anything that is not a parseable http(s) URL with a host, and for
    URLs carrying userinfo, which a legitimate aiXplain endpoint never does.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    try:
        if parsed.username or parsed.password:
            return None
        host, port = parsed.hostname, parsed.port
    except ValueError:  # malformed port, e.g. "https://host:notaport/x"
        return None
    if not host:
        return None
    # ``port is None`` means "not specified", which is the scheme default. An
    # explicit ``:0`` is a distinct (unconnectable) origin, so it must not be
    # folded into the default and inherit its trust.
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return (parsed.scheme, host.lower(), port)


def _origins_from_env() -> List[Origin]:
    """Parse ``AIXPLAIN_TRUSTED_HOSTS`` into origins, ignoring unparseable entries."""
    origins = []
    for entry in os.getenv(TRUSTED_HOSTS_ENV_VAR, "").split(","):
        entry = entry.strip()
        if not entry:
            continue
        origin = normalize_origin(entry if "://" in entry else f"https://{entry}")
        if origin is None:
            logger.warning(f"Ignoring unparseable {TRUSTED_HOSTS_ENV_VAR} entry {entry!r}")
            continue
        origins.append(origin)
    return origins


def build_trusted_origins(urls: Iterable[str]) -> FrozenSet[Origin]:
    """Build the trusted origin set from configured endpoints, defaults and env.

    Scheme is part of the origin, so plain ``http`` to an aiXplain host is not
    trusted; ``http`` is only ever trusted when an operator explicitly configured
    an ``http`` endpoint (e.g. ``BACKEND_URL=http://localhost:8000``), which is a
    deliberate opt-in on a host they control rather than something a response
    body can induce.
    """
    origins = set()
    for url in [*urls, *DEFAULT_TRUSTED_URLS]:
        if not url:
            continue
        origin = normalize_origin(url if "://" in url else f"https://{url}")
        if origin is not None:
            origins.add(origin)
    origins.update(_origins_from_env())
    return frozenset(origins)


class _AixplainSession(requests.Session):
    """Session that drops aiXplain credentials when a redirect leaves the trusted set.

    ``requests`` strips only ``Authorization`` on a host change; a custom
    ``x-api-key`` header is copied verbatim to the redirect target, so a single
    302 from a trusted host would hand the team key to an attacker-chosen one.
    Redirects stay enabled -- a legitimate ``302`` to a presigned S3 result URL
    still resolves, it just arrives unauthenticated (presigned URLs carry their
    own signature).
    """

    # Class-level default so a session restored without ``__init__`` (deepcopy,
    # pickle) fails closed -- trusting nothing means credentials are stripped on
    # every redirect, rather than ``rebuild_auth`` raising AttributeError.
    trusted_origins: FrozenSet[Origin] = frozenset()

    # ``requests.Session`` pickles only the names in ``__attrs__``; without this
    # a ``deepcopy`` of a client's session would silently drop the allowlist.
    __attrs__ = requests.Session.__attrs__ + ["trusted_origins"]

    def __init__(self, trusted_origins: FrozenSet[Origin] = frozenset()) -> None:
        """Initialize the session with the origins allowed to receive credentials."""
        super().__init__()
        self.trusted_origins = trusted_origins

    def rebuild_auth(self, prepared_request: requests.PreparedRequest, response: requests.Response) -> None:
        """Strip aiXplain credentials when the redirect target is not trusted."""
        super().rebuild_auth(prepared_request, response)
        if normalize_origin(prepared_request.url or "") not in self.trusted_origins:
            for name in AUTH_HEADER_NAMES:
                prepared_request.headers.pop(name, None)


def create_retry_session(
    total: Optional[int] = None,
    backoff_factor: Optional[float] = None,
    status_forcelist: Optional[List[int]] = None,
    trusted_origins: FrozenSet[Origin] = frozenset(),
    **kwargs: Any,
) -> requests.Session:
    """Creates a requests.Session with a specified retry strategy.

    Only ``GET`` is retried (see :data:`RETRY_ALLOWED_METHODS`): POST is not
    idempotent here, so a transport-level retry of ``/execute`` submits — and
    bills — the run again. Callers that want a run re-submitted on a transient
    failure use the SDK-level ``run_retries`` parameter instead.

    Args:
        total (int, optional): Total number of retries allowed. Defaults to 5.
        backoff_factor (float, optional): Backoff factor to apply between retry attempts. Defaults to 0.1.
        status_forcelist (list, optional): List of HTTP status codes to force a retry on. Defaults to [500, 502, 503, 504].
        trusted_origins (frozenset, optional): ``(scheme, host, port)`` triples allowed
            to receive aiXplain credentials across a redirect. Defaults to none, i.e.
            any redirect drops them.
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
        allowed_methods=RETRY_ALLOWED_METHODS,
        **kwargs,
    )
    session = _AixplainSession(trusted_origins=trusted_origins)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class AixplainClient:
    """HTTP client for aiXplain API with retry support."""

    def __init__(
        self,
        base_url: str,
        aixplain_api_key: Optional[str] = None,
        team_api_key: Optional[str] = None,
        retry_total: int = DEFAULT_RETRY_TOTAL,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
        retry_status_forcelist: List[int] = DEFAULT_RETRY_STATUS_FORCELIST,
        timeout: Optional[TimeoutType] = None,
        trusted_urls: Optional[List[str]] = None,
    ) -> None:
        """Initialize AixplainClient with authentication and retry configuration.

        Args:
            base_url (str): The base URL for the API.
            aixplain_api_key (str, optional): The individual API key.
            team_api_key (str, optional): The team API key.
            retry_total (int): Total number of retries allowed. Defaults to 5.
            retry_backoff_factor (float): Backoff factor between retry attempts. Defaults to 0.1.
            retry_status_forcelist (list): HTTP status codes that trigger a retry. Defaults to [500, 502, 503, 504].
            timeout (float or (float, float) tuple, optional): Default timeout for every
                request that doesn't pass its own ``timeout=``. Defaults to
                (AIXPLAIN_HTTP_CONNECT_TIMEOUT or 10, AIXPLAIN_HTTP_READ_TIMEOUT or 300)
                seconds. Individual calls can still override it per request.
            trusted_urls (list, optional): Extra endpoints allowed to receive the
                API key, on top of ``base_url``, the aiXplain defaults and
                ``AIXPLAIN_TRUSTED_HOSTS``. Any other URL raises
                :class:`UntrustedURLError` before a socket is opened.
        """
        self.base_url = base_url
        self.timeout: TimeoutType = timeout if timeout is not None else default_timeout()
        self.team_api_key = team_api_key
        self.aixplain_api_key = aixplain_api_key

        if not (self.aixplain_api_key or self.team_api_key):
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        if self.aixplain_api_key and self.team_api_key:
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        self.trusted_origins = build_trusted_origins([base_url, *(trusted_urls or [])])

        self.session = create_retry_session(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=retry_status_forcelist,
            trusted_origins=self.trusted_origins,
        )
        # The credential deliberately does NOT live on the session: session
        # headers ride along with any absolute URL handed to ``request_raw``,
        # which is exactly how the key used to reach body-supplied hosts.
        self.session.headers.update({"Content-Type": "application/json"})

    def resolve_url(self, path: str) -> str:
        """Resolve *path* against ``base_url`` unless it is already absolute."""
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(self.base_url, path)

    def is_trusted_url(self, url: str) -> bool:
        """Return True when *url* is an origin allowed to receive the API key."""
        return normalize_origin(url) in self.trusted_origins

    def ensure_trusted_url(self, path: str) -> str:
        """Resolve *path* and return it, raising unless it is a trusted origin.

        Validation happens on the *resolved* URL: a relative input such as
        ``//evil.example.com/x`` becomes an absolute foreign URL only after
        ``urljoin``, so checking the caller's string would be bypassable.

        Raises:
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.resolve_url(path)
        if not self.is_trusted_url(url):
            allowed = sorted(f"{scheme}://{host}:{port}" for scheme, host, port in self.trusted_origins)
            raise UntrustedURLError(
                f"Refusing to send credentials to untrusted URL {url!r}. "
                f"Allowed origins: {allowed}. "
                f"Set {TRUSTED_HOSTS_ENV_VAR} to extend this list."
            )
        return url

    def _auth_headers(self) -> dict:
        """Return the credential headers for a single request."""
        if self.team_api_key:
            return {"x-api-key": self.team_api_key}
        return {"x-aixplain-key": self.aixplain_api_key}

    def request_raw(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Sends an HTTP request.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path or full URL
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The response from the request

        Raises:
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.ensure_trusted_url(path)
        kwargs["headers"] = {**self._auth_headers(), **(kwargs.pop("headers", None) or {})}
        kwargs.setdefault("timeout", self.timeout)
        # ``headers`` now carries the API key, so it stays out of the log line.
        logger.debug(f"Requesting {method} {url} with kwargs: {kwargs}")
        response = self.session.request(method=method, url=url, **kwargs)
        logger.debug(f"Response: {response.text}")
        if not response.ok:
            error_obj = None
            try:
                error_obj = response.json()
            except Exception as e:
                logger.error(f"Error parsing error response: {e}")

            if isinstance(error_obj, list):
                raise APIError(error_obj, status_code=response.status_code, response_data={"errors": error_obj})
            if error_obj:
                # supplierError carries the actionable detail (e.g. "Name already
                # exists"); the "error" field is often just a code like
                # "err.supplier_error".
                message = (
                    error_obj.get("supplierError")
                    or error_obj.get("supplier_error")
                    or error_obj.get("message")
                    or error_obj.get("error")
                    or response.text
                )
                raise APIError(
                    message,
                    status_code=error_obj.get("statusCode", response.status_code),
                    response_data=error_obj,
                    error=error_obj.get("error", response.text),
                )
            else:
                raise APIError(response.text, status_code=response.status_code, error=response.text)

        return response

    def request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP request.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The response from the request
        """
        response = self.request_raw(method, path, **kwargs)
        return response.json()

    def get(self, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP GET request.

        Args:
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The JSON response from the request
        """
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP POST request.

        Args:
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The JSON response from the request
        """
        return self.request("POST", path, **kwargs)

    def request_stream(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Sends a streaming HTTP request.

        This method is similar to request_raw but enables streaming mode,
        which is necessary for Server-Sent Events (SSE) responses.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path or full URL
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The streaming response (not consumed)

        Raises:
            APIError: If the request fails
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.ensure_trusted_url(path)

        logger.debug(f"Requesting streaming {method} {url}")

        kwargs["headers"] = {**self._auth_headers(), **(kwargs.pop("headers", None) or {})}
        # Enable streaming mode
        kwargs["stream"] = True
        # In streaming mode the read timeout applies per chunk read, not to the
        # stream's total lifetime, so long-lived SSE streams stay safe as long
        # as the server keeps sending (events or keep-alives).
        kwargs.setdefault("timeout", self.timeout)

        response = self.session.request(method=method, url=url, **kwargs)

        # For streaming, we check status but don't consume the response body
        if not response.ok:
            error_obj = None
            try:
                # Try to get error details from response
                error_obj = response.json()
            except Exception as e:
                logger.error(f"Error parsing error response: {e}")

            if error_obj:
                raise APIError(
                    error_obj.get("message", error_obj.get("error", "Stream request failed")),
                    status_code=error_obj.get("statusCode", response.status_code),
                    response_data=error_obj,
                    error=error_obj.get("error", ""),
                )
            else:
                raise APIError(
                    f"Stream request failed with status {response.status_code}",
                    status_code=response.status_code,
                    error="",
                )

        return response
