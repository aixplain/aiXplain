---
sidebar_label: inspector
title: aixplain.modules.team_agent.inspector
---

Pre-defined agent for inspecting the data flow within a team agent.
WARNING: This feature is currently in private beta.

WARNING: This feature is currently in private beta.

Example usage:

inspector = Inspector(
    name=&quot;my_inspector&quot;,
    model_id=&quot;my_model&quot;,
    model_config=\{&quot;prompt&quot;: &quot;Check if the data is safe to use.&quot;},
    policy=InspectorPolicy.ADAPTIVE
)

team = TeamAgent(
    name=&quot;team&quot;
    agents=agents,
    description=&quot;team description&quot;,
    llm_id=&quot;xyz&quot;,
    use_mentalist=True,
    inspectors=[inspector],
)

#### AUTO\_DEFAULT\_MODEL\_ID

GPT-4.1 Nano

### InspectorAction Objects

```python
class InspectorAction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L39)

Inspector&#x27;s decision on the next action.

### InspectorOutput Objects

```python
class InspectorOutput(BaseModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L49)

Inspector&#x27;s output.

### InspectorAuto Objects

```python
class InspectorAuto(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L59)

A list of keywords for inspectors configured automatically in the backend.

#### get\_name

```python
def get_name() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L64)

Get the standardized name for this inspector type.

This method generates a consistent name for the inspector by prefixing
the enum value with &quot;inspector_&quot;.

**Returns**:

- `Text` - The inspector name in the format &quot;inspector_&lt;type&gt;&quot;.

### InspectorPolicy Objects

```python
class InspectorPolicy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L76)

Which action to take if the inspector gives negative feedback.

#### WARN

log only, continue execution

#### ABORT

stop execution

#### ADAPTIVE

adjust execution according to feedback

#### validate\_policy\_callable

```python
def validate_policy_callable(policy_func: Callable) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L84)

Validate that the policy callable meets the required constraints.

#### callable\_to\_code\_string

```python
def callable_to_code_string(policy_func: Callable) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L106)

Convert a callable policy function to a code string for serialization.

#### code\_string\_to\_callable

```python
def code_string_to_callable(code_string: str) -> Callable
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L124)

Convert a code string back to a callable function for deserialization.

#### get\_policy\_source

```python
def get_policy_source(func: Callable) -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L259)

Get the source code of a policy function.

This function tries to retrieve the source code of a policy function.
It first checks if the function has a stored _source_code attribute (for functions
created via code_string_to_callable), then falls back to inspect.getsource().

**Arguments**:

- `func` - The function to get source code for
  

**Returns**:

  The source code string if available, None otherwise

### Inspector Objects

```python
class Inspector(ModelWithParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L280)

Pre-defined agent for inspecting the data flow within a team agent.

The model should be onboarded before using it as an inspector.

**Attributes**:

- `name` - The name of the inspector.
- `model_id` - The ID of the model to wrap.
- `model_params` - The configuration for the model.
- `policy` - The policy for the inspector. Can be InspectorPolicy enum or a callable function.
  If callable, must have name &quot;process_response&quot;, arguments &quot;model_response&quot; and &quot;input_content&quot; (both strings),
  and return InspectorAction. Default is ADAPTIVE.

#### \_\_init\_\_

```python
def __init__(*args, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L299)

Initialize an Inspector instance.

This method initializes an inspector with either a custom model or an
automatic configuration. If auto is specified, it uses the default
auto model ID.

**Arguments**:

- `*args` - Variable length argument list passed to parent class.
- `**kwargs` - Arbitrary keyword arguments. Supported keys:
  - name (Text): The inspector&#x27;s name
  - model_id (Text): The model ID to use
  - model_params (Dict, optional): Model configuration
  - auto (InspectorAuto, optional): Auto configuration type
  - policy (InspectorPolicy, optional): Inspector policy
  

**Notes**:

  If auto is specified in kwargs, model_id is automatically set to
  AUTO_DEFAULT_MODEL_ID.

#### validate\_name

```python
@field_validator("name")
def validate_name(cls, v: Text) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L324)

Validate the inspector name field.

This validator ensures that the inspector&#x27;s name is not empty.

**Arguments**:

- `v` _Text_ - The name value to validate.
  

**Returns**:

- `Text` - The validated name value.
  

**Raises**:

- `ValueError` - If the name is an empty string.

#### model\_dump

```python
def model_dump(by_alias: bool = False, **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L353)

Override model_dump to handle callable policy serialization.

#### model\_validate

```python
@classmethod
def model_validate(cls, data: Union[Dict, "Inspector"]) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L368)

Override model_validate to handle callable policy deserialization.

