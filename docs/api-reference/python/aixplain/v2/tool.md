---
sidebar_label: tool
title: aixplain.v2.tool
---

`from aixplain import Tool, ToolResult`


Tool resource module for managing tools and their integrations.

### ToolResult Objects

```python
@dataclass_json

@dataclass(repr=False)
class ToolResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L54)

Result for a tool.

### Tool Objects

```python
@dataclass_json

@dataclass(repr=False)
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult],
           ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L62)

Resource for tools.

This class represents a tool resource that matches the backend structure.
Tools can be integrations, utilities, or other specialized resources.
Inherits from Model to reuse shared attributes and functionality.

#### DEFAULT\_INTEGRATION\_ID

Python Sandbox (script) integration

#### integration\_path

```python
@property
def integration_path() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L87)

The path of the integration (e.g. ``"aixplain/python-sandbox"``).

Available when the ``integration`` has been resolved to an
`Integration` object that carries a ``path`` attribute.
Returns ``None`` when the integration has not been resolved yet.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L98)

Initialize tool after dataclass creation.

#### actions

```python
@cached_property
def actions() -> Actions
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L177)

Collection of actions available on this tool.

#### inputs

```python
@property
def inputs()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L182)

Tools have multiple actions — use tool.actions['action_name'].inputs instead.

#### inputs

```python
@inputs.setter
def inputs(value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L187)

Prevent setting inputs directly on tools.

#### list\_actions

```python
def list_actions() -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L220)

List available actions for the tool (with integration fallback).

#### list\_inputs

```python
def list_inputs(*actions: str) -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L252)

List available inputs for specified actions.

**Deprecated:** Use ``tool.actions['action_name'].inputs`` to discover and configure action inputs instead.



#### validate\_allowed\_actions

```python
def validate_allowed_actions() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L423)

Validate that all allowed actions are available for this tool.

#### get\_parameters

```python
def get_parameters() -> List[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L463)

Get parameters for the tool in the format expected by agent saving.

#### as\_tool

```python
def as_tool() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L514)

Serialize this tool for agent creation.

#### run

```python
def run(*args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/tool.py#L579)

Run the tool.

