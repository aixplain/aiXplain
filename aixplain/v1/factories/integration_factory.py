"""Integration factory for creating and managing Integration models.

This module provides the IntegrationFactory class which handles the creation,
retrieval, and management of Integration models in the aiXplain platform.
"""

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
    def get(
        cls,
        model_id: Optional[Text] = None,
        name: Optional[Text] = None,
        api_key: Optional[Text] = None,
        use_cache: bool = False,
    ) -> Integration:
        """Retrieves a specific Integration model by its ID or name.

        Args:
            model_id (Optional[Text], optional): The unique identifier of the Integration model.
            name (Optional[Text], optional): The name of the Integration model.
            api_key (Optional[Text], optional): API key for authentication. Defaults to None.
            use_cache (bool, optional): Whether to use cached data. Defaults to False.

        Returns:
            Integration: The retrieved Integration model.

        Raises:
            AssertionError: If the provided ID/name does not correspond to an Integration model.
            ValueError: If neither model_id nor name is provided, or if both are provided.
            Exception: If the integration with the given name is not found.
        """
        # Validate that exactly one parameter is provided
        if not (model_id or name) or (model_id and name):
            raise ValueError("Must provide exactly one of 'model_id' or 'name'")

        # If name is provided, use list endpoint since by-name endpoint doesn't support integrations
        if name:
            result = cls.list(query=name, api_key=api_key)
            integrations = result.get("results", [])
            for integration in integrations:
                if integration.name == name:
                    return integration
            raise Exception(
                f"Integration GET by Name Error: Failed to retrieve integration '{name}'. "
                "No integration found with this exact name."
            )

        # If model_id is provided, use parent's get method
        model = super().get(model_id=model_id, api_key=api_key, use_cache=use_cache)
        assert isinstance(model, Integration), (
            f"The provided identifier ('{model_id}') is not from an integration model"
        )
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
