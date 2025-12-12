---
sidebar_label: inspector
title: aixplain.v2.inspector
---

Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

Example usage:
    ```python
    from aixplain.v2 import Inspector, InspectorTarget, InspectorPolicy, InspectorAction, InspectorOutput

    # Using built-in policy
    inspector = Inspector(
        name="my_inspector",
        model_id="model_id_here",
        model_params={"prompt": "Check if the data is safe to use."},
        policy=InspectorPolicy.ADAPTIVE
    )

    # Using custom policy
    def process_response(model_response, input_content: str) -> InspectorOutput:
        # Custom logic here
        return InspectorOutput(
            critiques="...",
            content_edited="...",
            action=InspectorAction.CONTINUE
        )

    inspector = Inspector(
        name="custom_inspector",
        model_id="model_id_here",
        model_params={"prompt": "Custom inspection prompt"},
        policy=process_response
    )

    # Use with team agent
    team_agent = Agent(
        name="team",
        subagents=[agent1, agent2],
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS]
    )
    ```

#### AUTO\_DEFAULT\_MODEL\_ID

GPT-4.1 Nano

### InspectorTarget Objects

```python
class InspectorTarget(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L55)

Target stages for inspector validation in the team agent pipeline.

This enumeration defines the stages where inspectors can be applied to
validate and ensure quality of the team agent&#x27;s operation.

**Attributes**:

- `INPUT` - Validates the input data before processing.
- `STEPS` - Validates intermediate steps during processing.
- `OUTPUT` - Validates the final output before returning.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L71)

Return the string value of the enum member.

**Returns**:

- `str` - The string value associated with the enum member.

### InspectorAction Objects

```python
class InspectorAction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L80)

Inspector&#x27;s decision on the next action.

**Attributes**:

- `CONTINUE` - Continue execution normally.
- `RERUN` - Rerun the current step.
- `ABORT` - Stop execution completely.

### InspectorPolicy Objects

```python
class InspectorPolicy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L94)

Which action to take if the inspector gives negative feedback.

**Attributes**:

- `WARN` - Log only, continue execution.
- `ABORT` - Stop execution immediately.
- `ADAPTIVE` - Adjust execution according to feedback.

### InspectorAuto Objects

```python
class InspectorAuto(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L108)

A list of keywords for inspectors configured automatically in the backend.

**Attributes**:

- `CORRECTNESS` - Automatic correctness validation.

#### get\_name

```python
def get_name() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L117)

Get the standardized name for this inspector type.

**Returns**:

- `str` - The inspector name in the format &quot;inspector_&lt;type&gt;&quot;.

### InspectorOutput Objects

```python
@dataclass_json

@dataclass
class InspectorOutput()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L128)

Inspector&#x27;s output after validation.

**Attributes**:

- `critiques` - Feedback text from the inspector.
- `content_edited` - Modified content (if any).
- `action` - The action to take next (CONTINUE, RERUN, or ABORT).

### ModelResponse Objects

```python
@dataclass_json

@dataclass
class ModelResponse()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L145)

Model response structure for inspector policy functions.

This is a simplified version that captures the essential fields needed
by inspector policy functions.

**Attributes**:

- `data` - The response data from the model.
- `error_message` - Any error message from the model.
- `status` - Status of the response (e.g., &quot;SUCCESS&quot;, &quot;FAILED&quot;).

#### validate\_policy\_callable

```python
def validate_policy_callable(policy_func: Callable) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L162)

Validate that the policy callable meets the required constraints.

A valid policy function must:
- Be named &#x27;process_response&#x27;
- Have exactly 2 parameters: &#x27;model_response&#x27; and &#x27;input_content&#x27;
- Return InspectorOutput

**Arguments**:

- `policy_func` - The policy function to validate.
  

**Returns**:

- `bool` - True if valid, False otherwise.

#### callable\_to\_code\_string

```python
def callable_to_code_string(policy_func: Callable) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L200)

Convert a callable policy function to a code string for serialization.

**Arguments**:

- `policy_func` - The policy function to convert.
  

**Returns**:

- `str` - The source code of the function as a string.

#### code\_string\_to\_callable

```python
def code_string_to_callable(code_string: str) -> Callable
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L225)

Convert a code string back to a callable function for deserialization.

**Arguments**:

- `code_string` - The source code string to execute.
  

**Returns**:

- `Callable` - The deserialized function.
  

**Raises**:

- `ValueError` - If the code string is invalid or doesn&#x27;t define process_response.

#### get\_policy\_source

```python
def get_policy_source(func: Callable) -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L298)

Get the source code of a policy function.

This function tries to retrieve the source code of a policy function.
It first checks if the function has a stored _source_code attribute (for functions
created via code_string_to_callable), then falls back to inspect.getsource().

**Arguments**:

- `func` - The function to get source code for.
  

**Returns**:

- `Optional[str]` - The source code string if available, None otherwise.

### Inspector Objects

```python
@dataclass
class Inspector()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L320)

Inspector for validating team agent operations.

An inspector validates the behavior of team agents at different stages
(input, steps, output) and can enforce policies to ensure quality,
safety, or correctness.

NOTE: This class does not use @dataclass_json because we need custom
serialization for callable policies.

**Attributes**:

- `name` - The name of the inspector.
- `model` - The model to use for inspection. Can be a model ID (str) or Model object.
- `model_params` - Configuration parameters for the model (e.g., prompts).
- `auto` - Optional automatic configuration type.
- `policy` - The policy for the inspector. Can be InspectorPolicy enum or
  a callable function. If callable, must be named &#x27;process_response&#x27;,
  have arguments &#x27;model_response&#x27; and &#x27;input_content&#x27;, and return
  InspectorOutput. Defaults to ADAPTIVE.
  

**Example**:

    ```python
    # Using model ID
    inspector = Inspector(
        name="safety_check",
        model="model_id",
        model_params={"prompt": "Check for safety issues"},
        policy=InspectorPolicy.ABORT
    )

    # Using Model object with params set on model
    model = aix.Model("model_id")
    model.inputs.query = "Check for safety issues"
    inspector = Inspector(
        name="safety_check",
        model=model,
        policy=InspectorPolicy.ABORT
    )

    # Using custom callable policy
    def process_response(model_response, input_content: str) -> InspectorOutput:
        if "unsafe" in model_response.data:
            return InspectorOutput(
                critiques="Unsafe content detected",
                content_edited="",
                action=InspectorAction.ABORT
            )
        return InspectorOutput(
            critiques="Content is safe",
            content_edited=input_content,
            action=InspectorAction.CONTINUE
        )

    inspector = Inspector(
        name="custom_safety",
        model="model_id",
        model_params={"prompt": "Check for safety"},
        policy=process_response
    )
    ```

#### model

Can be model ID string or Model object

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L391)

Post-initialization validation and setup.

#### to\_dict

```python
def to_dict(encode_json=False) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L441)

Convert inspector to dictionary with proper policy serialization.

**Arguments**:

- `encode_json` - If True, encodes the dict to JSON format.
  

**Returns**:

  Dict[str, Any]: The inspector as a dictionary.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L479)

Create an Inspector from a dictionary with policy deserialization.

**Arguments**:

- `data` - Dictionary containing inspector data.
  

**Returns**:

- `Inspector` - The deserialized inspector instance.

