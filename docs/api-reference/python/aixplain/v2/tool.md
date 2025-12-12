---
sidebar_label: tool
title: aixplain.v2.tool
---

Tool resource module for managing tools and their integrations.

### ToolResult Objects

```python
@dataclass_json

@dataclass(repr=False)
class ToolResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L21)

Result for a tool.

### Tool Objects

```python
@dataclass_json

@dataclass(repr=False)
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult],
           ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L29)

Resource for tools.

This class represents a tool resource that matches the backend structure.
Tools can be integrations, utilities, or other specialized resources.
Inherits from Model to reuse shared attributes and functionality.

#### DEFAULT\_INTEGRATION\_ID

Script integration

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L52)

Initialize tool after dataclass creation.

Sets up default integration for utility tools if no integration is provided.
Validates integration type if provided.

#### list\_actions

```python
def list_actions() -> List[Action]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L109)

List available actions for the tool.

Overrides parent method to add fallback to base integration and support
for utility models without real integrations.

**Returns**:

  List of Action objects available for this tool. Falls back to
  integration&#x27;s list_actions() if tool&#x27;s own method fails.

#### list\_inputs

```python
def list_inputs(*actions: str) -> List["Action"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L138)

List available inputs for specified actions.

Overrides parent method to add fallback to base integration and support
for utility models without real integrations.

**Arguments**:

- `*actions` - Variable number of action names to get inputs for.
  

**Returns**:

  List of Action objects with their input specifications. Falls back to
  integration&#x27;s list_inputs() if tool&#x27;s own method fails.

#### validate\_allowed\_actions

```python
def validate_allowed_actions() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L263)

Validate that all allowed actions are available for this tool.

Checks that:
- Integration is available
- All actions in allowed_actions list exist in the integration

**Raises**:

- `AssertionError` - If validation fails.

#### get\_parameters

```python
def get_parameters() -> List[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L282)

Get parameters for the tool in the format expected by agent saving.

This method includes both static backend values and dynamically set values
from the ActionInputsProxy instances, ensuring agents get the current
configured action inputs.

#### run

```python
def run(*args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L394)

Run the tool.

For utility models without integration, automatically maps to &quot;run&quot; action if no action specified.

