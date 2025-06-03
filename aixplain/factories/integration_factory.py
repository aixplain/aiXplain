__author__ = "thiagocastroferreira"

import aixplain.utils.config as config
from aixplain.enums import Function, Supplier, SortBy, SortOrder, OwnershipType
from aixplain.factories.model_factory.mixins.model_getter import ModelGetterMixin
from aixplain.factories.model_factory.mixins.model_list import ModelListMixin
from aixplain.modules.model.integration import Integration
from typing import Optional, Text, Union, Tuple, List


class IntegrationFactory(ModelGetterMixin, ModelListMixin):
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, model_id: Text, api_key: Optional[Text] = None, use_cache: bool = False) -> Integration:
        model = super().get(model_id=model_id, api_key=api_key)
        assert isinstance(model, Integration), f"The provided ID ('{model_id}') is not from an integration model"
        return model

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
        api_key: Optional[Text] = None,
    ) -> List[Integration]:
        return super().list(
            function=Function.CONNECTOR,
            query=query,
            suppliers=suppliers,
            ownership=ownership,
            sort_by=sort_by,
            sort_order=sort_order,
            page_number=page_number,
            page_size=page_size,
            api_key=api_key,
        )
