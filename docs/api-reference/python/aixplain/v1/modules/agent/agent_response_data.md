---
sidebar_label: agent_response_data
title: aixplain.v1.modules.agent.agent_response_data
---

Agent response data.

This module contains the AgentResponseData class, which is used to encapsulate the
input, output, and execution details of an agent&#x27;s response, including intermediate
steps and execution statistics.

### Artifact Objects

```python
@dataclass
class Artifact()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L14)

A user-facing deliverable produced during an agent run.

v1 mirror of :class:`aixplain.v2.agent.Artifact` — same field names, same
semantics. Artifacts come from two sources:

- ``source=&quot;tool_output&quot;`` — media a tool generated (image/audio/video/page).
Carries a ``url``, usually a **presigned** URL.
- ``source=&quot;workspace&quot;`` — a file the agent wrote into its workspace.
Carries inline UTF-8 text in ``content`` (binary workspace files are
skipped by the engine; there is no uploader yet).

Exactly one of ``url`` / ``content`` is populated.

**Warnings**:

  ``url_expires_at`` is when the **presigned URL** dies, not the artifact.
  Observed in the wild: a 24h window on a generated image URL. If you
  persist artifact URLs (database, cache, sent email), re-host the bytes
  before ``url_expires_at`` or the links will rot.
  
  ``category`` and ``source`` are plain strings, not enums: the engine may add
  new media categories before this SDK knows about them, and an unknown value
  must pass through rather than raise.
  

**Attributes**:

- ``1 _str_ - Unique identifier of the artifact.
- ``2 _str_ - URL basename, or workspace-relative path (``outputs/report.csv``).
- ``5 _Optional[str]_ - Human-friendly title, when the engine set one.
- ``6 _Optional[str]_ - MIME type of the artifact content.
- ``7 _str_ - ``image`` / ``audio`` / ``video`` / ``page`` / ``document``
  / ``code`` / ``data`` / ``archive`` / ``other``, or any newer value
  the engine introduces.
- ``6 _str_ - ``tool_output`` or ``workspace``.
- ``1 _Optional[str]_ - Tool that produced it (``tool_output`` only).
- ``4 _Optional[str]_ - Presigned URL (``tool_output`` only).
- ``7 _Optional[str]_ - ISO-8601 expiry of ``url``.
- ``0 _Optional[str]_ - Inline UTF-8 text (``workspace`` only).
- ``3 _Optional[str]_ - Content digest (``workspace`` only).
- ``6 _Optional[int]_ - Content size in bytes (``workspace`` only).
- ``9 _bool_ - Whether the final answer cited the artifact.
- ``0 _str_ - ISO-8601 creation timestamp.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Artifact"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L84)

Create an Artifact from a snake_case or camelCase payload.

Unknown keys are ignored, and missing keys fall back to the field
defaults. If a payload carries both spellings of a field, the one
appearing last wins (matching the v2 decoder).

**Arguments**:

- `data` _Dict[str, Any]_ - The artifact payload.
  

**Returns**:

- `Artifact` - A new instance populated with the payload data.

#### from\_list

```python
@classmethod
def from_list(cls, value: Any) -> List["Artifact"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L106)

Decode an ``artifacts`` payload without ever raising.

**Arguments**:

- `value` _Any_ - The raw ``artifacts`` value. Anything that is not a
  list (including ``None``) yields an empty list.
  

**Returns**:

- `List[Artifact]` - The decodable entries; junk entries are dropped.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L129)

Convert the artifact to its camelCase wire representation.

**Returns**:

  Dict[str, Any]: The artifact as a dictionary, matching the keys the
  v2 SDK emits.

#### get

```python
def get(key: str, default: Optional[Any] = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L139)

Get an attribute value, dict-style, with a default.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
- `default` _Optional[Any], optional_ - The value to return if the
  attribute is not found. Defaults to None.
  

**Returns**:

- `Any` - The value of the attribute, or the default value if not found.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L152)

Get an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The value of the attribute, or None if not found.

### AgentResponseData Objects

```python
class AgentResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L164)

A container for agent execution response data.

This class encapsulates the input, output, and execution details of an agent&#x27;s
response, including intermediate steps and execution statistics.

**Attributes**:

- `input` _Optional[Any]_ - The input provided to the agent.
- `output` _Optional[Any]_ - The final output from the agent.
- `session_id` _str_ - Identifier for the conversation session.
- `intermediate_steps` _List[Any]_ - List of steps taken during execution.
- `steps` _List[Any]_ - Reformatted list of steps with detailed execution info.
- `execution_stats` _Optional[Dict[str, Any]]_ - Statistics about the execution.
- `critiques` _str_ - Any critiques or feedback about the execution.
- `artifacts` _List[Artifact]_ - Deliverables produced during the run. Always a
  list, empty when the run produced none or the backend predates
  artifact support.

#### \_\_init\_\_

```python
def __init__(input: Optional[Any] = None,
             output: Optional[Any] = None,
             session_id: str = "",
             intermediate_steps: Optional[List[Any]] = None,
             steps: Optional[List[Any]] = None,
             execution_stats: Optional[Dict[str, Any]] = None,
             critiques: Optional[str] = None,
             artifacts: Optional[List[Any]] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L183)

Initialize a new AgentResponseData instance.

**Arguments**:

- `input` _Optional[Any], optional_ - The input provided to the agent.
  Defaults to None.
- `output` _Optional[Any], optional_ - The final output from the agent.
  Defaults to None.
- `session_id` _str, optional_ - Identifier for the conversation session.
  Defaults to &quot;&quot;.
- `intermediate_steps` _Optional[List[Any]], optional_ - List of steps taken
  during execution. Defaults to None.
- `steps` _Optional[List[Any]], optional_ - Reformatted list of steps with
  detailed execution info. Defaults to None.
- `execution_stats` _Optional[Dict[str, Any]], optional_ - Statistics about
  the execution. Defaults to None.
- `critiques` _Optional[str], optional_ - Any critiques or feedback about
  the execution. Defaults to None.
- `artifacts` _Optional[List[Any]], optional_ - Deliverables produced during
  the run, as raw payload dictionaries or :class:`Artifact`
  instances. Anything undecodable is dropped. Defaults to None,
  which yields an empty list.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L226)

Create an AgentResponseData instance from a dictionary.

**Arguments**:

- `data` _Dict[str, Any]_ - Dictionary containing response data with keys:
  - input: The input provided to the agent
  - output: The final output from the agent
  - session_id: Identifier for the conversation session
  - intermediate_steps: List of steps taken during execution
  - steps: Reformatted list of steps with detailed execution info
  - executionStats: Statistics about the execution
  - critiques: Any critiques or feedback
  - artifacts: Deliverables produced during the run
  

**Returns**:

- `AgentResponseData` - A new instance populated with the dictionary data.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L254)

Convert the response data to a dictionary representation.

**Returns**:

  Dict[str, Any]: A dictionary containing all response data with keys:
  - input: The input provided to the agent
  - output: The final output from the agent
  - session_id: Identifier for the conversation session
  - intermediate_steps: List of steps taken during execution
  - steps: Reformatted list of steps with detailed execution info
  - executionStats: Statistics about the execution
  - execution_stats: Alias for executionStats
  - critiques: Any critiques or feedback
  - artifacts: Deliverables produced during the run

#### get

```python
def get(key: str, default: Optional[Any] = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L281)

Get an attribute value using attribute-style access.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
- `default` _Optional[Any], optional_ - The value to return if the attribute
  is not found. Defaults to None.
  

**Returns**:

- `Any` - The value of the attribute, or the default value if not found.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L294)

Get an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The value of the attribute, or None if not found.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L305)

Set an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The name of the attribute to set.
- `value` _Any_ - The value to assign to the attribute.
  

**Raises**:

- `KeyError` - If the key is not a valid attribute of the class.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L320)

Return a string representation of the response data.

**Returns**:

- `str` - A string showing all attributes and their values in a readable format.

#### \_\_contains\_\_

```python
def __contains__(key: Text) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/agent/agent_response_data.py#L338)

Check if an attribute exists using &#x27;in&#x27; operator.

**Arguments**:

- `key` _Text_ - The name of the attribute to check.
  

**Returns**:

- `bool` - True if the attribute exists and is accessible, False otherwise.

