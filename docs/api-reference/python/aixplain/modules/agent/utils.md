---
sidebar_label: utils
title: aixplain.modules.agent.utils
---

#### process\_variables

```python
def process_variables(query: Union[Text, Dict], data: Union[Dict, Text],
                      parameters: Dict,
                      agent_description: Union[Text, None]) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/utils.py#L5)

Process variables in an agent&#x27;s description and input data.

This function validates and processes variables in an agent&#x27;s description and
input data, ensuring that all required variables are present and properly
formatted.

**Arguments**:

- `query` _Union[Text, Dict]_ - The input data provided to the agent.
- `data` _Union[Dict, Text]_ - The data to be processed.
- `parameters` _Dict_ - The parameters available to the agent.
- `agent_description` _Union[Text, None]_ - The description of the agent.
  

**Returns**:

- `Text` - The processed input data with all required variables included.
  

**Raises**:

- `AssertionError` - If a required variable is not found in the data or parameters.

#### validate\_history

```python
def validate_history(history)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/utils.py#L55)

Validates that `history` is a list of dicts, each with &#x27;role&#x27; and &#x27;content&#x27; keys.
Raises a ValueError if validation fails.

