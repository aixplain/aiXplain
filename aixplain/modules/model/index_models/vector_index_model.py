from typing import Union, List, Text, Optional, Dict
from enum import Enum
from aixplain.enums import StorageType
from aixplain.modules.model.index_models.index_model import IndexModel
from aixplain.modules.model.response import ModelResponse
from aixplain.enums import Function, Supplier, EmbeddingModel


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


class VectorIndexModel(IndexModel):
    supported_indices = ["airv2", "vectara", "zeroentropy"]

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
        **additional_info
    ):
        super().__init__(
            id, name, description, api_key, supplier, version, function, is_subscribed, cost, embedding_model, **additional_info
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
