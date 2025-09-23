---
sidebar_label: dataset_factory
title: aixplain.factories.dataset_factory
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
Date: December 1st 2022
Description:
    Dataset Factory Class

### DatasetFactory Objects

```python
class DatasetFactory(AssetFactory)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/dataset_factory.py#L54)

Factory class for creating and managing datasets in the aiXplain platform.

This class provides functionality for creating, retrieving, and managing
datasets, which are structured collections of data assets used for training,
evaluating, and benchmarking AI models. Datasets can include input data,
target data, hypotheses, and metadata.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, dataset_id: Text) -> Dataset
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/dataset_factory.py#L177)

Retrieve a dataset by its ID.

This method fetches a dataset and all its associated data assets from
the platform.

**Arguments**:

- `dataset_id` _Text_ - Unique identifier of the dataset to retrieve.
  

**Returns**:

- `Dataset` - Retrieved dataset object with all components loaded.
  

**Raises**:

- `Exception` - If:
  - Dataset ID is invalid
  - Authentication fails
  - Service is unavailable

#### list

```python
@classmethod
def list(cls,
         query: Optional[Text] = None,
         function: Optional[Function] = None,
         source_languages: Optional[Union[Language, List[Language]]] = None,
         target_languages: Optional[Union[Language, List[Language]]] = None,
         data_type: Optional[DataType] = None,
         license: Optional[License] = None,
         is_referenceless: Optional[bool] = None,
         page_number: int = 0,
         page_size: int = 20) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/dataset_factory.py#L216)

List and filter datasets with pagination support.

This method provides comprehensive filtering and pagination capabilities
for retrieving datasets from the aiXplain platform.

**Arguments**:

- `query` _Optional[Text], optional_ - Search query to filter datasets by name
  or description. Defaults to None.
- `function` _Optional[Function], optional_ - Filter by AI function type.
  Defaults to None.
  source_languages (Optional[Union[Language, List[Language]]], optional):
  Filter by input data language(s). Can be single language or list.
  Defaults to None.
  target_languages (Optional[Union[Language, List[Language]]], optional):
  Filter by output data language(s). Can be single language or list.
  Defaults to None.
- `data_type` _Optional[DataType], optional_ - Filter by data type.
  Defaults to None.
- `license` _Optional[License], optional_ - Filter by license type.
  Defaults to None.
- `is_referenceless` _Optional[bool], optional_ - Filter by whether dataset
  has references. Defaults to None.
- `page_number` _int, optional_ - Zero-based page number. Defaults to 0.
- `page_size` _int, optional_ - Number of items per page (1-100).
  Defaults to 20.
  

**Returns**:

- `Dict` - Response containing:
  - results (List[Dataset]): List of dataset objects
  - page_total (int): Total items in current page
  - page_number (int): Current page number
  - total (int): Total number of items across all pages
  

**Raises**:

- `Exception` - If:
  - page_size is not between 1 and 100
  - Request fails
  - Service is unavailable
- `AssertionError` - If page_size is invalid.

#### create

```python
@classmethod
def create(cls,
           name: Text,
           description: Text,
           license: License,
           function: Function,
           input_schema: List[Union[Dict, MetaData]],
           output_schema: List[Union[Dict, MetaData]] = [],
           hypotheses_schema: List[Union[Dict, MetaData]] = [],
           metadata_schema: List[Union[Dict, MetaData]] = [],
           content_path: Union[Union[Text, Path], List[Union[Text,
                                                             Path]]] = [],
           input_ref_data: Dict[Text, Any] = {},
           output_ref_data: Dict[Text, List[Any]] = {},
           hypotheses_ref_data: Dict[Text, Any] = {},
           meta_ref_data: Dict[Text, Any] = {},
           tags: List[Text] = [],
           privacy: Privacy = Privacy.PRIVATE,
           split_labels: Optional[List[Text]] = None,
           split_rate: Optional[List[float]] = None,
           error_handler: ErrorHandler = ErrorHandler.SKIP,
           s3_link: Optional[Text] = None,
           aws_credentials: Optional[Dict[Text, Text]] = {
               "AWS_ACCESS_KEY_ID": None,
               "AWS_SECRET_ACCESS_KEY": None
           },
           api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/dataset_factory.py#L331)

Create a new dataset from data files and references.

This method processes data files and existing data assets to create a new
dataset in the platform. It supports various data types, multiple input and
output configurations, and optional data splitting.

**Arguments**:

- `name` _Text_ - Name for the new dataset.
- `description` _Text_ - Description of the dataset&#x27;s contents and purpose.
- `license` _License_ - License type for the dataset.
- `function` _Function_ - AI function this dataset is suitable for.
- `input_schema` _List[Union[Dict, MetaData]]_ - Metadata configurations for
  input data processing.
- `output_schema` _List[Union[Dict, MetaData]], optional_ - Metadata configs
  for output/target data. Defaults to [].
- `hypotheses_schema` _List[Union[Dict, MetaData]], optional_ - Metadata
  configs for hypothesis data. Defaults to [].
- `metadata_schema` _List[Union[Dict, MetaData]], optional_ - Additional
  metadata configurations. Defaults to [].
  content_path (Union[Union[Text, Path], List[Union[Text, Path]]], optional):
  Path(s) to data files. Can be single path or list. Defaults to [].
- `input_ref_data` _Dict[Text, Any], optional_ - References to existing
  input data assets. Defaults to \{}.
- `output_ref_data` _Dict[Text, List[Any]], optional_ - References to
  existing output data assets. Defaults to \{}.
- `description`0 _Dict[Text, Any], optional_ - References to
  existing hypothesis data. Defaults to \{}.
- `description`1 _Dict[Text, Any], optional_ - References to existing
  metadata assets. Defaults to \{}.
- `description`2 _List[Text], optional_ - Tags describing the dataset.
  Defaults to [].
- `description`3 _Privacy, optional_ - Visibility setting.
  Defaults to Privacy.PRIVATE.
- `description`4 _Optional[List[Text]], optional_ - Labels for dataset
  splits (e.g., [&quot;train&quot;, &quot;test&quot;]). Defaults to None.
- `description`5 _Optional[List[float]], optional_ - Ratios for dataset
  splits (must sum to 1). Defaults to None.
- `description`6 _ErrorHandler, optional_ - Strategy for handling data
  processing errors. Defaults to ErrorHandler.SKIP.
- `description`7 _Optional[Text], optional_ - S3 URL for data files.
  Defaults to None.
- `description`8 _Optional[Dict[Text, Text]], optional_ - AWS credentials
  with access_key_id and secret_access_key. Defaults to None values.
- `description`9 _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `license`0 - Response containing:
  - status: Current processing status
  - asset_id: ID of the created dataset
  

**Raises**:

- `license`1 - If:
  - No input data is provided
  - Referenced data asset doesn&#x27;t exist
  - Reserved column names are used
  - Data rows are misaligned
  - Split configuration is invalid
  - Processing or upload fails
- `license`2 - If split configuration is invalid.

