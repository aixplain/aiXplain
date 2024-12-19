from aixplain.enums import Function, Supplier
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.modules.model.response import ModelResponse
from typing import Text, Optional, Union, Dict
from aixplain.modules.document_index import DocumentIndex
from typing import List
import logging
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

    def search(self, query: str, top_k: int = 10) -> ModelResponse:
        data = {"action": "search", "data": query, "payload": {"filters": {}, "top_k": top_k}}
        return self.run(data=data)

    def add(self, documents: List[DocumentIndex]) -> ModelResponse:
        payloads = [{"value": doc.value, "value_type": doc.value_type, "id": str(doc.id), "uri": doc.uri, "attributes": doc.attributes} for doc in documents]
        data = {"action": "ingest", "data": "", "payload": {"payloads": payloads}}
        return self.run(data=data)

    def update(self, documents: List[DocumentIndex]) -> ModelResponse:
        payloads = [{"value": doc.value, "value_type": doc.value_type, "id": str(doc.id), "uri": doc.uri, "attributes": doc.attributes} for doc in documents]
        data = {"action": "update", "data": "", "payload": {"payloads": payloads}}
        return self.run(data=data)

    def count(self) -> ModelResponse:
        data = {"action": "count", "data": ""}
        return self.run(data=data)
