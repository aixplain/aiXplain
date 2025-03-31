from aixplain.enums import EmbeddingModel, Function, Supplier, ResponseStatus, StorageType
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.modules.model.response import ModelResponse
from typing import Text, Optional, Union, Dict
from aixplain.modules.model.record import Record
from enum import Enum
from typing import List


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
        embedding_model: Optional[EmbeddingModel] = None,
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
            embedding_model (EmbeddingModel, optional): embedding model. Defaults to None.
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
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.embedding_model = embedding_model

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

    def upsert(self, documents: List[Record]) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (List[Record]): List of documents to be upserted

        Returns:
            ModelResponse: Response from the indexing service

        Example:
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
        """
        # Validate documents
        for doc in documents:
            doc.validate()
        # Convert documents to payloads
        payloads = [doc.to_dict() for doc in documents]
        # Build payload
        data = {"action": "ingest", "data": payloads}
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
    
    def get_document(self, document_id: Text) -> ModelResponse:
        """
        Get a document from the index.

        Args:
            document_id (Text): ID of the document to retrieve.

        Returns:
            ModelResponse: Response containing the retrieved document data.

        Raises:
            Exception: If document retrieval fails.
        
        Example:
            >>> index_model.get_document("123")
        """
        data = {"action": "get_document", "data": document_id}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to get document: {response.error_message}")

    def delete_document(self, document_id: Text) -> ModelResponse:
        """
        Delete a document from the index.

        Args:
            document_id (Text): ID of the document to delete.

        Returns:
            ModelResponse: Response containing the deleted document data.

        Raises:
            Exception: If document deletion fails.

        Example:
            >>> index_model.delete_document("123")
        """
        data = {"action": "delete", "data": document_id}
        response = self.run(data=data)
        if response.status == "SUCCESS":
            return response
        raise Exception(f"Failed to delete document: {response.error_message}")