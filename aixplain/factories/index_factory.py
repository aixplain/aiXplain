from aixplain.modules.model.index_model import IndexModel
from aixplain.factories import ModelFactory
from aixplain.enums import EmbeddingModel, Function, ResponseStatus, SortBy, SortOrder, OwnershipType, Supplier
from typing import Optional, Text, Union, List, Tuple

AIR_MODEL_ID = "66eae6656eb56311f2595011"


class IndexFactory(ModelFactory):
    @classmethod
    def create(
        cls, name: Text, description: Text, embedding_model: EmbeddingModel = EmbeddingModel.OPENAI_ADA002
    ) -> IndexModel:
        """Create a new index collection"""
        model = cls.get(AIR_MODEL_ID)

        data = {"data": name, "description": description, "model": embedding_model.value}
        response = model.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            model_id = response.data
            model = cls.get(model_id)
            return model

        error_message = f"Index Factory Exception: {response.error_message}"
        if error_message == "":
            error_message = "Index Factory Exception: An error occurred while creating the index collection."
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
