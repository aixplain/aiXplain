from typing import Union, List, Text, Optional, Dict
from enum import Enum
from aixplain.enums import StorageType
from aixplain.modules.model.index_models.base_index_model import BaseIndexModel, Splitter
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.enums import Function, Supplier, EmbeddingModel, ResponseStatus, IndexType


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


class VectorIndexModel(BaseIndexModel):
    supported_indices = ["airv2", "vectara", "zeroentropy"]

    def __init__(
        self,
        id: Text,
        name: Text,
        version: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        embedding_model: Optional[EmbeddingModel] = None,
        **additional_info,
    ):
        super().__init__(
            id,
            name,
            version,
            description,
            api_key,
            supplier,
            function,
            is_subscribed,
            cost,
            embedding_model,
            IndexType.VECTOR,
            **additional_info,
        )

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

    def upsert(self, documents: List[Record], splitter: Optional[Splitter] = None) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (List[Record]): List of documents to be upserted
            splitter (Splitter, optional): Splitter to be applied. Defaults to None.

        Returns:
            ModelResponse: Response from the indexing service

        Example:
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
