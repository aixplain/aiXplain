---
sidebar_label: corpus
title: aixplain.modules.corpus
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
Date: February 1st 2023
Description:
    Corpus Class

### Corpus Objects

```python
class Corpus(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/corpus.py#L37)

A class representing a general-purpose collection of data in the aiXplain platform.

This class extends Asset to provide functionality for managing corpora, which are
collections of data that can be processed and used to create task-specific datasets.
A corpus can contain various types of data and is used as a foundation for creating
specialized datasets.

**Attributes**:

- `id` _Text_ - ID of the corpus.
- `name` _Text_ - Name of the corpus.
- `description` _Text_ - Detailed description of the corpus.
- `data` _List[Data]_ - List of data objects that make up the corpus.
- `onboard_status` _OnboardStatus_ - Current onboarding status of the corpus.
- `functions` _List[Function]_ - AI functions the corpus is suitable for.
- `tags` _List[Text]_ - Descriptive tags for the corpus.
- `license` _Optional[License]_ - License associated with the corpus.
- `privacy` _Privacy_ - Privacy settings for the corpus.
- `supplier` _Text_ - The supplier/author of the corpus.
- `name`0 _Text_ - Version of the corpus.
- `name`1 _Optional[int]_ - Number of rows/items in the corpus.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text,
             data: List[Data],
             onboard_status: OnboardStatus,
             functions: List[Function] = [],
             tags: List[Text] = [],
             license: Optional[License] = None,
             privacy: Privacy = Privacy.PRIVATE,
             supplier: Text = "aiXplain",
             version: Text = "1.0",
             length: Optional[int] = None,
             **kwargs) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/corpus.py#L60)

Corpus Class.

Description:
Corpus is general-purpose collection of data that can be processed and used to create task-specific datasets.

**Arguments**:

- `id` _Text_ - Corpus ID
- `name` _Text_ - Corpus Name
- `description` _Text_ - description of the corpus
- `data` _List[Data]_ - List of data which the corpus consists of
- `onboard_status` _OnboardStatus_ - onboard status
- `functions` _List[Function], optional_ - AI functions in which the corpus is suggested to be used to. Defaults to [].
- `tags` _List[Text], optional_ - description tags. Defaults to [].
- `license` _Optional[License], optional_ - Corpus license. Defaults to None.
- `privacy` _Privacy, optional_ - Corpus privacy info. Defaults to Privacy.PRIVATE.
- `supplier` _Text, optional_ - Corpus supplier. Defaults to &quot;aiXplain&quot;.
- `name`0 _Text, optional_ - Corpus version. Defaults to &quot;1.0&quot;.
- `name`1 _Optional[int], optional_ - Number of rows in the Corpus. Defaults to None.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/corpus.py#L107)

Return a string representation of the Corpus instance.

**Returns**:

- `str` - A string in the format &quot;&lt;Corpus: name&gt;&quot;.

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/corpus.py#L115)

Delete this corpus from the aiXplain platform.

This method permanently removes the corpus from the platform. The operation
can only be performed by the corpus owner.

**Returns**:

  None
  

**Raises**:

- `Exception` - If the deletion fails, either because:
  - The corpus doesn&#x27;t exist
  - The user is not the owner
  - There&#x27;s a network/server error

