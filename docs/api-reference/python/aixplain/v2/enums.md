---
sidebar_label: enums
title: aixplain.v2.enums
---

V2 enums module - self-contained to avoid legacy dependencies.

This module provides all enum types used throughout the v2 SDK.

### AuthenticationScheme Objects

```python
class AuthenticationScheme(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L9)

Authentication schemes supported by integrations.

### FileType Objects

```python
class FileType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L20)

Structural types for File assets.

### FileContentType Objects

```python
class FileContentType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L28)

Legacy content classifications formerly exposed as ``FileType``.

### Function Objects

```python
class Function(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L41)

AI functions supported by the platform.

#### UTILITIES

Add the missing utilities function

#### GUARDRAILS

Guardrail / inspector guard models

### Language Objects

```python
class Language(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L68)

Languages supported by the platform.

### License Objects

```python
class License(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L85)

Licenses supported by the platform.

### AssetStatus Objects

```python
class AssetStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L97)

Asset status values.

### Privacy Objects

```python
class Privacy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L120)

Privacy settings.

### OnboardStatus Objects

```python
class OnboardStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L128)

Onboarding status values.

### OwnershipType Objects

```python
class OwnershipType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L137)

Ownership types.

### SortBy Objects

```python
class SortBy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L145)

Sort options.

### SortOrder Objects

```python
class SortOrder(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L153)

Sort order options.

### ErrorHandler Objects

```python
class ErrorHandler(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L160)

Error handling strategies.

### ResponseStatus Objects

```python
class ResponseStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L167)

Response status values.

### StorageType Objects

```python
class StorageType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L175)

Storage type options.

### Supplier Objects

```python
class Supplier(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L184)

AI model suppliers.

### FunctionType Objects

```python
class FunctionType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L196)

Function type categories.

### EvolveType Objects

```python
class EvolveType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L207)

Evolution types.

### CodeInterpreterModel Objects

```python
class CodeInterpreterModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L215)

Code interpreter models.

### DataType Objects

```python
class DataType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L222)

Enumeration of supported data types in the aiXplain system.

**Attributes**:

- `AUDIO` - Audio data type.
- `FLOAT` - Floating-point number data type.
- `IMAGE` - Image data type.
- `INTEGER` - Integer number data type.
- `LABEL` - Label/category data type.
- `TENSOR` - Tensor/multi-dimensional array data type.
- `TEXT` - Text data type.
- `VIDEO` - Video data type.
- `EMBEDDING` - Vector embedding data type.
- `NUMBER` - Generic number data type.
- `FLOAT`0 - Boolean data type.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L251)

Return the string representation of the data type.

### SplittingOptions Objects

```python
class SplittingOptions(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L256)

Enumeration of possible splitting options for text chunking.

This enum defines the different ways that text can be split into chunks,
including by word, sentence, passage, page, and line.

### SessionStatus Objects

```python
class SessionStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L270)

Session status values.

### RunStatus Objects

```python
class RunStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L279)

Run status values for sessions.

### MessageRole Objects

```python
class MessageRole(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L287)

Message role in a session conversation.

### Reaction Objects

```python
class Reaction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L294)

Reaction types for session messages.

### AttachmentType Objects

```python
class AttachmentType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L301)

Attachment type for session message attachments.

