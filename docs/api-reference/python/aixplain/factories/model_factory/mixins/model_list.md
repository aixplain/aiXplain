---
sidebar_label: model_list
title: aixplain.factories.model_factory.mixins.model_list
---

### ModelListMixin Objects

```python
class ModelListMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_list.py#L7)

Mixin class providing model listing functionality.

This mixin provides methods for retrieving lists of models with various
filtering and sorting options.

#### list

```python
@classmethod
def list(cls,
         query: Optional[Text] = "",
         function: Optional[Function] = None,
         suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
         source_languages: Optional[Union[Language, List[Language]]] = None,
         target_languages: Optional[Union[Language, List[Language]]] = None,
         is_finetunable: Optional[bool] = None,
         ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
         sort_by: Optional[SortBy] = None,
         sort_order: SortOrder = SortOrder.ASCENDING,
         page_number: int = 0,
         page_size: int = 20,
         model_ids: Optional[List[Text]] = None,
         api_key: Optional[Text] = None) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_list.py#L14)

List and filter available models with pagination support.

This method provides comprehensive filtering capabilities for retrieving
models. It supports two modes:
1. Filtering by model IDs (exclusive of other filters)
2. Filtering by various criteria (function, language, etc.)

**Arguments**:

- `query` _Optional[Text], optional_ - Search query to filter models.
  Defaults to &quot;&quot;.
- `function` _Optional[Function], optional_ - Filter by model function/task.
  Defaults to None.
- `suppliers` _Optional[Union[Supplier, List[Supplier]]], optional_ - Filter by
  supplier(s). Defaults to None.
  source_languages (Optional[Union[Language, List[Language]]], optional):
  Filter by input language(s). Defaults to None.
  target_languages (Optional[Union[Language, List[Language]]], optional):
  Filter by output language(s). Defaults to None.
- `is_finetunable` _Optional[bool], optional_ - Filter by fine-tuning capability.
  Defaults to None.
  ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
  Filter by ownership type (e.g., SUBSCRIBED, OWNER). Defaults to None.
- `sort_by` _Optional[SortBy], optional_ - Attribute to sort results by.
  Defaults to None.
- `sort_order` _SortOrder, optional_ - Sort direction (ascending/descending).
  Defaults to SortOrder.ASCENDING.
- `page_number` _int, optional_ - Page number for pagination. Defaults to 0.
- `page_size` _int, optional_ - Number of results per page. Defaults to 20.
- `model_ids` _Optional[List[Text]], optional_ - List of specific model IDs to retrieve.
  If provided, other filters are ignored. Defaults to None.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `function`0 - Dictionary containing:
  - results (List[Model]): List of models matching the criteria
  - page_total (int): Number of models in current page
  - page_number (int): Current page number
  - total (int): Total number of models matching the criteria
  

**Raises**:

- `function`1 - If model_ids is provided with other filters, or if
  page_size is less than the number of requested model_ids.

