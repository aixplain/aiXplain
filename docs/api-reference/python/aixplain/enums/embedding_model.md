---
sidebar_label: embedding_model
title: aixplain.enums.embedding_model
---

#### \_\_author\_\_

Copyright 2023 The aiXplain SDK authors
Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Author: aiXplain team
Date: February 17th 2025
Description:
    Embedding Model Enum

### EmbeddingModel Objects

```python
class EmbeddingModel(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/embedding_model.py#L23)

Enumeration of available embedding models in the aiXplain system.

This enum defines the unique identifiers for different embedding models that can
be used to generate vector representations of data.

**Attributes**:

- `OPENAI_ADA002` _str_ - OpenAI&#x27;s Ada-002 text embedding model ID.
- `JINA_CLIP_V2_MULTIMODAL` _str_ - Jina CLIP v2 multimodal embedding model ID.
- `MULTILINGUAL_E5_LARGE` _str_ - Multilingual E5 Large text embedding model ID.
- `BGE_M3` _str_ - BGE-M3 embedding model ID.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/embedding_model.py#L40)

Return the string representation of the embedding model ID.

**Returns**:

- `str` - The model ID value as a string.

