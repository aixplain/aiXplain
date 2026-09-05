---
sidebar_label: client
title: aixplain.v2.client
---

Client module for making HTTP requests to the aiXplain API.

#### default\_timeout

```python
def default_timeout() -> Tuple[float, float]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L52)

Resolve the default (connect, read) timeout, honouring env overrides.

``AIXPLAIN_HTTP_CONNECT_TIMEOUT`` / ``AIXPLAIN_HTTP_READ_TIMEOUT`` (seconds)
override the built-in defaults per environment without a code change.

#### create\_retry\_session

```python
def create_retry_session(total: Optional[int] = None,
                         backoff_factor: Optional[float] = None,
                         status_forcelist: Optional[List[int]] = None,
                         **kwargs: Any) -> requests.Session
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L64)

Creates a requests.Session with a specified retry strategy.

**Arguments**:

- `total` _int, optional_ - Total number of retries allowed. Defaults to 5.
- `backoff_factor` _float, optional_ - Backoff factor to apply between retry attempts. Defaults to 0.1.
- `status_forcelist` _list, optional_ - List of HTTP status codes to force a retry on. Defaults to [500, 502, 503, 504].
- `kwargs` _dict, optional_ - Additional keyword arguments for internal Retry object.
  

**Returns**:

- `requests.Session` - A requests.Session object with the specified retry strategy.

### AixplainClient Objects

```python
class AixplainClient()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L98)

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
        timeout: Optional[TimeoutType] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L101)

Initialize AixplainClient with authentication and retry configuration.

**Arguments**:

- `base_url` _str_ - The base URL for the API.
- `aixplain_api_key` _str, optional_ - The individual API key.
- `team_api_key` _str, optional_ - The team API key.
- `retry_total` _int_ - Total number of retries allowed. Defaults to 5.
- `retry_backoff_factor` _float_ - Backoff factor between retry attempts. Defaults to 0.1.
- `retry_status_forcelist` _list_ - HTTP status codes that trigger a retry. Defaults to [500, 502, 503, 504].
  timeout (float or (float, float) tuple, optional): Default timeout for every
  request that doesn&#x27;t pass its own ``timeout=``. Defaults to
  (AIXPLAIN_HTTP_CONNECT_TIMEOUT or 10, AIXPLAIN_HTTP_READ_TIMEOUT or 300)
  seconds. Individual calls can still override it per request.

#### request\_raw

```python
def request_raw(method: str, path: str, **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L150)

Sends an HTTP request.

**Arguments**:

- `method` _str_ - HTTP method (e.g. &#x27;GET&#x27;, &#x27;POST&#x27;)
- `path` _str_ - URL path or full URL
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `requests.Response` - The response from the request

#### request

```python
def request(method: str, path: str, **kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L190)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L204)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L216)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L228)

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

