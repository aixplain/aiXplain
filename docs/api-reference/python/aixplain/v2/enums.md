---
sidebar_label: enums
title: aixplain.v2.enums
---

`from aixplain import AssetStatus, AssetStatusValue, AttachmentType, AttachmentTypeValue, AuthenticationScheme, AuthenticationSchemeValue, CodeInterpreterModel, DataType, DataTypeValue, ErrorHandler, EvolveType, FileContentType, FileType, FileTypeValue, Function, FunctionType, FunctionValue, Language, LanguageValue, License, LicenseValue, MessageRole, OnboardStatus, OwnershipType, OwnershipTypeValue, Privacy, PrivacyValue, Reaction, ResponseStatus, RunStatus, SessionStatus, SortBy, SortByValue, SortOrder, SortOrderValue, SplittingOptions, SplittingOptionsValue, StorageType, StorageTypeValue, Supplier, SupplierValue`


V2 enums module - self-contained to avoid legacy dependencies.

This module provides all enum types used throughout the v2 SDK.

### AuthenticationScheme Objects

```python
class AuthenticationScheme(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L11)

Authentication schemes supported by integrations.

### FileType Objects

```python
class FileType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L22)

Structural types for File assets.

### FileContentType Objects

```python
class FileContentType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L29)

Legacy content classifications formerly exposed as ``FileType``.

### Function Objects

```python
class Function(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L42)

AI functions supported by the platform.

#### UTILITIES

Add the missing utilities function

#### GUARDRAILS

Guardrail / inspector guard models

### Language Objects

```python
class Language(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L69)

Languages supported by the platform.

### License Objects

```python
class License(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L86)

Licenses supported by the platform.

### AssetStatus Objects

```python
class AssetStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L98)

Asset status values.

### Privacy Objects

```python
class Privacy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L121)

Privacy settings.

### OnboardStatus Objects

```python
class OnboardStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L129)

Onboarding status values.

### OwnershipType Objects

```python
class OwnershipType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L138)

Ownership types.

### SortBy Objects

```python
class SortBy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L146)

Sort options.

### SortOrder Objects

```python
class SortOrder(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L154)

Sort order options.

### ErrorHandler Objects

```python
class ErrorHandler(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L161)

Error handling strategies.

### ResponseStatus Objects

```python
class ResponseStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L168)

Response status values.

### StorageType Objects

```python
class StorageType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L176)

Storage type options.

### Supplier Objects

```python
class Supplier(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L185)

AI model suppliers.

### FunctionType Objects

```python
class FunctionType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L197)

Function type categories.

### EvolveType Objects

```python
class EvolveType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L208)

Evolution types.

### CodeInterpreterModel Objects

```python
class CodeInterpreterModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L216)

Code interpreter models.

### DataType Objects

```python
class DataType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L223)

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
- `BOOLEAN` - Boolean data type.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L252)

Return the string representation of the data type.

### SplittingOptions Objects

```python
class SplittingOptions(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L257)

Enumeration of possible splitting options for text chunking.

This enum defines the different ways that text can be split into chunks,
including by word, sentence, passage, page, and line.

### SessionStatus Objects

```python
class SessionStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L271)

Session status values.

### RunStatus Objects

```python
class RunStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L280)

Run status values for sessions.

### MessageRole Objects

```python
class MessageRole(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L288)

Message role in a session conversation.

### Reaction Objects

```python
class Reaction(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L295)

Reaction types for session messages.

### AttachmentType Objects

```python
class AttachmentType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L302)

Attachment type for session message attachments.

