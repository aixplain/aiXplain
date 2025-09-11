---
sidebar_label: code_interpreter
title: aixplain.enums.code_interpreter
---

### CodeInterpreterModel Objects

```python
class CodeInterpreterModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/code_interpreter.py#L4)

Enumeration of available Code Interpreter model identifiers.

This enum defines the unique identifiers for different code interpreter models
available in the system. Each value represents a specific model&#x27;s ID that can
be used for code interpretation tasks.

**Attributes**:

- `PYTHON_AZURE` _str_ - Model ID for the Python code interpreter running on Azure.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/code_interpreter.py#L17)

Return the string representation of the model ID.

**Returns**:

- `str` - The model ID value as a string.

