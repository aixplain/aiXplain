---
sidebar_label: mixins
title: aixplain.v2.mixins
---

Mixins for v2 API classes.

### ParameterInput Objects

```python
class ParameterInput(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/mixins.py#L10)

TypedDict for individual parameter input configuration.

### ParameterDefinition Objects

```python
class ParameterDefinition(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/mixins.py#L27)

TypedDict for parameter definition structure.

### ToolDict Objects

```python
class ToolDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/mixins.py#L38)

TypedDict defining the expected structure for tool serialization.

This provides type safety and documentation for the as_tool() method return value.

### ToolableMixin Objects

```python
class ToolableMixin(ABC)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/mixins.py#L65)

Mixin that enforces the as_tool() interface for classes that can be used as tools.

Any class that inherits from this mixin must implement the as_tool() method,
which serializes the object into a format suitable for agent tool usage.

#### as\_tool

```python
@abstractmethod
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/mixins.py#L74)

Serialize this object as a tool for agent creation.

This method converts the object into a dictionary format that can be used
as a tool when creating agents. The format is strictly typed using ToolDict.

**Returns**:

- `ToolDict` - A typed dictionary representing this object as a tool with:
  - id: The tool&#x27;s unique identifier
  - name: The tool&#x27;s display name
  - description: The tool&#x27;s description
  - supplier: The supplier code (e.g., &quot;aixplain&quot;)
  - parameters: Optional list of parameter configurations
  - function: The tool&#x27;s function type (e.g., &quot;utilities&quot;)
  - type: The tool type (e.g., &quot;model&quot;)
  - version: The tool&#x27;s version as a string
  - assetId: The tool&#x27;s asset ID (usually same as id)
  

**Raises**:

- `NotImplementedError` - If the subclass doesn&#x27;t implement this method

