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

from urllib.parse import urljoin
from aixplain.utils.file_utils import _request_with_retry


class IndexFilterOperator(Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "in"
    NOT_CONTAINS = "not in"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN_OR_EQUALS = "<="


class IndexFilter:
    field: str
    value: str
    operator: Union[IndexFilterOperator, str]

    def __init__(self, field: str, value: str, operator: Union[IndexFilterOperator, str]):
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(self):
        return {
            "field": self.field,
            "value": self.value,
            "operator": self.operator.value if isinstance(self.operator, IndexFilterOperator) else self.operator,
        }


class Splitter:
    def __init__(
        self,
        split: bool = False,
        split_by: SplittingOptions = SplittingOptions.WORD,
        split_length: int = 1,
        split_overlap: int = 0,
    ):
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
        """Index Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            embedding_model (Union[EmbeddingModel, str], optional): embedding model. Defaults to None.
            **additional_info: Any additional Model info to be saved
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
                import warnings

                warnings.warn(f"Failed to get embedding size for embedding model {embedding_model}: {e}")
                self.embedding_size = None

    def to_dict(self) -> Dict:
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
            "payload": {"uri": uri, "value_type": value_type, "top_k": top_k}
        }
        return self.run(data=data)

    def upsert(self, documents: List[Record], splitter: Optional[Splitter] = None) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (List[Record]): List of documents to be upserted
            splitter (Splitter, optional): Splitter to be applied. Defaults to None.

        Returns:
            ModelResponse: Response from the indexing service

        Examples:
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})], splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=1, split_overlap=0))
            Splitter in the above example is optional and can be used to split the documents into smaller chunks.
        """
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

    def count(self) -> float:
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
