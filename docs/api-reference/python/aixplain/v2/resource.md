---
sidebar_label: resource
title: aixplain.v2.resource
---

Resource management module for v2 API.

#### with\_hooks

```python
def with_hooks(func: Callable) -> Callable
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L46)

Generic decorator to add before/after hooks to resource operations.

This decorator automatically infers the operation name from the function name
and provides a consistent pattern for all operations:
- Before hooks can return early to bypass the operation
- After hooks can transform the result
- Error handling is consistent across all operations
- Supports both positional and keyword arguments

Usage:
    @with_hooks
    def save(self, **kwargs):
        # operation implementation

    @with_hooks
    def run(self, *args, **kwargs):
        # operation implementation with positional args

#### encode\_resource\_id

```python
def encode_resource_id(resource_id: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L103)

URL encode a resource ID for use in API paths.

**Arguments**:

- `resource_id` - The resource ID to encode
  

**Returns**:

  The URL-encoded resource ID

### HasContext Objects

```python
@runtime_checkable
class HasContext(Protocol)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L117)

Protocol for classes that have a context attribute.

### HasResourcePath Objects

```python
@runtime_checkable
class HasResourcePath(Protocol)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L124)

Protocol for classes that have a RESOURCE_PATH attribute.

### HasFromDict Objects

```python
@runtime_checkable
class HasFromDict(Protocol)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L131)

Protocol for classes that have a from_dict method.

#### from\_dict

```python
@classmethod
def from_dict(cls: type, data: dict) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L135)

Create an instance from a dictionary.

### HasToDict Objects

```python
@runtime_checkable
class HasToDict(Protocol)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L141)

Protocol for classes that have a to_dict method.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L144)

Convert instance to dictionary.

### BaseMixin Objects

```python
class BaseMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L168)

Base mixin with meta capabilities for resource operations.

#### \_\_init\_subclass\_\_

```python
def __init_subclass__(cls: type, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L171)

Initialize subclass with validation.

### BaseResource Objects

```python
@dataclass_json

@dataclass
class BaseResource()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L182)

Base class for all resources.

**Attributes**:

- `context` - Aixplain: The Aixplain instance (hidden from serialization).
- `RESOURCE_PATH` - str: The resource path.
- `id` - str: The resource ID.
- `name` - str: The resource name.

#### is\_modified

```python
@property
def is_modified() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L260)

Check if the resource has been modified since last save.

**Returns**:

- `bool` - True if the resource has been modified, False otherwise

#### is\_deleted

```python
@property
def is_deleted() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L269)

Check if the resource has been deleted.

**Returns**:

- `bool` - True if the resource has been deleted, False otherwise

#### before\_save

```python
def before_save(*args: Any, **kwargs: Any) -> Optional[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L285)

Optional callback called before the resource is saved.

Override this method to add custom logic before saving.

**Arguments**:

- `*args` - Positional arguments passed to the save operation
- `**kwargs` - Keyword arguments passed to the save operation
  

**Returns**:

- `Optional[dict]` - If not None, this result will be returned early,
  bypassing the actual save operation. If None, the
  save operation will proceed normally.

#### after\_save

```python
def after_save(result: Union[dict, Exception], *args: Any,
               **kwargs: Any) -> Optional[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L301)

Optional callback called after the resource is saved.

Override this method to add custom logic after saving.

**Arguments**:

- `result` - The result from the save operation (dict on success,
  Exception on failure)
- `*args` - Positional arguments that were passed to the save operation
- `**kwargs` - Keyword arguments that were passed to the save operation
  

**Returns**:

- `Optional[dict]` - If not None, this result will be returned instead
  of the original result. If None, the original result
  will be returned.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L319)

Build the payload for the save action.

#### save

```python
@with_hooks
def save(*args: Any, **kwargs: Any) -> "BaseResource"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L346)

Save the resource with attribute shortcuts.

This generic implementation provides consistent save behavior across all resources:
- Supports attribute shortcuts: resource.save(name=&quot;new_name&quot;, description=&quot;...&quot;)
- Lets the backend handle validation (name uniqueness, ID existence, etc.)
- If the resource has an ID, it will be updated, otherwise it will be created.

**Arguments**:

- `*args` - Positional arguments (not used, but kept for compatibility)
- `id` - Optional[str] - Set resource ID before saving
- `name` - Optional[str] - Set resource name before saving
- `description` - Optional[str] - Set resource description before saving
- `**kwargs` - Other attributes to set before saving
  

**Returns**:

- `BaseResource` - The saved resource instance
  

**Raises**:

  Backend validation errors as appropriate

#### clone

```python
@with_hooks
def clone(**kwargs: Any) -> "BaseResource"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L387)

Clone the resource and return a copy with id=None.

This generic implementation provides consistent clone behavior across all resources:
- Creates deep copy of the resource
- Resets id=None and _saved_state=None
- Supports attribute shortcuts: resource.clone(name=&quot;new_name&quot;, version=&quot;2.0&quot;)
- Uses hook system for subclass-specific logic (status handling, etc.)

**Arguments**:

- `name` - Optional[str] - Set name on cloned resource
- `description` - Optional[str] - Set description on cloned resource
- `**kwargs` - Other attributes to set on cloned resource
  

**Returns**:

- `BaseResource` - New resource instance with id=None

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L451)

Return a string representation using assetPath &gt; instanceId &gt; id priority.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L461)

Return string representation of the resource.

#### encoded\_id

```python
@property
def encoded_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L466)

Get the URL-encoded version of the resource ID.

**Returns**:

  The URL-encoded resource ID, or empty string if no ID exists

### BaseParams Objects

```python
class BaseParams(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L477)

Base class for parameters that include API key and resource path.

**Attributes**:

- `api_key` - str: The API key for authentication.
- `resource_path` - str: Custom resource path for actions (optional).

### BaseSearchParams Objects

```python
class BaseSearchParams(BaseParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L489)

Base class for all search parameters.

**Attributes**:

- `query` - str: The query string.
- `ownership` - Tuple[OwnershipType, List[OwnershipType]]: The ownership
  type.
- `sort_by` - SortBy: The attribute to sort by.
- `sort_order` - SortOrder: The order to sort by.
- `page_number` - int: The page number.
- `page_size` - int: The page size.
- `resource_path` - str: Optional custom resource path to override
  RESOURCE_PATH.
- `paginate_items_key` - str: Optional key name for items in paginated
  response (overrides PAGINATE_ITEMS_KEY).

### BaseGetParams Objects

```python
class BaseGetParams(BaseParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L516)

Base class for all get parameters.

**Attributes**:

- `id` - str: The resource ID.
- `host` - str: The host URL for the request (optional).

### BaseDeleteParams Objects

```python
class BaseDeleteParams(BaseParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L527)

Base class for all delete parameters.

**Attributes**:

- `id` - str: The resource ID.

### BaseRunParams Objects

```python
class BaseRunParams(BaseParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L537)

Base class for all run parameters.

**Attributes**:

- `text` - str: The text to run.

### BaseResult Objects

```python
@dataclass_json

@dataclass
class BaseResult()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L550)

Abstract base class for running results.

This class provides a minimal interface that concrete result classes
should implement. Subclasses are responsible for defining their own
fields and handling their specific data structures.

### Result Objects

```python
@dataclass_json

@dataclass(repr=False)
class Result(BaseResult)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L565)

Default implementation of running results with common fields.

#### \_\_getattr\_\_

```python
def __getattr__(name: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L577)

Allow access to any field from the raw response data.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L583)

Return a formatted string representation with truncated data.

### DeleteResult Objects

```python
@dataclass_json

@dataclass
class DeleteResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L645)

Result for delete operations.

### Page Objects

```python
class Page(Generic[ResourceT])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L661)

Page of resources.

**Attributes**:

- `items` - List[ResourceT]: The list of resources.
- `total` - int: The total number of resources.

#### \_\_init\_\_

```python
def __init__(results: List[ResourceT], page_number: int, page_total: int,
             total: int)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L674)

Initialize a Page instance.

**Arguments**:

- `results` - List of resource instances in this page
- `page_number` - Current page number (0-indexed)
- `page_total` - Total number of pages
- `total` - Total number of resources across all pages

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L688)

Return JSON representation of the page.

#### \_\_getitem\_\_

```python
def __getitem__(key: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L694)

Allow dictionary-like access to page attributes.

### SearchResourceMixin Objects

```python
class SearchResourceMixin(BaseMixin, Generic[SearchParamsT, ResourceT])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L699)

Mixin for listing resources with pagination and search functionality.

**Attributes**:

- `PAGINATE_PATH` - str: The path for pagination.
- `PAGINATE_METHOD` - str: The method for pagination.
- `PAGINATE_ITEMS_KEY` - str: The key for the response.
- `PAGINATE_TOTAL_KEY` - str: The key for the total number of resources.
- `PAGINATE_PAGE_TOTAL_KEY` - str: The key for the total number of pages.
- `PAGINATE_DEFAULT_PAGE_NUMBER` - int: The default page number.
- `PAGINATE_DEFAULT_PAGE_SIZE` - int: The default page size.

#### PAGINATE\_ITEMS\_KEY

Default to match backend

#### search

```python
@classmethod
def search(cls: type, **kwargs: Unpack[SearchParamsT]) -> Page[ResourceT]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L777)

Search resources across the first n pages with optional filtering.

**Arguments**:

- `kwargs` - The keyword arguments.
  

**Returns**:

- `Page[ResourceT]` - Page of BaseResource instances

### GetResourceMixin Objects

```python
class GetResourceMixin(BaseMixin, Generic[GetParamsT, ResourceT])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L885)

Mixin for getting a resource.

#### get

```python
@classmethod
def get(cls: type,
        id: Any,
        host: Optional[str] = None,
        **kwargs: Unpack[GetParamsT]) -> ResourceT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L889)

Retrieve a single resource by its ID (or other get parameters).

**Arguments**:

- `id` - Any: The ID of the resource to get.
- `host` - str, optional: The host parameter to pass to the backend (default: None).
- `kwargs` - Get parameters to pass to the request.
  

**Returns**:

- `BaseResource` - Instance of the BaseResource class.
  

**Raises**:

- `ValueError` - If &#x27;RESOURCE_PATH&#x27; is not defined by the subclass.

### DeleteResourceMixin Objects

```python
class DeleteResourceMixin(BaseMixin, Generic[DeleteParamsT, DeleteResultT])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L930)

Mixin for deleting a resource.

#### DELETE\_RESPONSE\_CLASS

Default response class

#### build\_delete\_payload

```python
def build_delete_payload(**kwargs: Unpack[DeleteParamsT]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L935)

Build the payload for the delete action.

This method can be overridden by subclasses to provide custom payload
construction for delete operations.

#### build\_delete\_url

```python
def build_delete_url(**kwargs: Unpack[DeleteParamsT]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L944)

Build the URL for the delete action.

This method can be overridden by subclasses to provide custom URL
construction. The default implementation uses the resource path with
the resource ID.

**Returns**:

- `str` - The URL to use for the delete action

#### handle\_delete\_response

```python
def handle_delete_response(response: Any,
                           **kwargs: Unpack[DeleteParamsT]) -> DeleteResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L961)

Handle the response from a delete request.

This method can be overridden by subclasses to handle different
response patterns. The default implementation creates a simple
success response.

**Arguments**:

- `response` - The raw response from the API (may be Response object or dict)
- `**kwargs` - Delete parameters
  

**Returns**:

  DeleteResult instance from the configured response class

#### before\_delete

```python
def before_delete(*args: Any,
                  **kwargs: Unpack[DeleteParamsT]) -> Optional[DeleteResultT]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L998)

Optional callback called before the resource is deleted.

Override this method to add custom logic before deleting.

**Arguments**:

- `*args` - Positional arguments passed to the delete operation
- `**kwargs` - Keyword arguments passed to the delete operation
  

**Returns**:

- `Optional[DeleteResultT]` - If not None, this result will be returned early,
  bypassing the actual delete operation. If None, the
  delete operation will proceed normally.

#### after\_delete

```python
def after_delete(result: Union[DeleteResultT, Exception], *args: Any,
                 **kwargs: Unpack[DeleteParamsT]) -> Optional[DeleteResultT]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1014)

Optional callback called after the resource is deleted.

Override this method to add custom logic after deleting.

**Arguments**:

- `result` - The result from the delete operation (DeleteResultT on success,
  Exception on failure)
- `*args` - Positional arguments that were passed to the delete operation
- `**kwargs` - Keyword arguments that were passed to the delete operation
  

**Returns**:

- `Optional[DeleteResultT]` - If not None, this result will be returned instead
  of the original result. If None, the original result
  will be returned.

#### delete

```python
@with_hooks
def delete(*args: Any, **kwargs: Unpack[DeleteParamsT]) -> DeleteResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1038)

Delete a resource.

**Returns**:

- `DeleteResultT` - The result of the delete operation

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1055)

Mark the resource as deleted by clearing its ID and setting deletion flag.

### RunnableResourceMixin Objects

```python
class RunnableResourceMixin(BaseMixin, Generic[RunParamsT, ResultT])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1061)

Mixin for runnable resources.

#### RESPONSE\_CLASS

Default response class

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[RunParamsT]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1067)

Build the payload for the run action.

This method automatically handles dataclass serialization if the run
parameters are dataclasses with @dataclass_json decorator.

#### build\_run\_url

```python
def build_run_url(**kwargs: Unpack[RunParamsT]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1076)

Build the URL for the run action.

This method can be overridden by subclasses to provide custom URL
construction. The default implementation uses the resource path with
the run action.

**Returns**:

- `str` - The URL to use for the run action

#### handle\_run\_response

```python
def handle_run_response(response: dict,
                        **kwargs: Unpack[RunParamsT]) -> ResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1097)

Handle the response from a run request.

This method can be overridden by subclasses to handle different
response patterns. The default implementation assumes a polling URL
in the &#x27;data&#x27; field.

**Arguments**:

- `response` - The raw response from the API
- `**kwargs` - Run parameters
  

**Returns**:

  Response instance from the configured response class

#### before\_run

```python
def before_run(*args: Any, **kwargs: Unpack[RunParamsT]) -> Optional[ResultT]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1144)

Optional callback called before the resource is run.

Override this method to add custom logic before running.

**Arguments**:

- `*args` - Positional arguments passed to the run operation
- `**kwargs` - Keyword arguments passed to the run operation
  

**Returns**:

- `Optional[ResultT]` - If not None, this result will be returned early,
  bypassing the actual run operation. If None, the
  run operation will proceed normally.

#### after\_run

```python
def after_run(result: Union[ResultT, Exception], *args: Any,
              **kwargs: Unpack[RunParamsT]) -> Optional[ResultT]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1160)

Optional callback called after the resource is run.

Override this method to add custom logic after running.

**Arguments**:

- `result` - The result from the run operation (ResultT on success,
  Exception on failure)
- `*args` - Positional arguments that were passed to the run operation
- `**kwargs` - Keyword arguments that were passed to the run operation
  

**Returns**:

- `Optional[ResultT]` - If not None, this result will be returned instead
  of the original result. If None, the original result
  will be returned.

#### run

```python
@with_hooks
def run(*args: Any, **kwargs: Unpack[RunParamsT]) -> ResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1184)

Run the resource synchronously with automatic polling.

**Arguments**:

- `*args` - Positional arguments (converted to kwargs by subclasses)
- `**kwargs` - Run parameters including timeout and wait_time
  

**Returns**:

  Response instance from the configured response class

#### run\_async

```python
def run_async(**kwargs: Unpack[RunParamsT]) -> ResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1203)

Run the resource asynchronously.

**Arguments**:

- `**kwargs` - Run parameters specific to the resource type
  

**Returns**:

  Response instance from the configured RESPONSE_CLASS

#### poll

```python
def poll(poll_url: str) -> ResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1225)

Poll for the result of an asynchronous operation.

**Arguments**:

- `poll_url` - URL to poll for results
- `name` - Name/ID of the process
  

**Returns**:

  Response instance from the configured RESPONSE_CLASS
  

**Raises**:

- `APIError` - If the polling request fails
- `OperationFailedError` - If the operation has failed

#### on\_poll

```python
def on_poll(response: ResultT, **kwargs: Unpack[RunParamsT]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1274)

Hook called after each successful poll with the poll response.

Override this method in subclasses to handle poll responses,
such as displaying progress updates or logging status changes.

**Arguments**:

- `response` - The response from the poll operation
- `**kwargs` - Run parameters including show_progress, timeout, wait_time, etc.

#### sync\_poll

```python
def sync_poll(poll_url: str, **kwargs: Unpack[RunParamsT]) -> ResultT
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/resource.py#L1286)

Keeps polling until an asynchronous operation is complete.

**Arguments**:

- `poll_url` - URL to poll for results
- `name` - Name/ID of the process
- `**kwargs` - Run parameters including timeout, wait_time, and show_progress
  

**Returns**:

  Response instance from the configured RESPONSE_CLASS

