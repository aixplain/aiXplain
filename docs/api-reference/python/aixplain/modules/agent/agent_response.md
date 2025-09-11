---
sidebar_label: agent_response
title: aixplain.modules.agent.agent_response
---

### AgentResponse Objects

```python
class AgentResponse(ModelResponse)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L10)

A response object for agent execution results.

This class extends ModelResponse to handle agent-specific response data,
including intermediate steps and execution statistics. It provides dictionary-like
access to response data and serialization capabilities.

**Attributes**:

- `status` _ResponseStatus_ - The status of the agent execution.
- `data` _Optional[AgentResponseData]_ - Structured data from the agent execution.
- `details` _Optional[Union[Dict, List]]_ - Additional execution details.
- `completed` _bool_ - Whether the execution has completed.
- `error_message` _Text_ - Error message if execution failed.
- `used_credits` _float_ - Number of credits used for execution.
- `run_time` _float_ - Total execution time in seconds.
- `usage` _Optional[Dict]_ - Resource usage information.
- `url` _Optional[Text]_ - URL for asynchronous result polling.

#### \_\_init\_\_

```python
def __init__(status: ResponseStatus = ResponseStatus.FAILED,
             data: Optional[Union[AgentResponseData,
                                  "EvolverResponseData"]] = None,
             details: Optional[Union[Dict, List]] = {},
             completed: bool = False,
             error_message: Text = "",
             used_credits: float = 0.0,
             run_time: float = 0.0,
             usage: Optional[Dict] = None,
             url: Optional[Text] = None,
             **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L28)

Initialize a new AgentResponse instance.

**Arguments**:

- `status` _ResponseStatus, optional_ - The status of the agent execution.
  Defaults to ResponseStatus.FAILED.
- `data` _Optional[AgentResponseData], optional_ - Structured data from the
  agent execution. Defaults to None.
- `details` _Optional[Union[Dict, List]], optional_ - Additional execution
  details. Defaults to \{}.
- `completed` _bool, optional_ - Whether the execution has completed.
  Defaults to False.
- `error_message` _Text, optional_ - Error message if execution failed.
  Defaults to &quot;&quot;.
- `used_credits` _float, optional_ - Number of credits used for execution.
  Defaults to 0.0.
- `run_time` _float, optional_ - Total execution time in seconds.
  Defaults to 0.0.
- `usage` _Optional[Dict], optional_ - Resource usage information.
  Defaults to None.
- `url` _Optional[Text], optional_ - URL for asynchronous result polling.
  Defaults to None.
- `**kwargs` - Additional keyword arguments passed to ModelResponse.

#### \_\_getitem\_\_

```python
def __getitem__(key: Text) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L79)

Get a response attribute using dictionary-style access.

Overrides the parent class&#x27;s __getitem__ to handle AgentResponseData
serialization when accessing the &#x27;data&#x27; key.

**Arguments**:

- `key` _Text_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The value of the attribute. For &#x27;data&#x27; key, returns the
  serialized dictionary form.

#### \_\_setitem\_\_

```python
def __setitem__(key: Text, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L96)

Set a response attribute using dictionary-style access.

Overrides the parent class&#x27;s __setitem__ to handle AgentResponseData
deserialization when setting the &#x27;data&#x27; key.

**Arguments**:

- `key` _Text_ - The name of the attribute to set.
- `value` _Any_ - The value to assign. For &#x27;data&#x27; key, can be either a
  dictionary or AgentResponseData instance.

#### to\_dict

```python
def to_dict() -> Dict[Text, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L114)

Convert the response to a dictionary representation.

Overrides the parent class&#x27;s to_dict to handle AgentResponseData
serialization in the output dictionary.

**Returns**:

  Dict[Text, Any]: A dictionary containing all response data, with the
  &#x27;data&#x27; field containing the serialized AgentResponseData.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_response.py#L128)

Return a string representation of the response.

**Returns**:

- `str` - A string showing all attributes and their values in a readable format,
  with the class name changed from ModelResponse to AgentResponse.

