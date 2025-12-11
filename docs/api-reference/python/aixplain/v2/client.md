---
sidebar_label: client
title: aixplain.v2.client
---

#### create\_retry\_session

```python
def create_retry_session(total=None,
                         backoff_factor=None,
                         status_forcelist=None,
                         **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L13)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L43)

#### \_\_init\_\_

```python
def __init__(base_url: str,
             aixplain_api_key: str = None,
             team_api_key: str = None,
             retry_total=DEFAULT_RETRY_TOTAL,
             retry_backoff_factor=DEFAULT_RETRY_BACKOFF_FACTOR,
             retry_status_forcelist=DEFAULT_RETRY_STATUS_FORCELIST)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L44)

Initializes AixplainClient with authentication and retry configuration.

**Arguments**:

- `base_url` _str_ - The base URL for the API.
- `aixplain_api_key` _str, optional_ - The individual API key.
- `team_api_key` _str, optional_ - The team API key.
- `retry_total` _int, optional_ - Total number of retries allowed. Defaults to None, uses DEFAULT_RETRY_TOTAL.
- `retry_backoff_factor` _float, optional_ - Backoff factor to apply between retry attempts. Defaults to None, uses DEFAULT_RETRY_BACKOFF_FACTOR.
- `retry_status_forcelist` _list, optional_ - List of HTTP status codes to force a retry on. Defaults to None, uses DEFAULT_RETRY_STATUS_FORCELIST.

#### request

```python
def request(method: str, path: str, **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L87)

Sends an HTTP request.

**Arguments**:

- `method` _str_ - HTTP method (e.g. &#x27;GET&#x27;, &#x27;POST&#x27;)
- `path` _str_ - URL path
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `requests.Response` - The response from the request

#### get

```python
def get(path: str, **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L104)

Sends an HTTP GET request.

**Arguments**:

- `path` _str_ - URL path
- `kwargs` _dict, optional_ - Additional keyword arguments for the request
  

**Returns**:

- `requests.Response` - The response from the request

#### get\_obj

```python
def get_obj(path: str, **kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/client.py#L117)

Sends an HTTP GET request and returns the object.

