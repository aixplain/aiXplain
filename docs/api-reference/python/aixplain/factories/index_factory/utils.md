---
sidebar_label: utils
title: aixplain.factories.index_factory.utils
---

### BaseIndexParams Objects

```python
class BaseIndexParams(BaseModel, ABC)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L9)

Abstract base class for index parameters.

This class defines the common parameters and functionality for all index types.
It uses Pydantic for data validation and serialization.

**Attributes**:

- `model_config` _ConfigDict_ - Pydantic configuration using enum values.
- `name` _Text_ - Name of the index.
- `description` _Optional[Text]_ - Description of the index. Defaults to &quot;&quot;.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L25)

Convert the parameters to a dictionary format.

Converts the parameters to a dictionary suitable for API requests,
renaming &#x27;name&#x27; to &#x27;data&#x27; in the process.

**Returns**:

- `Dict` - Dictionary representation of the parameters.

#### id

```python
@property
@abstractmethod
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L40)

Abstract property that must be implemented in subclasses.

### BaseIndexParamsWithEmbeddingModel Objects

```python
class BaseIndexParamsWithEmbeddingModel(BaseIndexParams, ABC)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L45)

Abstract base class for index parameters that require an embedding model.

This class extends BaseIndexParams to add support for embedding model configuration,
including model selection and embedding size settings.

**Attributes**:

- `embedding_model` _Optional[Union[EmbeddingModel, str]]_ - Model to use for text
  embeddings. Defaults to EmbeddingModel.OPENAI_ADA002.
- `embedding_size` _Optional[int]_ - Size of the embeddings to generate.
  Defaults to None.

#### validate\_embedding\_model

```python
@field_validator("embedding_model")
def validate_embedding_model(cls, model_id) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L62)

Validate that the provided model is a text embedding model.

**Arguments**:

- `model_id` _Union[EmbeddingModel, str]_ - Model ID or enum value to validate.
  

**Returns**:

- `str` - The validated model ID.
  

**Raises**:

- `ValueError` - If the model is not a text embedding model.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L80)

Convert the parameters to a dictionary format.

Extends the base to_dict method to handle embedding-specific parameters,
renaming fields and restructuring as needed for the API.

**Returns**:

- `Dict` - Dictionary representation of the parameters with embedding
  configuration properly formatted.

### VectaraParams Objects

```python
class VectaraParams(BaseIndexParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L98)

Parameters for creating a Vectara index.

This class defines the configuration for Vectara&#x27;s vector search index.

**Attributes**:

- `_id` _ClassVar[str]_ - Static model ID for Vectara index type.

#### id

```python
@property
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L110)

Get the model ID for Vectara index type.

**Returns**:

- `str` - The Vectara model ID.

### ZeroEntropyParams Objects

```python
class ZeroEntropyParams(BaseIndexParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L119)

Parameters for creating a Zero Entropy index.

This class defines the configuration for Zero Entropy&#x27;s vector search index.

**Attributes**:

- `_id` _ClassVar[str]_ - Static model ID for Zero Entropy index type.

#### id

```python
@property
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L131)

Get the model ID for Zero Entropy index type.

**Returns**:

- `str` - The Zero Entropy model ID.

### AirParams Objects

```python
class AirParams(BaseIndexParamsWithEmbeddingModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L140)

Parameters for creating an AIR (aiXplain Index and Retrieval) index.

This class defines the configuration for AIR&#x27;s vector search index,
including embedding model settings.

**Attributes**:

- `_id` _ClassVar[str]_ - Static model ID for AIR index type.

#### id

```python
@property
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L153)

Get the model ID for AIR index type.

**Returns**:

- `str` - The AIR model ID.

### GraphRAGParams Objects

```python
class GraphRAGParams(BaseIndexParamsWithEmbeddingModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L162)

Parameters for creating a GraphRAG (Graph-based Retrieval-Augmented Generation) index.

This class defines the configuration for GraphRAG&#x27;s vector search index,
including embedding model and LLM settings.

**Attributes**:

- `_id` _ClassVar[str]_ - Static model ID for GraphRAG index type.
- `llm` _Optional[Text]_ - ID of the LLM to use for generation. Defaults to None.

#### id

```python
@property
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/index_factory/utils.py#L177)

Get the model ID for GraphRAG index type.

**Returns**:

- `str` - The GraphRAG model ID.

