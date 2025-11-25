from typing import Optional, Union, List, Tuple, Text
from aixplain.factories.model_factory.utils import (
    get_model_from_ids, get_assets_from_page
)
from aixplain.enums import (
    Function, Language, OwnershipType, SortBy, SortOrder, Supplier
)
from aixplain.modules.model import Model


class ModelListMixin:
    """Mixin class providing model listing functionality.

    This mixin provides methods for retrieving lists of models with various
    filtering and sorting options.
    """
    @classmethod
    def list(
        cls,
        query: Optional[Text] = "",
        function: Optional[Function] = None,
        suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
        source_languages: Optional[Union[Language, List[Language]]] = None,
        target_languages: Optional[Union[Language, List[Language]]] = None,
        is_finetunable: Optional[bool] = None,
        ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
        sort_by: Optional[SortBy] = None,
        sort_order: SortOrder = SortOrder.ASCENDING,
        page_number: int = 0,
        page_size: int = 20,
        model_ids: Optional[List[Text]] = None,
        api_key: Optional[Text] = None,
        **kwargs
    ) -> List[Model]:
        """List and filter available models with pagination support.

        This method provides comprehensive filtering capabilities for retrieving
        models. It supports two modes:
        1. Filtering by model IDs (exclusive of other filters)
        2. Filtering by various criteria (function, language, etc.)

        Args:
            query (Optional[Text], optional): Search query to filter models.
                Defaults to "".
            function (Optional[Function], optional): Filter by model function/task.
                Defaults to None.
            suppliers (Optional[Union[Supplier, List[Supplier]]], optional): Filter by
                supplier(s). Defaults to None.
            source_languages (Optional[Union[Language, List[Language]]], optional):
                Filter by input language(s). Defaults to None.
            target_languages (Optional[Union[Language, List[Language]]], optional):
                Filter by output language(s). Defaults to None.
            is_finetunable (Optional[bool], optional): Filter by fine-tuning capability.
                Defaults to None.
            ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
                Filter by ownership type (e.g., SUBSCRIBED, OWNER). Defaults to None.
            sort_by (Optional[SortBy], optional): Attribute to sort results by.
                Defaults to None.
            sort_order (SortOrder, optional): Sort direction (ascending/descending).
                Defaults to SortOrder.ASCENDING.
            page_number (int, optional): Page number for pagination. Defaults to 0.
            page_size (int, optional): Number of results per page. Defaults to 20.
            model_ids (Optional[List[Text]], optional): List of specific model IDs to retrieve.
                If provided, other filters are ignored. Defaults to None.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            dict: Dictionary containing:
                - results (List[Model]): List of models matching the criteria
                - page_total (int): Number of models in current page
                - page_number (int): Current page number
                - total (int): Total number of models matching the criteria

        Raises:
            AssertionError: If model_ids is provided with other filters, or if
                page_size is less than the number of requested model_ids.
        """
        api_key = kwargs.get("api_key", None) if api_key is None else api_key
        if model_ids is not None:
            assert len(model_ids) > 0, "Please provide at least one model id"
            assert (
                function is None
                and suppliers is None
                and source_languages is None
                and target_languages is None
                and is_finetunable is None
                and ownership is None
                and sort_by is None
            ), (
                "Cannot filter by function, suppliers, source languages, "
                "target languages, is finetunable, ownership, sort by when "
                "using model ids"
            )
            assert (
                len(model_ids) <= page_size
            ), "Page size must be greater than the number of model ids"
            models, total = get_model_from_ids(model_ids, api_key), len(model_ids)
        else:
            models, total = get_assets_from_page(
                query,
                page_number,
                page_size,
                function,
                suppliers,
                source_languages,
                target_languages,
                is_finetunable,
                ownership,
                sort_by,
                sort_order,
                api_key,
            )
        return {
            "results": models,
            "page_total": min(page_size, len(models)),
            "page_number": page_number,
            "total": total,
        }
