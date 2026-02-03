---
sidebar_label: resource
title: aixplain.v2.resource
---

### BaseResource Objects

```python
class BaseResource()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L23)

Base class for all resources.

**Attributes**:

- `context` - Aixplain: The Aixplain instance.
- `RESOURCE_PATH` - str: The resource path.

#### \_\_init\_\_

```python
def __init__(obj: Union[dict, Any])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L35)

Initialize a BaseResource instance.

**Arguments**:

- `obj` - dict: Dictionary containing the resource&#x27;s attributes.

#### \_\_getattr\_\_

```python
def __getattr__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L44)

Return the value corresponding to the key from the wrapped dictionary
if found, otherwise raise an AttributeError.

**Arguments**:

- `key` - str: Attribute name to retrieve from the resource.
  

**Returns**:

- `Any` - Value corresponding to the specified key.
  

**Raises**:

- `AttributeError` - If the key is not found in the wrapped
  dictionary.

#### save

```python
def save()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L65)

Save the resource.

If the resource has an ID, it will be updated, otherwise it will be created.

### BaseListParams Objects

```python
class BaseListParams(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L111)

Base class for all list parameters.

**Attributes**:

- `query` - str: The query string.
- `ownership` - Tuple[OwnershipType, List[OwnershipType]]: The ownership type.
- `sort_by` - SortBy: The attribute to sort by.
- `sort_order` - SortOrder: The order to sort by.
- `page_number` - int: The page number.
- `page_size` - int: The page size.

### BaseGetParams Objects

```python
class BaseGetParams(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L131)

Base class for all get parameters.

**Attributes**:

- `id` - str: The resource ID.

### BaseCreateParams Objects

```python
class BaseCreateParams(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L141)

Base class for all create parameters.

**Attributes**:

- `name` - str: The name of the resource.

### BareCreateParams Objects

```python
class BareCreateParams(BaseCreateParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L151)

Default implementation of create parameters.

### BareListParams Objects

```python
class BareListParams(BaseListParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L157)

Default implementation of list parameters.

### BareGetParams Objects

```python
class BareGetParams(BaseGetParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L163)

Default implementation of get parameters.

### Page Objects

```python
class Page(Generic[R])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L175)

Page of resources.

**Attributes**:

- `items` - List[R]: The list of resources.
- `total` - int: The total number of resources.

### ListResourceMixin Objects

```python
class ListResourceMixin(Generic[L, R])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L201)

Mixin for listing resources.

**Attributes**:

- `PAGINATE_PATH` - str: The path for pagination.
- `PAGINATE_METHOD` - str: The method for pagination.
- `PAGINATE_ITEMS_KEY` - str: The key for the response.
- `PAGINATE_TOTAL_KEY` - str: The key for the total number of resources.
- `PAGINATE_PAGE_TOTAL_KEY` - str: The key for the total number of pages.
- `PAGINATE_DEFAULT_PAGE_NUMBER` - int: The default page number.
- `PAGINATE_DEFAULT_PAGE_SIZE` - int: The default page size.

#### list

```python
@classmethod
def list(cls: Type[R], **kwargs: Unpack[L]) -> Page[R]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L224)

List resources across the first n pages with optional filtering.

**Arguments**:

- `kwargs` - Unpack[L]: The keyword arguments.
  

**Returns**:

- `Page[R]` - Page of BaseResource instances

### GetResourceMixin Objects

```python
class GetResourceMixin(Generic[G, R])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L334)

Mixin for getting a resource.

#### get

```python
@classmethod
def get(cls: Type[R], id: Any, **kwargs: Unpack[G]) -> R
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L338)

Retrieve a single resource by its ID (or other get parameters).

**Arguments**:

- `id` - Any: The ID of the resource to get.
- `kwargs` - Unpack[G]: Get parameters to pass to the request.
  

**Returns**:

- `BaseResource` - Instance of the BaseResource class.
  

**Raises**:

- `ValueError` - If &#x27;RESOURCE_PATH&#x27; is not defined by the subclass.

### CreateResourceMixin Objects

```python
class CreateResourceMixin(Generic[C, R])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L359)

Mixin for creating a resource.

#### create

```python
@classmethod
def create(cls, *args, **kwargs: Unpack[C]) -> R
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L363)

Create a resource.

**Arguments**:

- `kwargs` - Unpack[C]: The keyword arguments.
  

**Returns**:

- `BaseResource` - The created resource.

