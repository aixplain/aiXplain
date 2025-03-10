from aixplain.modules import Model
from aixplain.modules.model.index_model import IndexModel
from aixplain.factories import ModelFactory
from aixplain.enums import Function, ResponseStatus, SortBy, SortOrder, OwnershipType, Supplier
from typing import Optional, Text, Union, List, Tuple


class IndexFactory(ModelFactory):
    @classmethod
    def create(
        cls, name: Text, description: Text, embedding_model: Union[Model, Text] = "6734c55df127847059324d9e"
    ) -> IndexModel:
        """Create a new index collection"""
        if isinstance(embedding_model, Model):
            embedding_model = embedding_model.id

        assert embedding_model in [
            "6658d40729985c2cf72f42ec",
            "6734c55df127847059324d9e",
            "678a4f8547f687504744960a",
            "67c5f705d8f6a65d6f74d732",
        ], "Index Creation Collection Error: Invalid embedding model. Current supported models are: Snowflake Arctic-embed M-long (6658d40729985c2cf72f42ec), OpenAI Ada-002 (6734c55df127847059324d9e), Snowflake Arctic-embed L-v2.0 (678a4f8547f687504744960a), Jina Clip-v2 Multimodal (67c5f705d8f6a65d6f74d732)"

        model = cls.get("66eae6656eb56311f2595011")

        data = {"data": name, "description": description, "model": embedding_model}
        response = model.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            model_id = response.data
            model = cls.get(model_id)
            return model

        error_message = f"Index Factory Exception: {response.error_message}"
        if error_message == "":
            error_message = "Index Factory Exception:An error occurred while creating the index collection."
        raise Exception(error_message)

    @classmethod
    def list(
        cls,
        query: Optional[Text] = "",
        suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
        ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
        sort_by: Optional[SortBy] = None,
        sort_order: SortOrder = SortOrder.ASCENDING,
        page_number: int = 0,
        page_size: int = 20,
    ) -> List[IndexModel]:
        """List all indexes"""
        return super().list(
            function=Function.SEARCH,
            query=query,
            suppliers=suppliers,
            ownership=ownership,
            sort_by=sort_by,
            sort_order=sort_order,
            page_number=page_number,
            page_size=page_size,
        )
