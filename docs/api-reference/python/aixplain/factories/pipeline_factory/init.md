---
sidebar_label: pipeline_factory
title: aixplain.factories.pipeline_factory
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
Date: September 1st 2022
Description:
    Pipeline Factory Class

### PipelineFactory Objects

```python
class PipelineFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L39)

Factory class for creating, managing, and exploring pipeline objects.

This class provides functionality for creating new pipelines, retrieving existing
pipelines, and managing pipeline configurations in the aiXplain platform.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, pipeline_id: Text, api_key: Optional[Text] = None) -> Pipeline
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L52)

Retrieve a pipeline by its ID.

This method fetches an existing pipeline from the aiXplain platform using
its unique identifier.

**Arguments**:

- `pipeline_id` _Text_ - Unique identifier of the pipeline to retrieve.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `Pipeline` - Retrieved pipeline object with its configuration and architecture.
  

**Raises**:

- `Exception` - If the pipeline cannot be retrieved, including cases where:
  - Pipeline ID is invalid
  - Network error occurs
  - Authentication fails

#### get\_assets\_from\_page

```python
@classmethod
def get_assets_from_page(cls, page_number: int) -> List[Pipeline]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L125)

Retrieve a paginated list of pipelines.

This method fetches a page of pipelines from the aiXplain platform.
Each page contains up to 10 pipelines.

**Arguments**:

- `page_number` _int_ - Zero-based page number to retrieve.
  

**Returns**:

- `List[Pipeline]` - List of pipeline objects on the specified page.
  Returns an empty list if an error occurs or no pipelines are found.
  

**Notes**:

  This method is primarily used internally by get_first_k_assets.
  For more control over pipeline listing, use the list method instead.

#### get\_first\_k\_assets

```python
@classmethod
def get_first_k_assets(cls, k: int) -> List[Pipeline]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L161)

Retrieve the first K pipelines from the platform.

This method fetches up to K pipelines by making multiple paginated requests
as needed (10 pipelines per page).

**Arguments**:

- `k` _int_ - Number of pipelines to retrieve. Must be positive.
  

**Returns**:

- `List[Pipeline]` - List of up to K pipeline objects.
  Returns an empty list if an error occurs.
  

**Notes**:

  For more control over pipeline listing, use the list method instead.
  This method is maintained for backwards compatibility.

#### list

```python
@classmethod
def list(cls,
         query: Optional[Text] = None,
         functions: Optional[Union[Function, List[Function]]] = None,
         suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
         models: Optional[Union[Model, List[Model]]] = None,
         input_data_types: Optional[Union[DataType, List[DataType]]] = None,
         output_data_types: Optional[Union[DataType, List[DataType]]] = None,
         page_number: int = 0,
         page_size: int = 20,
         drafts_only: bool = False) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L190)

List and filter pipelines with pagination support.

This method provides comprehensive filtering and pagination capabilities
for retrieving pipelines from the aiXplain platform.

**Arguments**:

- `query` _Optional[Text], optional_ - Search query to filter pipelines by name
  or description. Defaults to None.
- `functions` _Optional[Union[Function, List[Function]]], optional_ - Filter by
  function type(s). Defaults to None.
- `suppliers` _Optional[Union[Supplier, List[Supplier]]], optional_ - Filter by
  supplier(s). Defaults to None.
- `models` _Optional[Union[Model, List[Model]]], optional_ - Filter by specific
  model(s) used in pipelines. Defaults to None.
  input_data_types (Optional[Union[DataType, List[DataType]]], optional):
  Filter by input data type(s). Defaults to None.
  output_data_types (Optional[Union[DataType, List[DataType]]], optional):
  Filter by output data type(s). Defaults to None.
- `page_number` _int, optional_ - Zero-based page number. Defaults to 0.
- `page_size` _int, optional_ - Number of items per page (1-100).
  Defaults to 20.
- `drafts_only` _bool, optional_ - If True, only return draft pipelines.
  Defaults to False.
  

**Returns**:

- `Dict` - Response containing:
  - results (List[Pipeline]): List of pipeline objects
  - page_total (int): Total items in current page
  - page_number (int): Current page number
  - total (int): Total number of items across all pages
  

**Raises**:

- `Exception` - If the request fails or if page_size is invalid.
- `AssertionError` - If page_size is not between 1 and 100.

#### init

```python
@classmethod
def init(cls, name: Text, api_key: Optional[Text] = None) -> Pipeline
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L311)

Initialize a new empty pipeline.

This method creates a new pipeline instance with no nodes or links,
ready for configuration.

**Arguments**:

- `name` _Text_ - Name of the pipeline.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `Pipeline` - New pipeline instance with empty configuration.

#### create

```python
@classmethod
def create(cls,
           name: Text,
           pipeline: Union[Text, Dict],
           api_key: Optional[Text] = None) -> Pipeline
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/pipeline_factory/__init__.py#L337)

Create a new draft pipeline.

This method creates a new pipeline in draft status from a configuration
provided either as a Python dictionary or a JSON file.

**Arguments**:

- `name` _Text_ - Name of the pipeline.
- `pipeline` _Union[Text, Dict]_ - Pipeline configuration either as:
  - Dict: Python dictionary containing nodes and links
  - Text: Path to a JSON file containing the configuration
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `Pipeline` - Created pipeline instance in draft status.
  

**Raises**:

- `Exception` - If:
  - JSON file path is invalid
  - File extension is not .json
  - Pipeline creation request fails
  - Pipeline configuration is invalid
- `AssertionError` - If the pipeline file doesn&#x27;t exist or isn&#x27;t a JSON file.

