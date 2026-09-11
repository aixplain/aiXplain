---
sidebar_label: client
title: aixplain.v2.client
---

Client module for making HTTP requests to the aiXplain API.

#### default\_timeout

```python
def default_timeout() -> Tuple[float, float]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L102)

Resolve the default (connect, read) timeout, honouring env overrides.

``AIXPLAIN_HTTP_CONNECT_TIMEOUT`` / ``AIXPLAIN_HTTP_READ_TIMEOUT`` (seconds)
override the built-in defaults per environment without a code change.

#### normalize\_origin

```python
def normalize_origin(url: str) -> Optional[Origin]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L322)

Return the normalized ``(scheme, host, port)`` triple for *url*, or None.

Uses ``hostname``/``port`` rather than ``netloc`` so that userinfo
(``https://platform-api.aixplain.com@evil.example.com/x``) cannot disguise the
real target and so ``:443`` compares equal to the implicit default. Returns
``None`` for anything that is not a parseable http(s) URL with a host, and for
URLs carrying userinfo, which a legitimate aiXplain endpoint never does.

#### build\_trusted\_origins

```python
def build_trusted_origins(urls: Iterable[str]) -> FrozenSet[Origin]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L368)

Build the trusted origin set from configured endpoints, defaults and env.

Scheme is part of the origin, so plain ``http`` to an aiXplain host is not
trusted; ``http`` is only ever trusted when an operator explicitly configured
an ``http`` endpoint (e.g. ``BACKEND_URL=http://localhost:8000``), which is a
deliberate opt-in on a host they control rather than something a response
body can induce.

### \_AixplainSession Objects

```python
class _AixplainSession(requests.Session)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L388)

Session that drops aiXplain credentials when a redirect leaves the trusted set.

``requests`` strips only ``Authorization`` on a host change; a custom
``x-api-key`` header is copied verbatim to the redirect target, so a single
302 from a trusted host would hand the team key to an attacker-chosen one.
Redirects stay enabled -- a legitimate ``302`` to a presigned S3 result URL
still resolves, it just arrives unauthenticated (presigned URLs carry their
own signature).

#### \_\_init\_\_

```python
def __init__(trusted_origins: FrozenSet[Origin] = frozenset()) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L408)

Initialize the session with the origins allowed to receive credentials.

#### rebuild\_auth

```python
def rebuild_auth(prepared_request: requests.PreparedRequest,
                 response: requests.Response) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L413)

Strip aiXplain credentials when the redirect target is not trusted.

#### create\_retry\_session

```python
def create_retry_session(total: Optional[int] = None,
                         backoff_factor: Optional[float] = None,
                         status_forcelist: Optional[List[int]] = None,
                         trusted_origins: FrozenSet[Origin] = frozenset(),
                         **kwargs: Any) -> requests.Session
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L467)

Creates a requests.Session with a specified retry strategy.

Only ``GET`` is retried (see :data:`RETRY_ALLOWED_METHODS`): POST is not
idempotent here, so a transport-level retry of ``/execute`` submits — and
bills — the run again. Callers that want a run re-submitted on a transient
failure use the SDK-level ``run_retries`` parameter instead.

**Arguments**:

- `total` _int, optional_ - Total number of retries allowed. Defaults to 5.
- `backoff_factor` _float, optional_ - Backoff factor to apply between retry attempts. Defaults to 0.1.
- `status_forcelist` _list, optional_ - List of HTTP status codes to force a retry on.
  Defaults to [429, 500, 502, 503, 504]. Retries are jittered and honour ``Retry-After``
  (bounded by DEFAULT_RETRY_AFTER_MAX).
- ``2 _frozenset, optional_ - ``(scheme, host, port)`` triples allowed
  to receive aiXplain credentials across a redirect. Defaults to none, i.e.
  any redirect drops them.
- ``5 _dict, optional_ - Additional keyword arguments for internal Retry object.
  

**Returns**:

- ``6 - A requests.Session object with the specified retry strategy.

### AixplainClient Objects

```python
class AixplainClient()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L523)

HTTP client for aiXplain API with retry support.

#### \_\_init\_\_

```python
def __init__(
        base_url: str,
        aixplain_api_key: Optional[str] = None,
        team_api_key: Optional[str] = None,
        retry_total: int = DEFAULT_RETRY_TOTAL,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
        retry_status_forcelist: List[int] = DEFAULT_RETRY_STATUS_FORCELIST,
        timeout: Optional[TimeoutType] = None,
        trusted_urls: Optional[List[str]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L526)

Initialize AixplainClient with authentication and retry configuration.

**Arguments**:

- `base_url` _str_ - The base URL for the API.
- `aixplain_api_key` _str, optional_ - The individual API key.
- `team_api_key` _str, optional_ - The team API key.
- `retry_total` _int_ - Total number of retries allowed. Defaults to 5.
- `retry_backoff_factor` _float_ - Backoff factor between retry attempts. Defaults to 0.1.
- `retry_status_forcelist` _list_ - HTTP status codes that trigger a retry.
  Defaults to [429, 500, 502, 503, 504].
  timeout (float or (float, float) tuple, optional): Default timeout for every
  request that doesn&#x27;t pass its own ``timeout=``. Defaults to
  (AIXPLAIN_HTTP_CONNECT_TIMEOUT or 10, AIXPLAIN_HTTP_READ_TIMEOUT or 300)
  seconds. Individual calls can still override it per request.
- `trusted_urls` _list, optional_ - Extra endpoints allowed to receive the
  API key, on top of ``base_url``, the aiXplain defaults and
  ``AIXPLAIN_TRUSTED_HOSTS``. Any other URL raises
  :class:`aixplain_api_key`3 before a socket is opened.

#### resolve\_url

```python
def resolve_url(path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L584)

Resolve *path* against ``base_url`` unless it is already absolute.

#### is\_trusted\_url

```python
def is_trusted_url(url: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L590)

Return True when *url* is an origin allowed to receive the API key.

#### ensure\_trusted\_url

```python
def ensure_trusted_url(path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L594)

Resolve *path* and return it, raising unless it is a trusted origin.

Validation happens on the *resolved* URL: a relative input such as
``//evil.example.com/x`` becomes an absolute foreign URL only after
``urljoin``, so checking the caller&#x27;s string would be bypassable.

**Raises**:

- `UntrustedURLError` - If the resolved URL is not a trusted aiXplain origin.

#### request\_raw

```python
def request_raw(method: str, path: str, **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L620)

Sends an HTTP request.

**Arguments**:

- `method` _str_ - HTTP method (e.g. &#x27;GET&#x27;, &#x27;POST&#x27;)
- `path` _str_ - URL path or full URL
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `requests.Response` - The response from the request
  

**Raises**:

- `UntrustedURLError` - If the resolved URL is not a trusted aiXplain origin.

#### request

```python
def request(method: str, path: str, **kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L673)

Sends an HTTP request.

**Arguments**:

- `method` _str_ - HTTP method (e.g. &#x27;GET&#x27;, &#x27;POST&#x27;)
- `path` _str_ - URL path
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `dict` - The response from the request

#### get

```python
def get(path: str, **kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L687)

Sends an HTTP GET request.

**Arguments**:

- `path` _str_ - URL path
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `dict` - The JSON response from the request

#### post

```python
def post(path: str, **kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L699)

Sends an HTTP POST request.

**Arguments**:

- `path` _str_ - URL path
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `dict` - The JSON response from the request

#### request\_stream

```python
def request_stream(method: str, path: str, **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L711)

Sends a streaming HTTP request.

This method is similar to request_raw but enables streaming mode,
which is necessary for Server-Sent Events (SSE) responses.

**Arguments**:

- `method` _str_ - HTTP method (e.g. &#x27;GET&#x27;, &#x27;POST&#x27;)
- `path` _str_ - URL path or full URL
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `requests.Response` - The streaming response (not consumed)
  

**Raises**:

- `APIError` - If the request fails
- `UntrustedURLError` - If the resolved URL is not a trusted aiXplain origin.

