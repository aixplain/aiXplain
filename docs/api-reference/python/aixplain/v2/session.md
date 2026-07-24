---
sidebar_label: session
title: aixplain.v2.session
---

Session module for aiXplain v2 SDK.

#### resolve\_attachments

```python
def resolve_attachments(context: Any,
                        attachments: Optional[List[Union[str, Path,
                                                         Dict[str, Any]]]],
                        files: Optional[List[Union[str, Path]]],
                        *,
                        error_label: str = "") -> List[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L147)

Normalize the unified ``attachments`` (plus deprecated ``files``) for the API.

Each entry becomes a ``\{url, name, type, mimeType}`` dict. URL entries (``http(s)://``
/ ``s3://`` strings, or dicts carrying a ``url``) pass through unchanged; local paths
(plain strings, or dicts carrying a ``path``) are uploaded to aiXplain storage and the
resulting download link is attached. The ``FileUploader`` is created lazily, only when
an upload is actually needed. Shared by ``Session.add_message`` and ``Agent`` runs.

**Arguments**:

- ``0 - An object exposing ``backend_url`` and ``api_key`` (the SDK context).
- ``5 - The unified attachments list.
- ``6 - Deprecated local-path list (merged in, with a warning).
- ``7 - Optional context for upload-error messages (e.g. ``&quot;session &#x27;s1&#x27;&quot;``).

### SessionMessageAttachment Objects

```python
@dataclass_json

@dataclass
class SessionMessageAttachment()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L294)

Attachment on a session message.

### SessionMessage Objects

```python
@dataclass_json

@dataclass
class SessionMessage()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L308)

A message within a session (not a resource — all ops go through Session).

### ExecutionConfig Objects

```python
@dataclass_json

@dataclass
class ExecutionConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L326)

Per-session execution configuration.

Mirrors the run-time agent parameters historically passed to
``agent.run`` so that messages posted to a session execute the agent
with the same configuration. The backend reads ``executionConfig``
on session create/update and applies it when subsequent user
messages trigger agent runs.

**Attributes**:

- `execution_params` - Backend execution params (output format, max
  tokens, etc.). Both snake_case and camelCase keys are
  accepted; snake_case is normalized to camelCase on send.
- `criteria` - Free-form evaluation criteria sent to the agent.
- `evolve` - Evolution config as a JSON string (kept as a string to
  match the backend contract).
- `identifier` - Free-form identifier the backend can echo back on
  messages (e.g. for client-side correlation).
- `run_response_generation` - Whether the agent should run its final
  response-generation step.
- `budget` - Per-session run budget (cost / duration / iterations). Accepts a
  ``Budget`` instance or a snake_case/camelCase dict. Serialized into
  ``executionParams.budget`` so messages posted to the session run the
  agent with this budget — the session-scoped equivalent of the agent&#x27;s
  own ``agent.budget``.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L363)

Coerce a dict/Budget ``budget`` into a ``Budget`` instance.

#### to\_api\_dict

```python
def to_api_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L369)

Build the camelCase API payload, normalizing nested params.

Only fields the caller set are included so the backend keeps
existing values on partial updates. The deprecated
``execution_params[&#x27;max_iterations&#x27;]`` is folded into
``executionParams.budget.maxIterations`` (Budget wins on conflict) and a
standalone ``executionParams.maxIterations`` is never emitted — mirroring
the agent run path so sessions and direct runs behave identically.

#### coerce

```python
@classmethod
def coerce(cls, value: Any) -> Optional["ExecutionConfig"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L458)

Accept an ExecutionConfig, dict, or None and return a config or None.

### Session Objects

```python
@dataclass_json

@dataclass(repr=False)
class Session(BaseResource, GetResourceMixin[BaseGetParams, "Session"],
              DeleteResourceMixin[BaseDeleteParams, "Session"],
              SearchResourceMixin[BaseSearchParams, "Session"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L488)

Session resource for managing agent conversation sessions.

Sessions are the single entry point for conversation threads: create with
``aix.Session(agent=…)`` + ``save()``, find with ``aix.Session.search(agent=…)``,
and drive with ``agent.run(query, session=…)``. Each session is bound to one
agent (``agent_id``).

#### \_\_post\_init\_\_

```python
def __post_init__(agent: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L527)

Resolve the ``agent`` convenience arg and coerce ``execution_config``.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L560)

Build payload with only mutable fields.

#### search

```python
@classmethod
def search(cls,
           agent: Optional[Any] = None,
           status: Optional[str] = None,
           user_id: Optional[str] = None,
           created_after: Optional[Union[str, datetime]] = None,
           created_before: Optional[Union[str, datetime]] = None,
           memory_enabled: Optional[bool] = None,
           page_number: int = 0,
           page_size: int = 20,
           **kwargs: Any) -> Page["Session"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L574)

Search sessions with optional filters, returning a paginated ``Page``.

The single, standard way to list sessions (there is no ``agent.list_sessions()``
and no bespoke ``Session.list()``). Mirrors the ``search`` on every other
asset, but hits the session list endpoint (a plain ``GET /v1/sessions``
with query-param filters) and wraps the result in a ``Page``.

**Arguments**:

- ``2 - Filter by agent — an :class:``3 instance
  or an agent id string.
- ``4 - Filter by session status (e.g. ``&quot;active&quot;``).
- ``7 - Filter by owning user id.
- ``8 - Lower bound on the session&#x27;s creation time
  (``datetime`` or ISO string).
- ``1 - Upper bound on the session&#x27;s creation time.
- ``2 - When ``True`` return memory-on threads (sessions with
  persisted traces); when ``False`` return memory-off runs. ``None``
  (default) applies no memory filter. *(Backend filter delivery is a
  follow-up; the SDK forwards the parameter today.)*
- ``9 - Zero-indexed page number (default 0).
- ``0 - Page size (default 20).
- ``1 - Accepted for forward compatibility with the standard
  search signature; ignored by the session list endpoint.
  

**Returns**:

- ``2 - A page of Session instances.
  

**Raises**:

- ``3 - If the API response cannot be parsed or
  deserialization fails.
- ``4 - If the API request fails.

#### messages

```python
def messages() -> List[SessionMessage]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L666)

Get all messages in this session.

**Returns**:

  List of SessionMessage instances.
  

**Raises**:

- `ResourceError` - If the API response is not a list or
  deserialization fails.
- `APIError` - If the API request fails.

#### add\_message

```python
def add_message(
        role: str,
        content: str,
        request_id: Optional[str] = None,
        attachments: Optional[List[Union[str, Path, Dict[str, Any]]]] = None,
        files: Optional[List[Union[str, Path]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None) -> SessionMessage
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L690)

Add a message to this session.

**Arguments**:

- `role` - Message role (&quot;user&quot; or &quot;assistant&quot;).
- `content` - Message content. May be empty when ``attachments`` carry the
  turn&#x27;s input (e.g. an audio clip that is itself the prompt).
- `request_id` - Optional request ID to associate with the message.
- `attachments` - The message&#x27;s attachments. Each entry may be:
  
  * a hosted-URL dict ``\{&quot;url&quot;, &quot;type&quot;?, &quot;name&quot;?, &quot;mimeType&quot;?}`` — used as-is;
  * a local-path dict ``\{&quot;path&quot;: &quot;/...&quot;, &quot;type&quot;?, ...}`` — uploaded;
  * a string URL (``http(s)://`` / ``s3://``) — attached as-is;
  * a string local path — uploaded to aiXplain storage.
  
- `content`4 - Deprecated. Local file paths to upload and attach — pass these
  through ``attachments`` instead.
- `content`7 - Per-message per-tool parameter overrides in the platform
  ``[\{id, parameters: [\{name, value}]}]`` shape, applied to the
  run this message triggers. Normally populated automatically from
  the agent&#x27;s tool objects by ``agent.run(query, session=…)``.
  

**Returns**:

  The created SessionMessage.
  

**Raises**:

- ``2 - If the operation fails.
- ``3 - If the API request fails.
- ``4 - If a file upload fails.

#### get\_message

```python
def get_message(message_id: str) -> SessionMessage
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L762)

Get a specific message by ID.

**Arguments**:

- `message_id` - The message ID.
  

**Returns**:

  The SessionMessage.
  

**Raises**:

- `ResourceError` - If deserialization fails.
- `APIError` - If the API request fails (e.g., message not found).

#### delete\_message

```python
def delete_message(message_id: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L785)

Delete a message from this session.

**Arguments**:

- `message_id` - The message ID to delete.
  

**Raises**:

- `APIError` - If the API request fails (e.g., message not found).
- `ResourceError` - If the session is in an invalid state.

#### react

```python
def react(message_id: str, reaction: Optional[str]) -> SessionMessage
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/session.py#L804)

React to a message or clear a reaction.

Only assistant messages can be reacted to.

**Arguments**:

- `message_id` - The message ID to react to.
- `reaction` - &quot;LIKE&quot;, &quot;DISLIKE&quot;, or None to clear.
  

**Returns**:

  The updated SessionMessage.
  

**Raises**:

- `APIError` - If the API request fails (e.g., reacting to a
  non-assistant message).
- `ResourceError` - If deserialization fails.

