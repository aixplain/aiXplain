---
sidebar_label: llm_utils
title: aixplain.utils.llm_utils
---

#### get\_llm\_instance

```python
def get_llm_instance(llm_id: Text,
                     api_key: Optional[Text] = None,
                     use_cache: bool = True) -> LLM
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/llm_utils.py#L6)

Get an LLM instance with specific configuration.

**Arguments**:

- `llm_id` _Text_ - ID of the LLM model to use.
- `api_key` _Optional[Text], optional_ - API key to use. Defaults to None.
- `use_cache` _bool, optional_ - Whether to use caching for model retrieval. Defaults to True.
  

**Returns**:

- `LLM` - Configured LLM instance.
  

**Raises**:

- `Exception` - If the LLM model with the given ID is not found.

