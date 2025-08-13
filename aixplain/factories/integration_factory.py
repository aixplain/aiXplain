__author__ = "thiagocastroferreira"

import aixplain.utils.config as config
from aixplain.enums import Function, Supplier, SortBy, SortOrder, OwnershipType
from aixplain.factories.model_factory.mixins.model_getter import ModelGetterMixin
from aixplain.factories.model_factory.mixins.model_list import ModelListMixin
from aixplain.modules.model.integration import Integration
from typing import Optional, Text, Union, Tuple, List


class IntegrationFactory(ModelGetterMixin, ModelListMixin):
    """Factory class for creating and managing Integration models.

    This class provides functionality to get and list Integration models using the backend API.
    It inherits from ModelGetterMixin and ModelListMixin to provide model retrieval and listing capabilities.

    Attributes:
        backend_url: The URL of the backend API endpoint.
    """
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, model_id: Text, api_key: Optional[Text] = None, use_cache: bool = False) -> Integration:
        """Retrieves a specific Integration model by its ID.

        Args:
            model_id (Text): The unique identifier of the Integration model.
            api_key (Optional[Text], optional): API key for authentication. Defaults to None.
            use_cache (bool, optional): Whether to use cached data. Defaults to False.

        Returns:
            Integration: The retrieved Integration model.

        Raises:
            AssertionError: If the provided ID does not correspond to an Integration model.
        """
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
        """Lists Integration models based on the provided filters and pagination parameters.

        Args:
            query (Optional[Text], optional): Search query string. Defaults to "".
            suppliers (Optional[Union[Supplier, List[Supplier]]], optional): Filter by supplier(s). Defaults to None.
            ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional): Filter by ownership type. Defaults to None.
            sort_by (Optional[SortBy], optional): Field to sort results by. Defaults to None.
            sort_order (SortOrder, optional): Sort order (ascending/descending). Defaults to SortOrder.ASCENDING.
            page_number (int, optional): Page number for pagination. Defaults to 0.
            page_size (int, optional): Number of items per page. Defaults to 20.
            api_key (Optional[Text], optional): API key for authentication. Defaults to None.

        Returns:
            List[Integration]: A list of Integration models matching the specified criteria.
        """
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
