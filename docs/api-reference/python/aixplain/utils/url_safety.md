---
sidebar_label: url_safety
title: aixplain.utils.url_safety
---

Central URL trust policy for the SDK (BUG-939).

Three unrelated code paths used to trust a URL simply because it parsed:

* the configured endpoints (``BACKEND_URL``, ``MODELS_RUN_URL``,
  ``PIPELINES_RUN_URL``), which are read straight from the environment and can
  therefore be set by any ``.env`` on the machine;
* URLs handed to the SDK by a caller or read out of a backend response, which
  were gated only by ``validators.url()`` -- a *syntax* check that happily
  accepts ``http://169.254.169.254/latest/meta-data/``, ``http://127.0.0.1:8080/x``
  and ``http://10.0.0.1/``;
* the presigned ``uploadUrl``, which decides where every dataset, database file
  and attachment is PUT.

All three decisions live here so the call sites stay one-liners and the policy
cannot drift between v1, v2 and ``aixplain/utils``. This module deliberately
imports nothing from ``aixplain.v2`` -- it is consumed by ``aixplain.utils.config``
and by v1, neither of which may depend on v2.

Residual risk: :func:``4 resolves the host to validate it and then lets
``requests`` resolve it again to connect, so a hostile resolver serving a
zero-TTL record can still swing the second lookup (classic DNS rebinding).
Closing that window requires connecting to the pinned address with an explicit
``Host`` header and an SNI override; it is tracked separately.

#### INSECURE\_OPT\_IN\_ENV\_VAR

Opt-in that allows plain ``http://`` config and upload URLs (local dev, on-prem).

#### ALLOW\_PRIVATE\_FETCH\_ENV\_VAR

Opt-in that allows :func:`safe_get` to reach private/loopback addresses.

#### UPLOAD\_ALLOWLIST\_ENV\_VAR

Comma-separated extra hosts/suffixes accepted by :func:`validate_upload_url`.

#### AIXPLAIN\_HOST\_SUFFIX

Host suffix considered &quot;an aiXplain endpoint&quot; for the config-URL warning.

#### DEFAULT\_UPLOAD\_HOST\_SUFFIXES

Upload hosts accepted without configuration.

#### MAX\_FETCH\_REDIRECTS

How many redirects :func:`safe_get` will follow (each one re-validated).

### UnsafeURLError Objects

```python
class UnsafeURLError(ValueError)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/url_safety.py#L77)

Raised when a URL fails the SDK&#x27;s trust policy.

Subclasses :class:`ValueError` so existing ``except ValueError`` handlers at
the call sites keep working.

#### validate\_config\_url

```python
def validate_config_url(url: str, name: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/url_safety.py#L140)

Validate a configured endpoint URL (``BACKEND_URL``, ``*_RUN_URL``).

Requires ``https://`` unless ``AIXPLAIN_ALLOW_INSECURE_URLS=1``, which is
also what permits ``http://localhost`` for local development. Emits one
WARNING per ``(name, host)`` when the host is not an ``aixplain.com`` host,
because a redirected endpoint is the difference between the team key
reaching aiXplain and reaching whoever wrote the ``.env`` (BUG-939).

**Arguments**:

- ``6 - The configured URL.
- ``7 - The environment variable name, used in messages.
  

**Returns**:

- ``8 - *url* unchanged, when it satisfies the policy.
  

**Raises**:

- ``9 - If the URL is not http(s), has no host, carries
  userinfo, or is ``http://`` without the explicit opt-in.

#### validate\_fetch\_url

```python
def validate_fetch_url(url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/url_safety.py#L227)

Validate a URL the SDK is about to fetch for a caller or from a response.

``validators.url()`` -- the check these call sites used to rely on -- is a
syntax check: against validators 0.35.0 it returns True for
``http://169.254.169.254/latest/meta-data/``, ``http://127.0.0.1:8080/x``
and ``http://10.0.0.1/`` (BUG-939). This is the security check that has to
sit next to it: scheme allowlist, no userinfo, and *every* resolved address
rejected if it is loopback, private, link-local, reserved, multicast,
unspecified or a known cloud-metadata endpoint.

Set ``AIXPLAIN_ALLOW_PRIVATE_FETCH=1`` on an on-prem deployment whose
artifact host lives on a private range. That opt-in relaxes the *private
range* rule only -- the cloud metadata endpoints stay refused either way.
Nobody&#x27;s artifact host is ``169.254.169.254``, and the flag exists to reach
an internal file server, not to let a caller-supplied (or model-generated)
URL read the container&#x27;s instance credentials and upload them.

**Arguments**:

- ``2 - The URL about to be fetched.
  

**Returns**:

- ``3 - *url* unchanged, when it satisfies the policy.
  

**Raises**:

- ``4 - If the scheme, host or any resolved address is rejected,
  or if the host does not resolve.

#### safe\_get

```python
def safe_get(url: str,
             *,
             timeout: Optional[Any] = None,
             stream: bool = False,
             headers: Optional[dict] = None,
             max_redirects: int = MAX_FETCH_REDIRECTS,
             max_bytes: Optional[int] = None,
             session: Optional[requests.Session] = None,
             **kwargs: Any) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/url_safety.py#L323)

GET *url*, applying :func:`validate_fetch_url` to it and to every redirect.

Redirects are followed manually (``allow_redirects=False``) so that each
``Location`` is re-validated: a perfectly public host that 302s to
``http://169.254.169.254/`` is otherwise indistinguishable from a safe fetch.

**Arguments**:

- `url` - The URL to fetch.
- `timeout` - ``requests`` timeout; defaults to
  ``(FETCH_TIMEOUT_CONNECT, FETCH_TIMEOUT_READ)``.
- ``3 - Leave the body unconsumed (ignored when *max_bytes* is set).
- ``4 - Extra request headers.
- ``5 - How many redirects to follow before giving up.
- ``6 - Optional cap on the response body size.
- ``7 - Optional ``requests.Session`` to issue the request on.
- ``0 - Forwarded to ``requests.get``.
  

**Returns**:

- ``3 - The final response. The status is **not** raised on,
  so callers keep their existing error handling.
  

**Raises**:

- ``4 - If the target, or any redirect target, fails the policy,
  or if the redirect budget is exhausted.

#### validate\_upload\_url

```python
def validate_upload_url(url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/url_safety.py#L402)

Validate a presigned ``uploadUrl`` before the SDK PUTs a file to it.

The URL comes straight out of a backend response, so a compromised backend
-- or a ``BACKEND_URL`` redirected by an ambient ``.env`` -- would otherwise
receive every dataset, database file, skill bundle and attachment while the
SDK reported success (BUG-939).

``*.amazonaws.com`` and ``*.aixplain.com`` are allowed by default; extend
with a comma-separated ``AIXPLAIN_UPLOAD_HOST_ALLOWLIST`` (each entry may be
a bare host, ``.suffix`` or ``*.suffix``). https is required unless
``AIXPLAIN_ALLOW_INSECURE_URLS=1``.

**Arguments**:

- ``8 - The presigned upload URL returned by the backend.
  

**Returns**:

- ``9 - *url* unchanged, when it satisfies the policy.
  

**Raises**:

- ``0 - If the scheme or host is not allowed.

