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

### Language Objects

```python
class Language(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L48)

Languages supported by the platform.

### License Objects

```python
class License(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L65)

Licenses supported by the platform.

### AssetStatus Objects

```python
class AssetStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L77)

Asset status values.

### Privacy Objects

```python
class Privacy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L100)

Privacy settings.

### OnboardStatus Objects

```python
class OnboardStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L108)

Onboarding status values.

### OwnershipType Objects

```python
class OwnershipType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L117)

Ownership types.

### SortBy Objects

```python
class SortBy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L125)

Sort options.

### SortOrder Objects

```python
class SortOrder(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L133)

Sort order options.

### ErrorHandler Objects

```python
class ErrorHandler(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L140)

Error handling strategies.

### ResponseStatus Objects

```python
class ResponseStatus(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L147)

Response status values.

### StorageType Objects

```python
class StorageType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L155)

Storage type options.

### Supplier Objects

```python
class Supplier(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L164)

AI model suppliers.

### FunctionType Objects

```python
class FunctionType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L176)

Function type categories.

### EvolveType Objects

```python
class EvolveType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L187)

Evolution types.

### CodeInterpreterModel Objects

```python
class CodeInterpreterModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L195)

Code interpreter models.

### DataType Objects

```python
class DataType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L202)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L231)

Return the string representation of the data type.

### SplittingOptions Objects

```python
class SplittingOptions(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums.py#L236)

Enumeration of possible splitting options for text chunking.

This enum defines the different ways that text can be split into chunks,
including by word, sentence, passage, page, and line.

