---
sidebar_label: evolver_response_data
title: aixplain.modules.team_agent.evolver_response_data
---

### EvolverResponseData Objects

```python
class EvolverResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L7)

Container for team agent evolution response data.

This class encapsulates all the data returned from a team agent evolution
process, including the evolved agent, code, evaluation reports, and
historical archive information.

**Attributes**:

- `evolved_agent` _TeamAgent_ - The evolved team agent instance.
- `current_code` _str_ - The current YAML code representation of the agent.
- `evaluation_report` _str_ - Report containing evaluation results.
- `comparison_report` _str_ - Report comparing different agent versions.
- `criteria` _str_ - Criteria used for evolution evaluation.
- `archive` _List[str]_ - Historical archive of previous versions.
- `current_output` _str_ - Current output from the agent.

#### \_\_init\_\_

```python
def __init__(evolved_agent: "TeamAgent",
             current_code: Text,
             evaluation_report: Text,
             comparison_report: Text,
             criteria: Text,
             archive: List[Text],
             current_output: Text = "") -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L24)

Initialize the EvolverResponseData instance.

**Arguments**:

- `evolved_agent` _TeamAgent_ - The evolved team agent instance.
- `current_code` _str_ - The current YAML code representation.
- `evaluation_report` _str_ - Report containing evaluation results.
- `comparison_report` _str_ - Report comparing different versions.
- `criteria` _str_ - Criteria used for evolution evaluation.
- `archive` _List[str]_ - Historical archive of previous versions.
- `current_output` _str, optional_ - Current output from the agent.
  Defaults to empty string.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any], llm_id: Text,
              api_key: Text) -> "EvolverResponseData"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L56)

Create an EvolverResponseData instance from a dictionary.

**Arguments**:

- `data` _Dict[str, Any]_ - Dictionary containing the response data.
- `llm_id` _str_ - The LLM identifier for building the team agent.
- `api_key` _str_ - API key for accessing the LLM service.
  

**Returns**:

- `EvolverResponseData` - A new instance created from the dictionary data.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L82)

Convert the EvolverResponseData instance to a dictionary.

**Returns**:

  Dict[str, Any]: Dictionary representation of the instance data.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L99)

Get an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The attribute name to retrieve.
  

**Returns**:

- `Any` - The value of the requested attribute, or None if not found.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L111)

Set an attribute value using dictionary-style access.

**Arguments**:

- `key` _str_ - The attribute name to set.
- `value` _Any_ - The value to assign to the attribute.
  

**Raises**:

- `KeyError` - If the key is not a valid attribute of the class.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/evolver_response_data.py#L127)

Return a string representation of the EvolverResponseData instance.

**Returns**:

- `str` - A string representation showing key attributes of the instance.

