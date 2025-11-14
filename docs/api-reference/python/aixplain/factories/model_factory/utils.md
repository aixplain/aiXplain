---
sidebar_label: utils
title: aixplain.factories.model_factory.utils
---

#### create\_model\_from\_response

```python
def create_model_from_response(response: Dict) -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/utils.py#L20)

Convert API response JSON into appropriate Model object.

This function creates the correct type of Model object (Model, LLM, IndexModel,
Integration, ConnectionTool, MCPConnection, or UtilityModel) based on the
function type and parameters in the response.

**Arguments**:

- `response` _Dict_ - API response containing model information including:
  - id: Model identifier
  - name: Model name
  - function: Function type information
  - params: Model parameters
  - api_key: Optional API key
  - attributes: Optional model attributes
  - code: Optional model code
  - version: Optional version information
  

**Returns**:

- `Model` - Instantiated model object of the appropriate subclass based on
  the function type.
  

**Raises**:

- `Exception` - If required code is not found for UtilityModel.

#### get\_assets\_from\_page

```python
def get_assets_from_page(query,
                         page_number: int,
                         page_size: int,
                         function: Function,
                         suppliers: Union[Supplier, List[Supplier]],
                         source_languages: Union[Language, List[Language]],
                         target_languages: Union[Language, List[Language]],
                         is_finetunable: bool = None,
                         ownership: Optional[Tuple[
                             OwnershipType, List[OwnershipType]]] = None,
                         sort_by: Optional[SortBy] = None,
                         sort_order: SortOrder = SortOrder.ASCENDING,
                         api_key: Optional[str] = None) -> List[Model]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/utils.py#L149)

Retrieve a paginated list of models with specified filters.

This function fetches a page of models from the aiXplain platform, applying
various filters such as function type, suppliers, languages, and ownership.

**Arguments**:

- `query` - Search query string to filter models.
- `page_number` _int_ - Page number to retrieve (0-based).
- `page_size` _int_ - Number of models per page.
- `function` _Function_ - Function type to filter models by.
- `suppliers` _Union[Supplier, List[Supplier]]_ - Single supplier or list of
  suppliers to filter models by.
- `source_languages` _Union[Language, List[Language]]_ - Source language(s)
  supported by the models.
- `target_languages` _Union[Language, List[Language]]_ - Target language(s)
  for translation models.
- `is_finetunable` _bool, optional_ - Filter for fine-tunable models.
  Defaults to None.
  ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
  Filter by model ownership type. Defaults to None.
- `sort_by` _Optional[SortBy], optional_ - Field to sort results by.
  Defaults to None.
- `sort_order` _SortOrder, optional_ - Sort direction (ascending/descending).
  Defaults to SortOrder.ASCENDING.
- `page_number`0 _Optional[str], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

  Tuple[List[Model], int]: A tuple containing:
  - List of Model objects matching the filters
  - Total number of models matching the filters
  

**Raises**:

- `page_number`1 - If the API request fails or returns an error.

#### get\_model\_from\_ids

```python
def get_model_from_ids(model_ids: List[str],
                       api_key: Optional[str] = None) -> List[Model]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/utils.py#L262)

Retrieve multiple models by their IDs.

This function fetches multiple models from the aiXplain platform in a single
request using their unique identifiers.

**Arguments**:

- `model_ids` _List[str]_ - List of model IDs to retrieve.
- `api_key` _Optional[str], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `List[Model]` - List of Model objects corresponding to the provided IDs.
  Each model will be instantiated as the appropriate subclass based
  on its function type.
  

**Raises**:

- `Exception` - If the API request fails or returns an error, including
  cases where models are not found or access is denied.

