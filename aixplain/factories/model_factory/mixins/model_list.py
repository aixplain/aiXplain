import json
import logging
from typing import Optional, Union, List, Tuple, Text
from aixplain.enums import Function, Language, OwnershipType, SortBy, SortOrder, Supplier
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin


def get_assets_from_page(
    query,
    page_number: int,
    page_size: int,
    function: Function,
    suppliers: Union[Supplier, List[Supplier]],
    source_languages: Union[Language, List[Language]],
    target_languages: Union[Language, List[Language]],
    is_finetunable: bool = None,
    ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
    sort_by: Optional[SortBy] = None,
    sort_order: SortOrder = SortOrder.ASCENDING,
    api_key: Optional[str] = None,
) -> List[Model]:
    try:
        url = urljoin(config.BACKEND_URL, "sdk/models/paginate")
        filter_params = {"q": query, "pageNumber": page_number, "pageSize": page_size}
        if is_finetunable is not None:
            filter_params["isFineTunable"] = is_finetunable
        if function is not None:
            filter_params["functions"] = [function.value]
        if suppliers is not None:
            if isinstance(suppliers, Supplier) is True:
                suppliers = [suppliers]
            filter_params["suppliers"] = [supplier.value["id"] for supplier in suppliers]
        if ownership is not None:
            if isinstance(ownership, OwnershipType) is True:
                ownership = [ownership]
            filter_params["ownership"] = [ownership_.value for ownership_ in ownership]

        lang_filter_params = []
        if source_languages is not None:
            if isinstance(source_languages, Language):
                source_languages = [source_languages]
            if function == Function.TRANSLATION:
                lang_filter_params.append({"code": "sourcelanguage", "value": source_languages[0].value["language"]})
            else:
                lang_filter_params.append({"code": "language", "value": source_languages[0].value["language"]})
                if source_languages[0].value["dialect"] != "":
                    lang_filter_params.append({"code": "dialect", "value": source_languages[0].value["dialect"]})
        if target_languages is not None:
            if isinstance(target_languages, Language):
                target_languages = [target_languages]
            if function == Function.TRANSLATION:
                code = "targetlanguage"
                lang_filter_params.append({"code": code, "value": target_languages[0].value["language"]})
        if sort_by is not None:
            filter_params["sort"] = [{"dir": sort_order.value, "field": sort_by.value}]
        if len(lang_filter_params) != 0:
            filter_params["ioFilter"] = lang_filter_params
        headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

        logging.info(f"Start service for POST Models Paginate - {url} - {headers} - {json.dumps(filter_params)}")
        r = _request_with_retry("post", url, headers=headers, json=filter_params)
        resp = r.json()

    except Exception as e:
        error_message = f"Listing Models: Error in getting Models on Page {page_number}: {e}"
        logging.error(error_message, exc_info=True)
        return []
    if 200 <= r.status_code < 300:
        logging.info(f"Listing Models: Status of getting Models on Page {page_number}: {r.status_code}")
        all_models = resp["items"]
        from aixplain.factories.model_factory.mixins import create_model_from_response

        model_list = []
        for model_info_json in all_models:
            model_info_json["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                model_info_json["api_key"] = api_key
            model_list.append(create_model_from_response(model_info_json))
        return model_list, resp["total"]
    else:
        error_message = f"Listing Models Error: Failed to retrieve models. Status Code: {r.status_code}. Error: {resp}"
        logging.error(error_message)
        raise Exception(error_message)


def get_model_from_ids(model_ids: List[str], api_key: Optional[str] = None) -> List[Model]:
    from aixplain.factories.model_factory.mixins import create_model_from_response

    resp = None
    try:
        url = urljoin(config.BACKEND_URL, f"sdk/models?ids={','.join(model_ids)}")
        api_key = config.TEAM_API_KEY if api_key is None else api_key
        headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Model  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()

    except Exception:
        if resp is not None and "statusCode" in resp:
            status_code = resp["statusCode"]
            message = resp["message"]
            message = f"Model Creation: Status {status_code} - {message}"
        else:
            message = "Model Creation: Unspecified Error"
        logging.error(message)
        raise Exception(f"{message}")
    if 200 <= r.status_code < 300:
        models = []
        for item in resp["items"]:
            item["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                item["api_key"] = api_key
            models.append(create_model_from_response(item))
        return models
    else:
        error_message = f"Model GET Error: Failed to retrieve models {model_ids}. Status Code: {r.status_code}. Error: {resp}"
        logging.error(error_message)
        raise Exception(error_message)


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
