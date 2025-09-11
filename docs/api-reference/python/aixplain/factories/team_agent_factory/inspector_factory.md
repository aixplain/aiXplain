---
sidebar_label: inspector_factory
title: aixplain.factories.team_agent_factory.inspector_factory
---

Factory module for creating and configuring inspector agents.

This module provides functionality for creating inspector agents that can validate
and monitor team agent operations. Inspectors can be created from existing models
or using automatic configurations.

WARNING: This feature is currently in private beta.

**Example**:

  Create an inspector from a model with adaptive policy::
  
  inspector = InspectorFactory.create_from_model(
  name=&quot;my_inspector&quot;,
  model_id=&quot;my_model&quot;,
- `model_config=\{"prompt"` - &quot;Check if the data is safe to use.&quot;},
  policy=InspectorPolicy.ADAPTIVE,
  )
  

**Notes**:

  Currently only supports GUARDRAILS and TEXT_GENERATION models as inspectors.

### InspectorFactory Objects

```python
class InspectorFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/inspector_factory.py#L39)

Factory class for creating and configuring inspector agents.

This class provides methods for creating inspector agents either from existing
models or using automatic configurations. Inspectors are used to validate and
monitor team agent operations, providing feedback and enforcing policies.

#### create\_from\_model

```python
@classmethod
def create_from_model(
    cls,
    name: Text,
    model: Union[Text, Model],
    model_config: Optional[Dict] = None,
    policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE
) -> Inspector
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/inspector_factory.py#L48)

Create a new inspector agent from an onboarded model.

This method creates an inspector agent using an existing model that has been
onboarded to the platform. The model must be of a supported function type
(currently GUARDRAILS or TEXT_GENERATION).

**Arguments**:

- `name` _Text_ - Name of the inspector agent.
- `model` _Union[Text, Model]_ - Either a Model instance or model ID string
  to use for the inspector.
- `model_config` _Optional[Dict], optional_ - Configuration parameters for
  the inspector model (e.g., prompts, thresholds). Defaults to None.
- `policy` - Action to take upon negative feedback (WARN/ABORT/ADAPTIVE)
  or a callable function. If callable, must have name &quot;process_response&quot;,
  arguments &quot;model_response&quot; and &quot;input_content&quot; (both strings), and
  return InspectorAction. Defaults to ADAPTIVE.
  

**Returns**:

- `Inspector` - Created and configured inspector agent.
  

**Raises**:

- `ValueError` - If:
  - Model ID is invalid
  - Model is not onboarded
  - Model function is not supported
- `Exception` - If model retrieval fails

#### create\_auto

```python
@classmethod
def create_auto(
    cls,
    auto: InspectorAuto,
    name: Optional[Text] = None,
    policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE
) -> Inspector
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/inspector_factory.py#L124)

Create a new inspector agent using automatic configuration.

This method creates an inspector agent using a pre-configured InspectorAuto
instance, which provides automatic inspection capabilities without requiring
a specific model.

**Arguments**:

- `auto` _InspectorAuto_ - Pre-configured automatic inspector instance.
- `name` _Optional[Text], optional_ - Name for the inspector. If not provided,
  uses the name from the auto configuration. Defaults to None.
- `policy` - Action to take upon negative feedback (WARN/ABORT/ADAPTIVE)
  or a callable function. If callable, must have name &quot;process_response&quot;,
  arguments &quot;model_response&quot; and &quot;input_content&quot; (both strings), and
  return InspectorAction. Defaults to ADAPTIVE.
  

**Returns**:

- `Inspector` - Created and configured inspector agent using automatic
  inspection capabilities.

