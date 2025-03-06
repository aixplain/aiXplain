from aixplain.enums import Function, Supplier, ResponseStatus
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.modules.model.response import ModelResponse
from typing import Text, Optional, Union, Dict
from aixplain.modules.model.record import Record
from typing import List


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

    def search(self, query: str, top_k: int = 10, filters: Dict = {}) -> ModelResponse:
        data = {"action": "search", "data": query, "payload": {"filters": filters, "top_k": top_k}}
        return self.run(data=data)

    def upsert(self, documents: List[Record]) -> ModelResponse:
        payloads = [doc.to_dict() for doc in documents]
        data = {"action": "ingest", "data": "", "payload": {"payloads": payloads}}
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
