---
sidebar_label: convert_datatype_utils
title: aixplain.utils.convert_datatype_utils
---

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

#### dict\_to\_metadata

```python
def dict_to_metadata(metadatas: List[Union[Dict, MetaData]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/convert_datatype_utils.py#L22)

Convert all the Dicts to MetaData

**Arguments**:

- `metadatas` _List[Union[Dict, MetaData]], optional_ - metadata of metadata information of the dataset.
  

**Returns**:

  None
  

**Raises**:

- `TypeError` - If one or more elements in the metadata_schema are not well-structured

