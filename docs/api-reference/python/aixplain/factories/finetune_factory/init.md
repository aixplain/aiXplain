---
sidebar_label: finetune_factory
title: aixplain.factories.finetune_factory
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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: June 14th 2023
Description:
    Finetune Factory Class

### FinetuneFactory Objects

```python
class FinetuneFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/finetune_factory/__init__.py#L40)

Factory class for creating and managing model fine-tuning operations.

This class provides static methods to create and manage fine-tuning jobs
for machine learning models. It handles cost estimation, dataset preparation,
and fine-tuning configuration.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### create

```python
@classmethod
def create(cls,
           name: Text,
           dataset_list: List[Union[Dataset, Text]],
           model: Union[Model, Text],
           prompt_template: Optional[Text] = None,
           hyperparameters: Optional[Hyperparameters] = None,
           train_percentage: Optional[float] = 100,
           dev_percentage: Optional[float] = 0) -> Finetune
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/finetune_factory/__init__.py#L68)

Create a new fine-tuning job with the specified configuration.

This method sets up a fine-tuning job by validating the configuration,
estimating costs, and preparing the datasets and model. It supports both
direct Dataset/Model objects and their IDs as inputs.

**Arguments**:

- `name` _Text_ - Name for the fine-tuning job.
- `dataset_list` _List[Union[Dataset, Text]]_ - List of Dataset objects or dataset IDs
  to use for fine-tuning.
- `model` _Union[Model, Text]_ - Model object or model ID to be fine-tuned.
- `prompt_template` _Text, optional_ - Template for formatting training examples.
  Use &lt;&lt;COLUMN_NAME&gt;&gt; to reference dataset columns. Defaults to None.
- `hyperparameters` _Hyperparameters, optional_ - Fine-tuning hyperparameters
  configuration. Defaults to None.
- `train_percentage` _float, optional_ - Percentage of data to use for training.
  Must be &gt; 0. Defaults to 100.
- `dev_percentage` _float, optional_ - Percentage of data to use for validation.
  train_percentage + dev_percentage must be &lt;= 100. Defaults to 0.
  

**Returns**:

- `Finetune` - Configured fine-tuning job object, or None if creation failed.
  

**Raises**:

- `AssertionError` - If train_percentage &lt;= 0 or train_percentage + dev_percentage &gt; 100.

