---
sidebar_label: evolve_utils
title: aixplain.utils.evolve_utils
---

#### create\_llm\_dict

```python
def create_llm_dict(
        llm: Optional[Union[Text, LLM]]) -> Optional[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/evolve_utils.py#L5)

Create a dictionary representation of an LLM for evolution parameters.

**Arguments**:

- `llm` - Either an LLM ID string or an LLM object instance.
  

**Returns**:

  Dictionary with LLM information if llm is provided, None otherwise.

