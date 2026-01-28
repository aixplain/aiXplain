---
sidebar_label: prompt_validator
title: aixplain.factories.finetune_factory.prompt_validator
---

#### validate\_prompt

```python
def validate_prompt(prompt: Text, dataset_list: List[Dataset]) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/finetune_factory/prompt_validator.py#L23)

Validate and normalize a prompt template against a list of datasets.

This function processes a prompt template that contains references to dataset
columns in the format &lt;&lt;COLUMN_NAME&gt;&gt; or &lt;&lt;COLUMN_ID&gt;&gt;. It validates that all
referenced columns exist in the provided datasets and normalizes column IDs
to their corresponding names.

**Arguments**:

- `prompt` _Text_ - Prompt template containing column references in
  &lt;&lt;COLUMN_NAME&gt;&gt; or &lt;&lt;COLUMN_ID&gt;&gt; format.
- `dataset_list` _List[Dataset]_ - List of datasets to validate the
  prompt template against.
  

**Returns**:

- `Text` - Normalized prompt template with column references converted
  to \{COLUMN_NAME} format.
  

**Raises**:

- `AssertionError` - If any of these conditions are met:
  - Multiple datasets have the same referenced column name
  - Referenced columns are not found in any dataset

