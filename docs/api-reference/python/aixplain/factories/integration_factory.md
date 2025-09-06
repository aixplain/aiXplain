---
sidebar_label: integration_factory
title: aixplain.factories.integration_factory
---

### IntegrationFactory Objects

```python
class IntegrationFactory(ModelGetterMixin, ModelListMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/integration_factory.py#L11)

Factory class for creating and managing Integration models.

This class provides functionality to get and list Integration models using the backend API.
It inherits from ModelGetterMixin and ModelListMixin to provide model retrieval and listing capabilities.

**Attributes**:

- `backend_url` - The URL of the backend API endpoint.

#### get

```python
@classmethod
def get(cls,
        model_id: Text,
        api_key: Optional[Text] = None,
        use_cache: bool = False) -> Integration
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/integration_factory.py#L23)

Retrieves a specific Integration model by its ID.

**Arguments**:

- `model_id` _Text_ - The unique identifier of the Integration model.
- `api_key` _Optional[Text], optional_ - API key for authentication. Defaults to None.
- `use_cache` _bool, optional_ - Whether to use cached data. Defaults to False.
  

**Returns**:

- `Integration` - The retrieved Integration model.
  

**Raises**:

- `AssertionError` - If the provided ID does not correspond to an Integration model.

#### list

```python
@classmethod
def list(cls,
         query: Optional[Text] = "",
         suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
         ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
         sort_by: Optional[SortBy] = None,
         sort_order: SortOrder = SortOrder.ASCENDING,
         page_number: int = 0,
         page_size: int = 20,
         api_key: Optional[Text] = None) -> List[Integration]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/integration_factory.py#L42)

Lists Integration models based on the provided filters and pagination parameters.

**Arguments**:

- `query` _Optional[Text], optional_ - Search query string. Defaults to &quot;&quot;.
- `suppliers` _Optional[Union[Supplier, List[Supplier]]], optional_ - Filter by supplier(s). Defaults to None.
- `ownership` _Optional[Tuple[OwnershipType, List[OwnershipType]]], optional_ - Filter by ownership type. Defaults to None.
- `sort_by` _Optional[SortBy], optional_ - Field to sort results by. Defaults to None.
- `sort_order` _SortOrder, optional_ - Sort order (ascending/descending). Defaults to SortOrder.ASCENDING.
- `page_number` _int, optional_ - Page number for pagination. Defaults to 0.
- `page_size` _int, optional_ - Number of items per page. Defaults to 20.
- `api_key` _Optional[Text], optional_ - API key for authentication. Defaults to None.
  

**Returns**:

- `List[Integration]` - A list of Integration models matching the specified criteria.

