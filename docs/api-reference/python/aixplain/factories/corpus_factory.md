---
sidebar_label: corpus_factory
title: aixplain.factories.corpus_factory
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
Date: March 27th 2023
Description:
    Corpus Factory Class

### CorpusFactory Objects

```python
class CorpusFactory(AssetFactory)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/corpus_factory.py#L50)

Factory class for creating and managing corpora in the aiXplain platform.

This class provides functionality for creating, retrieving, and managing
corpora, which are collections of data assets used for training and
evaluating AI models.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, corpus_id: Text) -> Corpus
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/corpus_factory.py#L128)

Retrieve a corpus by its ID.

This method fetches a corpus and all its associated data assets from
the platform.

**Arguments**:

- `corpus_id` _Text_ - Unique identifier of the corpus to retrieve.
  

**Returns**:

- `Corpus` - Retrieved corpus object with all data assets loaded.
  

**Raises**:

- `Exception` - If:
  - Corpus ID is invalid
  - Authentication fails
  - Service is unavailable

#### list

```python
@classmethod
def list(cls,
         query: Optional[Text] = None,
         function: Optional[Function] = None,
         language: Optional[Union[Language, List[Language]]] = None,
         data_type: Optional[DataType] = None,
         license: Optional[License] = None,
         page_number: int = 0,
         page_size: int = 20) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/corpus_factory.py#L176)

List and filter corpora with pagination support.

This method provides comprehensive filtering and pagination capabilities
for retrieving corpora from the aiXplain platform.

**Arguments**:

- `query` _Optional[Text], optional_ - Search query to filter corpora by name
  or description. Defaults to None.
- `function` _Optional[Function], optional_ - Filter by AI function type.
  Defaults to None.
- `language` _Optional[Union[Language, List[Language]]], optional_ - Filter by
  language(s). Can be single language or list. Defaults to None.
- `data_type` _Optional[DataType], optional_ - Filter by data type.
  Defaults to None.
- `license` _Optional[License], optional_ - Filter by license type.
  Defaults to None.
- `page_number` _int, optional_ - Zero-based page number. Defaults to 0.
- `page_size` _int, optional_ - Number of items per page (1-100).
  Defaults to 20.
  

**Returns**:

- `Dict` - Response containing:
  - results (List[Corpus]): List of corpus objects
  - page_total (int): Total items in current page
  - page_number (int): Current page number
  - total (int): Total number of items across all pages
  

**Raises**:

- `Exception` - If:
  - page_size is not between 1 and 100
  - Request fails
  - Service is unavailable
- `AssertionError` - If page_size is invalid.

#### get\_assets\_from\_page

```python
@classmethod
def get_assets_from_page(cls,
                         page_number: int = 1,
                         task: Optional[Function] = None,
                         language: Optional[Text] = None) -> List[Corpus]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/corpus_factory.py#L278)

Retrieve a paginated list of corpora with optional filters.

**Notes**:

  This method is deprecated. Use list() instead.
  

**Arguments**:

- `page_number` _int, optional_ - One-based page number. Defaults to 1.
- `task` _Optional[Function], optional_ - Filter by AI task/function.
  Defaults to None.
- `language` _Optional[Text], optional_ - Filter by language code.
  Defaults to None.
  

**Returns**:

- `List[Corpus]` - List of corpus objects matching the filters.
  
  Deprecated:
  Use list() method instead for more comprehensive filtering and
  pagination capabilities.

#### create

```python
@classmethod
def create(cls,
           name: Text,
           description: Text,
           license: License,
           content_path: Union[Union[Text, Path], List[Union[Text, Path]]],
           schema: List[Union[Dict, MetaData]],
           ref_data: List[Any] = [],
           tags: List[Text] = [],
           functions: List[Function] = [],
           privacy: Privacy = Privacy.PRIVATE,
           error_handler: ErrorHandler = ErrorHandler.SKIP,
           api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/corpus_factory.py#L310)

Create a new corpus from data files.

This method asynchronously uploads and processes data files to create a new
corpus in the user&#x27;s dashboard. The data files are processed according to
the provided schema and combined with any referenced existing data.

**Arguments**:

- `name` _Text_ - Name for the new corpus.
- `description` _Text_ - Description of the corpus&#x27;s contents and purpose.
- `license` _License_ - License type for the corpus.
- `content_path` _Union[Union[Text, Path], List[Union[Text, Path]]]_ - Path(s)
  to CSV files containing the data. Can be single path or list.
- `schema` _List[Union[Dict, MetaData]]_ - Metadata configurations defining
  how to process the data files.
- `ref_data` _List[Any], optional_ - References to existing data assets to
  include in the corpus. Can be Data objects or IDs. Defaults to [].
- `tags` _List[Text], optional_ - Tags describing the corpus content.
  Defaults to [].
- `functions` _List[Function], optional_ - AI functions this corpus is
  suitable for. Defaults to [].
- `privacy` _Privacy, optional_ - Visibility setting for the corpus.
  Defaults to Privacy.PRIVATE.
- `error_handler` _ErrorHandler, optional_ - Strategy for handling data
  processing errors. Defaults to ErrorHandler.SKIP.
- `description`0 _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `description`1 - Response containing:
  - status: Current processing status
  - asset_id: ID of the created corpus
  

**Raises**:

- `description`2 - If:
  - No schema or reference data provided
  - Referenced data asset doesn&#x27;t exist
  - Reserved column names are used
  - Data rows are misaligned
  - Processing or upload fails

