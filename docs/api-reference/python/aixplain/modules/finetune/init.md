---
sidebar_label: finetune
title: aixplain.modules.finetune
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
    FineTune Class

### Finetune Objects

```python
class Finetune(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/__init__.py#L37)

A tool for fine-tuning machine learning models using custom datasets.

This class provides functionality to customize pre-trained models for specific tasks
by fine-tuning them on user-provided datasets. It handles the configuration of
training parameters, data splitting, and job execution.

**Attributes**:

- `name` _Text_ - Name of the fine-tuning job.
- `dataset_list` _List[Dataset]_ - List of datasets to use for fine-tuning.
- `model` _Model_ - The base model to be fine-tuned.
- `cost` _FinetuneCost_ - Cost information for the fine-tuning job.
- `id` _Text_ - ID of the fine-tuning job.
- `description` _Text_ - Detailed description of the fine-tuning purpose.
- `supplier` _Text_ - Provider/creator of the fine-tuned model.
- `version` _Text_ - Version identifier of the fine-tuning job.
- `train_percentage` _float_ - Percentage of data to use for training.
- `dev_percentage` _float_ - Percentage of data to use for validation.
- `dataset_list`0 _Text_ - Template for formatting training examples, using
  &lt;&lt;COLUMN_NAME&gt;&gt; to reference dataset columns.
- `dataset_list`1 _Hyperparameters_ - Configuration for the fine-tuning process.
- `dataset_list`2 _dict_ - Extra metadata for the fine-tuning job.
- `dataset_list`3 _str_ - URL endpoint for the backend API.
- `dataset_list`4 _str_ - Authentication key for API access.
- `dataset_list`5 _str_ - aiXplain-specific API key.

#### \_\_init\_\_

```python
def __init__(name: Text,
             dataset_list: List[Dataset],
             model: Model,
             cost: FinetuneCost,
             id: Optional[Text] = "",
             description: Optional[Text] = "",
             supplier: Optional[Text] = "aiXplain",
             version: Optional[Text] = "1.0",
             train_percentage: Optional[float] = 100,
             dev_percentage: Optional[float] = 0,
             prompt_template: Optional[Text] = None,
             hyperparameters: Optional[Hyperparameters] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/__init__.py#L64)

Initialize a new Finetune instance.

**Arguments**:

- `name` _Text_ - Name of the fine-tuning job.
- `dataset_list` _List[Dataset]_ - List of datasets to use for fine-tuning.
- `model` _Model_ - The base model to be fine-tuned.
- `cost` _FinetuneCost_ - Cost information for the fine-tuning job.
- `id` _Text, optional_ - ID of the job. Defaults to &quot;&quot;.
- `description` _Text, optional_ - Detailed description of the fine-tuning
  purpose. Defaults to &quot;&quot;.
- `supplier` _Text, optional_ - Provider/creator of the fine-tuned model.
  Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version identifier. Defaults to &quot;1.0&quot;.
- `train_percentage` _float, optional_ - Percentage of data to use for
  training. Defaults to 100.
- `dev_percentage` _float, optional_ - Percentage of data to use for
  validation. Defaults to 0.
- `dataset_list`0 _Text, optional_ - Template for formatting training
  examples. Use &lt;&lt;COLUMN_NAME&gt;&gt; to reference dataset columns.
  Defaults to None.
- `dataset_list`1 _Hyperparameters, optional_ - Configuration for the
  fine-tuning process. Defaults to None.
- `dataset_list`2 - Extra metadata for the fine-tuning job.

#### start

```python
def start() -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/__init__.py#L117)

Start the fine-tuning job on the backend.

This method submits the fine-tuning configuration to the backend and initiates
the training process. It handles the creation of the training payload,
including dataset splits and hyperparameters.

**Returns**:

- `Model` - The model object representing the fine-tuning job. Returns None
  if the job submission fails.
  

**Raises**:

- `Exception` - If there are errors in the API request or response handling.

