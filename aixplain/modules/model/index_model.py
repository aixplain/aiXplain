import os
import warnings
from uuid import uuid4
from aixplain.enums import EmbeddingModel, Function, Supplier, ResponseStatus, StorageType, FunctionType
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.modules.model.response import ModelResponse
from typing import Text, Optional, Union, Dict
from aixplain.modules.model.record import Record
from enum import Enum
from typing import List
from aixplain.enums.splitting_options import SplittingOptions
import os

DOCLING_MODEL_ID = "677bee6c6eb56331f9192a91"

class IndexFilterOperator(Enum):
    """Enumeration of operators available for filtering index records.

    This enum defines the comparison operators that can be used when creating
    filters for searching and retrieving records from an index.

    Attributes:
        EQUALS (str): Equality operator ("==")
        NOT_EQUALS (str): Inequality operator ("!=")
        CONTAINS (str): Membership test operator ("in")
        NOT_CONTAINS (str): Negative membership test operator ("not in")
        GREATER_THAN (str): Greater than operator (">")
        LESS_THAN (str): Less than operator ("<")
        GREATER_THAN_OR_EQUALS (str): Greater than or equal to operator (">=")
        LESS_THAN_OR_EQUALS (str): Less than or equal to operator ("<=")
    """
    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "in"
    NOT_CONTAINS = "not in"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN_OR_EQUALS = "<="


class IndexFilter:
    """A class representing a filter for querying index records.

    This class defines a filter that can be used to search or retrieve records from an index
    based on specific field values and comparison operators.

    Attributes:
        field (str): The name of the field to filter on.
        value (str): The value to compare against.
        operator (Union[IndexFilterOperator, str]): The comparison operator to use.
    """

    field: str
    value: str
    operator: Union[IndexFilterOperator, str]

    def __init__(self, field: str, value: str, operator: Union[IndexFilterOperator, str]):
        """Initialize a new IndexFilter instance.

        Args:
            field (str): The name of the field to filter on.
            value (str): The value to compare against.
            operator (Union[IndexFilterOperator, str]): The comparison operator to use.
        """
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(self):
        """Convert the filter to a dictionary representation.

        Returns:
            dict: A dictionary containing the filter's field, value, and operator.
                The operator is converted to its string value if it's an IndexFilterOperator.
        """
        return {
            "field": self.field,
            "value": self.value,
            "operator": self.operator.value if isinstance(self.operator, IndexFilterOperator) else self.operator,
        }


class Splitter:
    """A class for configuring how documents should be split during indexing.

    This class provides options for splitting documents into smaller chunks before
    they are indexed, which can be useful for large documents or for specific
    search requirements.

    Attributes:
        split (bool): Whether to split the documents or not.
        split_by (SplittingOptions): The method to use for splitting (e.g., by word, sentence).
        split_length (int): The length of each split chunk.
        split_overlap (int): The number of overlapping units between consecutive chunks.
    """

    def __init__(
        self,
        split: bool = False,
        split_by: SplittingOptions = SplittingOptions.WORD,
        split_length: int = 1,
        split_overlap: int = 0,
    ):
        """Initialize a new Splitter instance.

        Args:
            split (bool, optional): Whether to split the documents. Defaults to False.
            split_by (SplittingOptions, optional): The method to use for splitting.
                Defaults to SplittingOptions.WORD.
            split_length (int, optional): The length of each split chunk. Defaults to 1.
            split_overlap (int, optional): The number of overlapping units between
                consecutive chunks. Defaults to 0.
        """
        self.split = split
        self.split_by = split_by
        self.split_length = split_length
        self.split_overlap = split_overlap


class IndexModel(Model):
    def __init__(
        self,
        id: Text,
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
        **additional_info,
    ) -> None:
        """Initialize a new IndexModel instance.

        Args:
            id (Text): ID of the Index Model.
            name (Text): Name of the Index Model.
            description (Text, optional): Description of the Index Model. Defaults to "".
            api_key (Text, optional): API key of the Index Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the Index Model. Defaults to "aiXplain".
            version (Text, optional): Version of the Index Model. Defaults to "1.0".
            function (Function, optional): Function of the Index Model. Must be Function.SEARCH.
            is_subscribed (bool, optional): Whether the user is subscribed. Defaults to False.
            cost (Dict, optional): Cost of the Index Model. Defaults to None.
            embedding_model (Union[EmbeddingModel, str], optional): Model used for embedding documents. Defaults to None.
            function_type (FunctionType, optional): Type of the function. Defaults to FunctionType.SEARCH.
            **additional_info: Any additional Index Model info to be saved.

        Raises:
            AssertionError: If function is not Function.SEARCH.
        """
        assert function == Function.SEARCH, "Index only supports search function"
        super().__init__(
            id=id,
            name=name,
            description=description,
            supplier=supplier,
            version=version,
            cost=cost,
            function=function,
            is_subscribed=is_subscribed,
            api_key=api_key,
            function_type=function_type,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.embedding_model = embedding_model
        if embedding_model:
            try:
                from aixplain.factories import ModelFactory

                model = ModelFactory.get(embedding_model)
                self.embedding_size = model.additional_info["embedding_size"]
            except Exception as e:
                warnings.warn(f"Failed to get embedding size for embedding model {embedding_model}: {e}")
                self.embedding_size = None

    def to_dict(self) -> Dict:
        """Convert the IndexModel instance to a dictionary representation.

        Returns:
            Dict: A dictionary containing the model's attributes, including:
                - All attributes from the parent Model class
                - embedding_model: The model used for embedding documents
                - embedding_size: The size of the embeddings produced
                - collection_type: The type of collection derived from the version
        """
        data = super().to_dict()
        data["embedding_model"] = self.embedding_model
        data["embedding_size"] = self.embedding_size
        data["collection_type"] = self.version.split("-", 1)[0]
        return data

    def search(self, query: str, top_k: int = 10, filters: List[IndexFilter] = []) -> ModelResponse:
        """Search for documents in the index

        Args:
            query (str): Query to be searched
            top_k (int, optional): Number of results to be returned. Defaults to 10.
            filters (List[IndexFilter], optional): Filters to be applied. Defaults to [].

        Returns:
            ModelResponse: Response from the indexing service

        Example:
            - index_model.search("Hello")
            - index_model.search("", filters=[IndexFilter(field="category", value="animate", operator=IndexFilterOperator.EQUALS)])
        """
        from aixplain.factories import FileFactory

        uri, value_type = "", "text"
        storage_type = FileFactory.check_storage_type(query)
        if storage_type in [StorageType.FILE, StorageType.URL]:
            uri = FileFactory.to_link(query)
            query = ""
            value_type = "image"

        data = {
            "action": "search",
            "data": query or uri,
            "dataType": value_type,
            "filters": [filter.to_dict() for filter in filters],
            "payload": {"uri": uri, "value_type": value_type, "top_k": top_k},
        }
        return self.run(data=data)

    def upsert(self, documents: Union[List[Record], str], splitter: Optional[Splitter] = None) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (Union[List[Record], str]): List of documents to be upserted or a file path
            splitter (Splitter, optional): Splitter to be applied. Defaults to None.

        Returns:
            ModelResponse: Response from the indexing service

        Examples:
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})], splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=1, split_overlap=0))
            index_model.upsert("my_file.pdf")
            index_model.upsert("my_file.pdf", splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=400, split_overlap=50))
            Splitter in the above example is optional and can be used to split the documents into smaller chunks.
        """
        if isinstance(documents, str):
            documents = [self.prepare_record_from_file(documents)]
        # Validate documents
        for doc in documents:
            doc.validate()
        # Convert documents to payloads
        payloads = [doc.to_dict() for doc in documents]
        # Build payload
        data = {
            "action": "ingest",
            "data": payloads,
        }
        if splitter and splitter.split:
            data["additional_params"] = {
                "splitter": {
                    "split": splitter.split,
                    "split_by": splitter.split_by,
                    "split_length": splitter.split_length,
                    "split_overlap": splitter.split_overlap,
                }
            }
        # Run the indexing service
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            response.data = payloads
            return response
        raise Exception(f"Failed to upsert documents: {response.error_message}")

    def count(self) -> int:
        """Get the total number of documents in the index.

        Returns:
            float: The number of documents in the index.

        Raises:
            Exception: If the count operation fails.

        Example:
            >>> index_model.count()
            42
        """
        data = {"action": "count", "data": ""}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return int(response.data)
        raise Exception(f"Failed to count documents: {response.error_message}")

    def get_record(self, record_id: Text) -> ModelResponse:
        """
        Get a document from the index.

        Args:
            record_id (Text): ID of the document to retrieve.

        Returns:
            ModelResponse: Response containing the retrieved document data.

        Raises:
            Exception: If document retrieval fails.

        Example:
            >>> index_model.get_record("123")
        """
        data = {"action": "get_document", "data": record_id}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to get record: {response.error_message}")

    def delete_record(self, record_id: Text) -> ModelResponse:
        """
        Delete a document from the index.

        Args:
            record_id (Text): ID of the document to delete.

        Returns:
            ModelResponse: Response containing the deleted document data.

        Raises:
            Exception: If document deletion fails.

        Example:
            >>> index_model.delete_record("123")
        """
        data = {"action": "delete", "data": record_id}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to delete record: {response.error_message}")

    def prepare_record_from_file(self, file_path: str, file_id: str = None) -> Record:
        """Prepare a record from a file.

        Args:
            file_path (str): The path to the file to be processed.
            file_id (str, optional): The ID to assign to the record. If not provided, a unique ID is generated.

        Returns:
            Record: A Record object containing the file's content and metadata.

        Raises:
            Exception: If the file cannot be parsed.

        Example:
            >>> record = index_model.prepare_record_from_file("/path/to/file.txt")
        """
        response = self.parse_file(file_path)
        file_name = file_path.split("/")[-1]
        if not file_id:
            file_id = file_name + "_" + str(uuid4())
        return Record(value=response.data, value_type="text", id=file_id, attributes={"file_name": file_name})

    @staticmethod
    def parse_file(file_path: str) -> ModelResponse:
        """Parse a file using the Docling model.

        Args:
            file_path (str): The path to the file to be parsed.

        Returns:
            ModelResponse: The response containing the parsed file content.

        Raises:
            Exception: If the file does not exist or cannot be parsed.

        Example:
            >>> response = IndexModel.parse_file("/path/to/file.pdf")
        """
        if not os.path.exists(file_path):
            raise Exception(f"File {file_path} does not exist")
        if file_path.endswith(".txt"):
            with open(file_path, "r") as file:
                data = file.read()
            if not data:
                warnings.warn(f"File {file_path} is empty")
            return ModelResponse(status=ResponseStatus.SUCCESS, data=data, completed=True)
        try:
            from aixplain.factories import ModelFactory

            model = ModelFactory.get(DOCLING_MODEL_ID)
            response = model.run(file_path)
            if not response.data:
                warnings.warn(f"File {file_path} is empty")
            return response
        except Exception as e:
            raise Exception(f"Failed to parse file: {e}")

    def retrieve_records_with_filter(self, filter: IndexFilter) -> ModelResponse:
        """
        Retrieve records from the index that match the given filter.

        Args:
            filter (IndexFilter): The filter criteria to apply when retrieving records.

        Returns:
            ModelResponse: Response containing the retrieved records.

        Raises:
            Exception: If retrieval fails.

        Example:
            >>> from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator
            >>> my_filter = IndexFilter(field="category", value="world", operator=IndexFilterOperator.EQUALS)
            >>> index_model.retrieve_records_with_filter(my_filter)
        """
        data = {"action": "retrieve_by_filter", "data": filter.to_dict()}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to retrieve records with filter: {response.error_message}")

    def delete_records_by_date(self, date: float) -> ModelResponse:
        """
        Delete records from the index that match the given date.

        Args:
            date (float): The date (as a timestamp) to match records for deletion.

        Returns:
            ModelResponse: Response containing the result of the deletion operation.

        Raises:
            Exception: If deletion fails.

        Example:
            >>> index_model.delete_records_by_date(1717708800)
        """
        data = {"action": "delete_by_date", "data": date}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to delete records by date: {response.error_message}")
