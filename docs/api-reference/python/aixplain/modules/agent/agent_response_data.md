---
sidebar_label: agent_response_data
title: aixplain.modules.agent.agent_response_data
---

### AgentResponseData Objects

```python
class AgentResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L4)

A container for agent execution response data.

This class encapsulates the input, output, and execution details of an agent&#x27;s
response, including intermediate steps and execution statistics.

**Attributes**:

- `input` _Optional[Any]_ - The input provided to the agent.
- `output` _Optional[Any]_ - The final output from the agent.
- `session_id` _str_ - Identifier for the conversation session.
- `intermediate_steps` _List[Any]_ - List of steps taken during execution.
- `execution_stats` _Optional[Dict[str, Any]]_ - Statistics about the execution.
- `critiques` _str_ - Any critiques or feedback about the execution.

#### \_\_init\_\_

```python
def __init__(input: Optional[Any] = None,
             output: Optional[Any] = None,
             session_id: str = "",
             intermediate_steps: Optional[List[Any]] = None,
             execution_stats: Optional[Dict[str, Any]] = None,
             critiques: Optional[str] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L18)

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
- `execution_stats` _Optional[Dict[str, Any]], optional_ - Statistics about
  the execution. Defaults to None.
- `critiques` _Optional[str], optional_ - Any critiques or feedback about
  the execution. Defaults to None.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L51)

Create an AgentResponseData instance from a dictionary.

**Arguments**:

- `data` _Dict[str, Any]_ - Dictionary containing response data with keys:
  - input: The input provided to the agent
  - output: The final output from the agent
  - session_id: Identifier for the conversation session
  - intermediate_steps: List of steps taken during execution
  - executionStats: Statistics about the execution
  - critiques: Any critiques or feedback
  

**Returns**:

- `AgentResponseData` - A new instance populated with the dictionary data.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L75)

Convert the response data to a dictionary representation.

**Returns**:

  Dict[str, Any]: A dictionary containing all response data with keys:
  - input: The input provided to the agent
  - output: The final output from the agent
  - session_id: Identifier for the conversation session
  - intermediate_steps: List of steps taken during execution
  - executionStats: Statistics about the execution
  - execution_stats: Alias for executionStats
  - critiques: Any critiques or feedback

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L101)

Get an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The value of the attribute, or None if not found.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L112)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L127)

Return a string representation of the response data.

**Returns**:

- `str` - A string showing all attributes and their values in a readable format.

#### \_\_contains\_\_

```python
def __contains__(key: Text) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response_data.py#L143)

Check if an attribute exists using &#x27;in&#x27; operator.

**Arguments**:

- `key` _Text_ - The name of the attribute to check.
  

**Returns**:

- `bool` - True if the attribute exists and is accessible, False otherwise.

