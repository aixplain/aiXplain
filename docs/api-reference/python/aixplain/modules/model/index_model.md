---
sidebar_label: index_model
title: aixplain.modules.model.index_model
---

### IndexFilterOperator Objects

```python
class IndexFilterOperator(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L17)

Enumeration of operators available for filtering index records.

This enum defines the comparison operators that can be used when creating
filters for searching and retrieving records from an index.

**Attributes**:

- `EQUALS` _str_ - Equality operator (&quot;==&quot;)
- `NOT_EQUALS` _str_ - Inequality operator (&quot;!=&quot;)
- `CONTAINS` _str_ - Membership test operator (&quot;in&quot;)
- `NOT_CONTAINS` _str_ - Negative membership test operator (&quot;not in&quot;)
- `GREATER_THAN` _str_ - Greater than operator (&quot;&gt;&quot;)
- `LESS_THAN` _str_ - Less than operator (&quot;&lt;&quot;)
- `GREATER_THAN_OR_EQUALS` _str_ - Greater than or equal to operator (&quot;&gt;=&quot;)
- `LESS_THAN_OR_EQUALS` _str_ - Less than or equal to operator (&quot;&lt;=&quot;)

### IndexFilter Objects

```python
class IndexFilter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L43)

A class representing a filter for querying index records.

This class defines a filter that can be used to search or retrieve records from an index
based on specific field values and comparison operators.

**Attributes**:

- `field` _str_ - The name of the field to filter on.
- `value` _str_ - The value to compare against.
- `operator` _Union[IndexFilterOperator, str]_ - The comparison operator to use.

#### \_\_init\_\_

```python
def __init__(field: str, value: str, operator: Union[IndexFilterOperator,
                                                     str])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L59)

Initialize a new IndexFilter instance.

**Arguments**:

- `field` _str_ - The name of the field to filter on.
- `value` _str_ - The value to compare against.
- `operator` _Union[IndexFilterOperator, str]_ - The comparison operator to use.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L71)

Convert the filter to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the filter&#x27;s field, value, and operator.
  The operator is converted to its string value if it&#x27;s an IndexFilterOperator.

### Splitter Objects

```python
class Splitter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L85)

A class for configuring how documents should be split during indexing.

This class provides options for splitting documents into smaller chunks before
they are indexed, which can be useful for large documents or for specific
search requirements.

**Attributes**:

- `split` _bool_ - Whether to split the documents or not.
- `split_by` _SplittingOptions_ - The method to use for splitting (e.g., by word, sentence).
- `split_length` _int_ - The length of each split chunk.
- `split_overlap` _int_ - The number of overlapping units between consecutive chunks.

#### \_\_init\_\_

```python
def __init__(split: bool = False,
             split_by: SplittingOptions = SplittingOptions.WORD,
             split_length: int = 1,
             split_overlap: int = 0)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L99)

Initialize a new Splitter instance.

**Arguments**:

- `split` _bool, optional_ - Whether to split the documents. Defaults to False.
- `split_by` _SplittingOptions, optional_ - The method to use for splitting.
  Defaults to SplittingOptions.WORD.
- `split_length` _int, optional_ - The length of each split chunk. Defaults to 1.
- `split_overlap` _int, optional_ - The number of overlapping units between
  consecutive chunks. Defaults to 0.

### IndexModel Objects

```python
class IndexModel(Model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L122)

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text = "",
             api_key: Optional[Text] = None,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             function: Optional[Function] = None,
             is_subscribed: bool = False,
             cost: Optional[Dict] = None,
             embedding_model: Union[EmbeddingModel, str] = None,
             function_type: Optional[FunctionType] = FunctionType.SEARCH,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L123)

Initialize a new IndexModel instance.

**Arguments**:

- `id` _Text_ - ID of the Index Model.
- `name` _Text_ - Name of the Index Model.
- `description` _Text, optional_ - Description of the Index Model. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key of the Index Model. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the Index Model. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version of the Index Model. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - Function of the Index Model. Must be Function.SEARCH.
- `is_subscribed` _bool, optional_ - Whether the user is subscribed. Defaults to False.
- `cost` _Dict, optional_ - Cost of the Index Model. Defaults to None.
- `embedding_model` _Union[EmbeddingModel, str], optional_ - Model used for embedding documents. Defaults to None.
- `name`0 _FunctionType, optional_ - Type of the function. Defaults to FunctionType.SEARCH.
- `name`1 - Any additional Index Model info to be saved.
  

**Raises**:

- `name`2 - If function is not Function.SEARCH.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L184)

Convert the IndexModel instance to a dictionary representation.

**Returns**:

- `Dict` - A dictionary containing the model&#x27;s attributes, including:
  - All attributes from the parent Model class
  - embedding_model: The model used for embedding documents
  - embedding_size: The size of the embeddings produced
  - collection_type: The type of collection derived from the version

#### search

```python
def search(query: str,
           top_k: int = 10,
           filters: List[IndexFilter] = []) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L200)

Search for documents in the index

**Arguments**:

- `query` _str_ - Query to be searched
- `top_k` _int, optional_ - Number of results to be returned. Defaults to 10.
- `filters` _List[IndexFilter], optional_ - Filters to be applied. Defaults to [].
  

**Returns**:

- `ModelResponse` - Response from the indexing service
  

**Example**:

  - index_model.search(&quot;Hello&quot;)
  - index_model.search(&quot;&quot;, filters=[IndexFilter(field=&quot;category&quot;, value=&quot;animate&quot;, operator=IndexFilterOperator.EQUALS)])

#### upsert

```python
def upsert(documents: Union[List[Record], str],
           splitter: Optional[Splitter] = None) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L233)

Upsert documents into the index

**Arguments**:

- `documents` _Union[List[Record], str]_ - List of documents to be upserted or a file path
- `splitter` _Splitter, optional_ - Splitter to be applied. Defaults to None.
  

**Returns**:

- `ModelResponse` - Response from the indexing service
  

**Examples**:

  index_model.upsert([Record(value=&quot;Hello, world!&quot;, value_type=&quot;text&quot;, uri=&quot;&quot;, id=&quot;1&quot;, attributes=\{})])
  index_model.upsert([Record(value=&quot;Hello, world!&quot;, value_type=&quot;text&quot;, uri=&quot;&quot;, id=&quot;1&quot;, attributes=\{})], splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=1, split_overlap=0))
  index_model.upsert(&quot;my_file.pdf&quot;)
  index_model.upsert(&quot;my_file.pdf&quot;, splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=400, split_overlap=50))
  Splitter in the above example is optional and can be used to split the documents into smaller chunks.

#### count

```python
def count() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L278)

Get the total number of documents in the index.

**Returns**:

- `float` - The number of documents in the index.
  

**Raises**:

- `Exception` - If the count operation fails.
  

**Example**:

  &gt;&gt;&gt; index_model.count()
  42

#### get\_record

```python
def get_record(record_id: Text) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L297)

Get a document from the index.

**Arguments**:

- `record_id` _Text_ - ID of the document to retrieve.
  

**Returns**:

- `ModelResponse` - Response containing the retrieved document data.
  

**Raises**:

- `Exception` - If document retrieval fails.
  

**Example**:

  &gt;&gt;&gt; index_model.get_record(&quot;123&quot;)

#### delete\_record

```python
def delete_record(record_id: Text) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L319)

Delete a document from the index.

**Arguments**:

- `record_id` _Text_ - ID of the document to delete.
  

**Returns**:

- `ModelResponse` - Response containing the deleted document data.
  

**Raises**:

- `Exception` - If document deletion fails.
  

**Example**:

  &gt;&gt;&gt; index_model.delete_record(&quot;123&quot;)

#### prepare\_record\_from\_file

```python
def prepare_record_from_file(file_path: str, file_id: str = None) -> Record
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L341)

Prepare a record from a file.

**Arguments**:

- `file_path` _str_ - The path to the file to be processed.
- `file_id` _str, optional_ - The ID to assign to the record. If not provided, a unique ID is generated.
  

**Returns**:

- `Record` - A Record object containing the file&#x27;s content and metadata.
  

**Raises**:

- `Exception` - If the file cannot be parsed.
  

**Example**:

  &gt;&gt;&gt; record = index_model.prepare_record_from_file(&quot;/path/to/file.txt&quot;)

#### parse\_file

```python
@staticmethod
def parse_file(file_path: str) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L364)

Parse a file using the Docling model.

**Arguments**:

- `file_path` _str_ - The path to the file to be parsed.
  

**Returns**:

- `ModelResponse` - The response containing the parsed file content.
  

**Raises**:

- `Exception` - If the file does not exist or cannot be parsed.
  

**Example**:

  &gt;&gt;&gt; response = IndexModel.parse_file(&quot;/path/to/file.pdf&quot;)

#### retrieve\_records\_with\_filter

```python
def retrieve_records_with_filter(filter: IndexFilter) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L398)

Retrieve records from the index that match the given filter.

**Arguments**:

- `filter` _IndexFilter_ - The filter criteria to apply when retrieving records.
  

**Returns**:

- `ModelResponse` - Response containing the retrieved records.
  

**Raises**:

- `Exception` - If retrieval fails.
  

**Example**:

  &gt;&gt;&gt; from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator
  &gt;&gt;&gt; my_filter = IndexFilter(field=&quot;category&quot;, value=&quot;world&quot;, operator=IndexFilterOperator.EQUALS)
  &gt;&gt;&gt; index_model.retrieve_records_with_filter(my_filter)

#### delete\_records\_by\_date

```python
def delete_records_by_date(date: float) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/index_model.py#L422)

Delete records from the index that match the given date.

**Arguments**:

- `date` _float_ - The date (as a timestamp) to match records for deletion.
  

**Returns**:

- `ModelResponse` - Response containing the result of the deletion operation.
  

**Raises**:

- `Exception` - If deletion fails.
  

**Example**:

  &gt;&gt;&gt; index_model.delete_records_by_date(1717708800)

