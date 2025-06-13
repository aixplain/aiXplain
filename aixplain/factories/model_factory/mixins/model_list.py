from typing import Optional, Union, List, Tuple, Text
from aixplain.factories.model_factory.utils import get_model_from_ids, get_assets_from_page
from aixplain.enums import Function, Language, OwnershipType, SortBy, SortOrder, Supplier
from aixplain.modules.model import Model


class ModelListMixin:
    @classmethod
    def list(
        cls,
        function: Optional[Function] = None,
        query: Optional[Text] = "",
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
    ) -> List[Model]:
        """Gets the first k given models based on the provided task and language filters

        Args:
            function (Function): function filter.
            source_languages (Optional[Union[Language, List[Language]]], optional): language filter of input data. Defaults to None.
            target_languages (Optional[Union[Language, List[Language]]], optional): language filter of output data. Defaults to None.
            is_finetunable (Optional[bool], optional): can be finetuned or not. Defaults to None.
            ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional): Ownership filters (e.g. SUBSCRIBED, OWNER). Defaults to None.
            sort_by (Optional[SortBy], optional): sort the retrived models by a specific attribute,
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.
            model_ids (Optional[List[Text]], optional): model ids to filter. Defaults to None.
            api_key (Optional[Text], optional): Team API key. Defaults to None.

        Returns:
            List[Model]: List of models based on given filters
        """
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
            ), "Cannot filter by function, suppliers, source languages, target languages, is finetunable, ownership, sort by when using model ids"
            assert len(model_ids) <= page_size, "Page size must be greater than the number of model ids"
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
