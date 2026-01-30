---
sidebar_label: inspector
title: aixplain.modules.team_agent.inspector
---

Pre-defined agent for inspecting the data flow within a team agent.

WARNING: This feature is currently in private beta.

#### AUTO\_DEFAULT\_MODEL\_ID

GPT-4.1 Nano

### Inspectoraction\_type Objects

```python
class Inspectoraction_type(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L19)

Enum defining the types of actions an inspector can take.

### InspectorOnExhaust Objects

```python
class InspectorOnExhaust(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L28)

Enum defining behavior when inspector retries are exhausted.

### InspectorSeverity Objects

```python
class InspectorSeverity(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L35)

Enum defining the severity levels for inspector findings.

### InspectorActionConfig Objects

```python
class InspectorActionConfig(BaseModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L48)

Configuration for what an inspector should do when it finds issues.

LLM-style actions (continue/rerun/abort):
  - evaluator + evaluator_prompt
  - (rerun only) max_retries/on_exhaust

EDIT action:
  - edit_fn (required)
  - edit_evaluator_fn (optional gate)

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L122)

Convert the action config to a dictionary for serialization.

**Returns**:

  Dict[str, Any]: Dictionary representation with camelCase keys.

### Inspector Objects

```python
class Inspector(BaseModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L136)

Inspector config object (SDK-side).

#### validate\_name

```python
@field_validator("name")
@classmethod
def validate_name(cls, v: Text) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L147)

Validate that the inspector name is not empty.

**Arguments**:

- `v` - The name value to validate.
  

**Returns**:

  The validated name.
  

**Raises**:

- `ValueError` - If the name is empty or whitespace-only.

#### validate\_targets

```python
@field_validator("targets")
@classmethod
def validate_targets(cls, v: List[Text]) -> List[Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L165)

Validate and filter the targets list.

**Arguments**:

- `v` - The list of target names to validate.
  

**Returns**:

  A filtered list containing only non-empty target names.

#### model\_dump

```python
def model_dump(*args, **kwargs) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L178)

Serialize the inspector to a dictionary.

**Arguments**:

- `*args` - Positional arguments passed to parent model_dump.
- `**kwargs` - Keyword arguments passed to parent model_dump.
  

**Returns**:

  Dict[str, Any]: Dictionary representation of the inspector.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L194)

Convert the inspector to a dictionary for serialization.

**Returns**:

  Dict[str, Any]: Dictionary representation excluding None values.

### VerificationInspector Objects

```python
class VerificationInspector(Inspector)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L203)

Convenience inspector for rerun-based verification.

#### \_\_init\_\_

```python
def __init__(
        *,
        evaluator: Text,
        evaluator_prompt: Text = "Check the output against the plan",
        targets: Optional[List[Text]] = None,
        maxRetries: int = 2,
        onExhaust: InspectorOnExhaust = InspectorOnExhaust.CONTINUE,
        severity: InspectorSeverity = InspectorSeverity.MEDIUM,
        name: Text = "VerificationInspector",
        description:
    Text = "Checks output against the plan and requests rerun on mismatch",
        **kwargs: Any)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/inspector.py#L206)

Initialize a verification inspector with rerun-based verification.

**Arguments**:

- `evaluator` - The evaluator model ID to use for verification.
- `evaluator_prompt` - The prompt for the evaluator.
- `targets` - List of target agent names to inspect.
- `maxRetries` - Maximum number of rerun attempts.
- `onExhaust` - Behavior when retries are exhausted.
- `severity` - The severity level of this inspector.
- `name` - The name of the inspector.
- `description` - Description of the inspector&#x27;s purpose.
- `**kwargs` - Additional keyword arguments passed to the parent class.

