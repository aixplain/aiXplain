---
sidebar_label: inspector
title: aixplain.v2.inspector
---

Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

### InspectorTarget Objects

```python
class InspectorTarget(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L25)

Target stages for inspector validation in the team agent pipeline.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L32)

Return the string value of the enum.

### InspectorAction Objects

```python
class InspectorAction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L37)

Actions an inspector can take when evaluating content.

### InspectorOnExhaust Objects

```python
class InspectorOnExhaust(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L46)

Action to take when max retries are exhausted.

### InspectorSeverity Objects

```python
class InspectorSeverity(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L53)

Severity level for inspector findings.

### EvaluatorType Objects

```python
class EvaluatorType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L62)

Type of evaluator or editor.

### InspectorActionConfig Objects

```python
@dataclass
class InspectorActionConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L70)

Inspector action configuration.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L77)

Validate that max_retries and on_exhaust are only used with RERUN.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L87)

Convert the action config to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "InspectorActionConfig"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L97)

Create an InspectorActionConfig from a dictionary.

### EvaluatorConfig Objects

```python
@dataclass
class EvaluatorConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L107)

Evaluator configuration for an inspector.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L115)

Validate and convert callable functions to source strings.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L124)

Convert to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "EvaluatorConfig"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L136)

Create an EvaluatorConfig from a dictionary.

### EditorConfig Objects

```python
@dataclass
class EditorConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L147)

Editor configuration for an inspector.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L155)

Validate and convert callable functions to source strings.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L160)

Convert to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "EditorConfig"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L172)

Create an EditorConfig from a dictionary.

### Inspector Objects

```python
@dataclass
class Inspector()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L183)

Inspector v2 configuration object.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L195)

Validate inspector configuration after initialization.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L203)

Convert the inspector to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L220)

Create an Inspector from a dictionary.

