---
sidebar_label: index_factory
title: aixplain.factories.index_factory
---

#### \_\_author\_\_

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Abdul Basit Anees, Thiago Castro Ferreira, Zaina Abushaban
Date: December 26th 2024
Description:
    Index Factory Class

#### validate\_embedding\_model

```python
def validate_embedding_model(model_id: Union[EmbeddingModel, str]) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/__init__.py#L42)

Validate that a model is a text embedding model.

**Arguments**:

- `model_id` _Union[EmbeddingModel, str]_ - The model ID or EmbeddingModel enum
  value to validate.
  

**Returns**:

- `bool` - True if the model is a text embedding model, False otherwise.

### IndexFactory Objects

```python
class IndexFactory(ModelFactory, Generic[T])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/__init__.py#L56)

Factory class for creating and managing index collections.

This class extends ModelFactory to provide specialized functionality for
managing index collections, which are used for efficient data retrieval
and searching. It supports various index types through the generic
parameter T.

**Attributes**:

- `T` _TypeVar_ - Type variable bound to BaseIndexParams, representing
  the specific index parameters type.

#### create

```python
@classmethod
def create(cls,
           name: Optional[Text] = None,
           description: Optional[Text] = None,
           embedding_model: Union[EmbeddingModel,
                                  str] = EmbeddingModel.OPENAI_ADA002,
           params: Optional[T] = None,
           **kwargs) -> IndexModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/__init__.py#L70)

Create a new index collection for efficient data retrieval.

This method supports two ways of creating an index:
1. Using individual parameters (name, description, embedding_model) - Deprecated
2. Using a params object of type T (recommended)

**Arguments**:

- `name` _Optional[Text], optional_ - Name of the index collection.
  Deprecated, use params instead. Defaults to None.
- `description` _Optional[Text], optional_ - Description of the index collection.
  Deprecated, use params instead. Defaults to None.
- `embedding_model` _Union[EmbeddingModel, str], optional_ - Model to use for text embeddings.
  Deprecated, use params instead. Defaults to EmbeddingModel.OPENAI_ADA002.
- `params` _Optional[T], optional_ - Index parameters object. This is the
  recommended way to create an index. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `IndexModel` - Created index collection model.
  

**Raises**:

- `AssertionError` - If neither params nor all legacy parameters are provided,
  or if both params and legacy parameters are provided.
- `Exception` - If index creation fails.

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
         page_size: int = 20) -> List[IndexModel]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/__init__.py#L142)

List available index collections with optional filtering and sorting.

**Arguments**:

- `query` _Optional[Text], optional_ - Search query to filter indexes.
  Defaults to &quot;&quot;.
- `suppliers` _Optional[Union[Supplier, List[Supplier]]], optional_ - Filter by
  supplier(s). Defaults to None.
  ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
  Filter by ownership type. Defaults to None.
- `sort_by` _Optional[SortBy], optional_ - Field to sort results by.
  Defaults to None.
- `sort_order` _SortOrder, optional_ - Sort direction (ascending/descending).
  Defaults to SortOrder.ASCENDING.
- `page_number` _int, optional_ - Page number for pagination. Defaults to 0.
- `page_size` _int, optional_ - Number of results per page. Defaults to 20.
  

**Returns**:

- `List[IndexModel]` - List of index models matching the specified criteria.

