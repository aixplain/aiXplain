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

File types supported by the platform.

### Function Objects

```python
class Function(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L33)

AI functions supported by the platform.

#### UTILITIES

Add the missing utilities function

#### GUARDRAILS

Guardrail / inspector guard models

### Language Objects

```python
class Language(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L49)

Languages supported by the platform.

### License Objects

```python
class License(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L66)

Licenses supported by the platform.

### AssetStatus Objects

```python
class AssetStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L78)

Asset status values.

### Privacy Objects

```python
class Privacy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L101)

Privacy settings.

### OnboardStatus Objects

```python
class OnboardStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L109)

Onboarding status values.

### OwnershipType Objects

```python
class OwnershipType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L118)

Ownership types.

### SortBy Objects

```python
class SortBy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L126)

Sort options.

### SortOrder Objects

```python
class SortOrder(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L134)

Sort order options.

### ErrorHandler Objects

```python
class ErrorHandler(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L141)

Error handling strategies.

### ResponseStatus Objects

```python
class ResponseStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L148)

Response status values.

### StorageType Objects

```python
class StorageType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L156)

Storage type options.

### Supplier Objects

```python
class Supplier(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L165)

AI model suppliers.

### FunctionType Objects

```python
class FunctionType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L177)

Function type categories.

### EvolveType Objects

```python
class EvolveType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L188)

Evolution types.

### CodeInterpreterModel Objects

```python
class CodeInterpreterModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L196)

Code interpreter models.

### DataType Objects

```python
class DataType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L203)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L232)

Return the string representation of the data type.

### SplittingOptions Objects

```python
class SplittingOptions(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L237)

Enumeration of possible splitting options for text chunking.

This enum defines the different ways that text can be split into chunks,
including by word, sentence, passage, page, and line.

### SessionStatus Objects

```python
class SessionStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L251)

Session status values.

### RunStatus Objects

```python
class RunStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L260)

Run status values for sessions.

### MessageRole Objects

```python
class MessageRole(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L268)

Message role in a session conversation.

### Reaction Objects

```python
class Reaction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L275)

Reaction types for session messages.

### AttachmentType Objects

```python
class AttachmentType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L282)

Attachment type for session message attachments.

