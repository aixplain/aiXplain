---
sidebar_label: dataset
title: aixplain.modules.dataset
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
Date: October 28th 2022
Description:
    Datasets Class

### Dataset Objects

```python
class Dataset(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/dataset.py#L38)

Dataset is a collection of data intended to be used for a specific function.
Different from corpus, a dataset is a representative sample of a specific phenomenon to a specific AI task.
aiXplain also counts with an extensive collection of datasets for training, infer and benchmark various tasks like
Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.

**Attributes**:

- `id` _Text_ - Dataset ID
- `name` _Text_ - Dataset Name
- `description` _Text_ - Dataset description
- `function` _Function_ - Function for which the dataset is intented to
- `source_data` _Dict[Any, Data]_ - List of input Data to the function
- `target_data` _Dict[Any, List[Data]]_ - List of Multi-reference Data which is expected to be outputted by the function
- `onboard_status` _OnboardStatus_ - onboard status
- `hypotheses` _Dict[Any, Data], optional_ - dataset&#x27;s hypotheses, i.e. model outputs based on the source data. Defaults to \{}.
- `metadata` _Dict[Any, Data], optional_ - dataset&#x27;s metadata. Defaults to \{}.
- `tags` _List[Text], optional_ - tags that describe the dataset. Defaults to [].
- `name`0 _Optional[License], optional_ - Dataset License. Defaults to None.
- `name`1 _Privacy, optional_ - Dataset Privacy. Defaults to Privacy.PRIVATE.
- `name`2 _Text, optional_ - Dataset Supplier. Defaults to &quot;aiXplain&quot;.
- `name`3 _Text, optional_ - Dataset Version. Defaults to &quot;1.0&quot;.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text,
             function: Function,
             source_data: Dict[Any, Data],
             target_data: Dict[Any, List[Data]],
             onboard_status: OnboardStatus,
             hypotheses: Dict[Any, Data] = {},
             metadata: Dict[Any, Data] = {},
             tags: List[Text] = [],
             license: Optional[License] = None,
             privacy: Privacy = Privacy.PRIVATE,
             supplier: Text = "aiXplain",
             version: Text = "1.0",
             length: Optional[int] = None,
             **kwargs) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/dataset.py#L61)

Dataset Class.

Description:
Dataset is a collection of data intended to be used for a specific function.
Different from corpus, a dataset is a representative sample of a specific phenomenon to a specific AI task.
aiXplain also counts with an extensive collection of datasets for training, infer and benchmark various tasks like
Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.

**Arguments**:

- `id` _Text_ - Dataset ID
- `name` _Text_ - Dataset Name
- `description` _Text_ - Dataset description
- `function` _Function_ - Function for which the dataset is intented to
- `source_data` _Dict[Any, Data]_ - List of input Data to the function
- `target_data` _Dict[Any, List[Data]]_ - List of Multi-reference Data which is expected to be outputted by the function
- `onboard_status` _OnboardStatus_ - onboard status
- `hypotheses` _Dict[Any, Data], optional_ - dataset&#x27;s hypotheses, i.e. model outputs based on the source data. Defaults to \{}.
- `metadata` _Dict[Any, Data], optional_ - dataset&#x27;s metadata. Defaults to \{}.
- `tags` _List[Text], optional_ - tags that describe the dataset. Defaults to [].
- `name`0 _Optional[License], optional_ - Dataset License. Defaults to None.
- `name`1 _Privacy, optional_ - Dataset Privacy. Defaults to Privacy.PRIVATE.
- `name`2 _Text, optional_ - Dataset Supplier. Defaults to &quot;aiXplain&quot;.
- `name`3 _Text, optional_ - Dataset Version. Defaults to &quot;1.0&quot;.
- `name`4 _Optional[int], optional_ - Number of rows in the Dataset. Defaults to None.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/dataset.py#L120)

Return a string representation of the Dataset instance.

**Returns**:

- `str` - A string in the format &quot;&lt;Dataset: name&gt;&quot;.

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/dataset.py#L128)

Delete this dataset from the aiXplain platform.

This method permanently removes the dataset from the platform. The operation
can only be performed by the dataset owner.

**Returns**:

  None
  

**Raises**:

- `Exception` - If the deletion fails, either because:
  - The dataset doesn&#x27;t exist
  - The user is not the owner
  - There&#x27;s a network/server error

