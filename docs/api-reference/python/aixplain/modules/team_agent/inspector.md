---
sidebar_label: inspector
title: aixplain.modules.team_agent.inspector
---

Pre-defined agent for inspecting the data flow within a team agent.

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

### InspectorAuto Objects

```python
class InspectorAuto(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L35)

A list of keywords for inspectors configured automatically in the backend.

#### get\_name

```python
def get_name() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L40)

Get the standardized name for this inspector type.

This method generates a consistent name for the inspector by prefixing
the enum value with &quot;inspector_&quot;.

**Returns**:

- `Text` - The inspector name in the format &quot;inspector_&lt;type&gt;&quot;.

### InspectorPolicy Objects

```python
class InspectorPolicy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L52)

Which action to take if the inspector gives negative feedback.

#### WARN

log only, continue execution

#### ABORT

stop execution

#### ADAPTIVE

adjust execution according to feedback

### Inspector Objects

```python
class Inspector(ModelWithParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L60)

Pre-defined agent for inspecting the data flow within a team agent.

The model should be onboarded before using it as an inspector.

**Attributes**:

- `name` - The name of the inspector.
- `model_id` - The ID of the model to wrap.
- `model_params` - The configuration for the model.
- `policy` - The policy for the inspector. Default is ADAPTIVE.

#### \_\_init\_\_

```python
def __init__(*args, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L77)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L102)

Validate the inspector name field.

This validator ensures that the inspector&#x27;s name is not empty.

**Arguments**:

- `v` _Text_ - The name value to validate.
  

**Returns**:

- `Text` - The validated name value.
  

**Raises**:

- `ValueError` - If the name is an empty string.

