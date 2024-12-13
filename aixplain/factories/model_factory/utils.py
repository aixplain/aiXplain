import json
import logging
from aixplain.modules.model import Model
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.model.utility_model import UtilityModel, UtilityModelInput
from aixplain.enums import DataType, Function, Language, OwnershipType, Supplier, SortBy, SortOrder
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from aixplain.enums.function import FunctionInputOutput
from datetime import datetime
from typing import Dict, Union, List, Optional, Tuple
from urllib.parse import urljoin


def create_model_from_response(response: Dict) -> Model:
    """Converts response Json to 'Model' object

    Args:
        response (Dict): Json from API

    Returns:
        Model: Coverted 'Model' object
    """
    if "api_key" not in response:
        response["api_key"] = config.TEAM_API_KEY

    parameters = {}
    if "params" in response:
        for param in response["params"]:
            if "language" in param["name"]:
                parameters[param["name"]] = [w["value"] for w in param["values"]]

    function_id = response["function"]["id"]
    function = Function(function_id)
    function_io = FunctionInputOutput.get(function_id, None)
    input_params = {param["code"]: param for param in function_io["spec"]["params"]}
    output_params = {param["code"]: param for param in function_io["spec"]["output"]}

    inputs, temperature = [], None
    ModelClass = Model
    if function == Function.TEXT_GENERATION:
        ModelClass = LLM
        f = [p for p in response.get("params", []) if p["name"] == "temperature"]
        if len(f) > 0 and len(f[0].get("defaultValues", [])) > 0:
            temperature = float(f[0]["defaultValues"][0]["value"])
    elif function == Function.UTILITIES:
        ModelClass = UtilityModel
        inputs = [
            UtilityModelInput(name=param["name"], description=param.get("description", ""), type=DataType(param["dataType"]))
            for param in response["params"]
        ]
        input_params = {param["name"]: param for param in response["params"]}

    created_at = None
    if "createdAt" in response and response["createdAt"]:
        created_at = datetime.fromisoformat(response["createdAt"].replace("Z", "+00:00"))

    return ModelClass(
        response["id"],
        response["name"],
        description=response.get("description", ""),
        code=response.get("code", ""),
        supplier=response["supplier"],
        api_key=response["api_key"],
        cost=response["pricing"],
        function=function,
        created_at=created_at,
        parameters=parameters,
        input_params=input_params,
        output_params=output_params,
        is_subscribed=True if "subscription" in response else False,
        version=response["version"]["id"],
        inputs=inputs,
        temperature=temperature,
    )


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
        from aixplain.factories.model_factory.utils import create_model_from_response

        model_list = [create_model_from_response(model_info_json) for model_info_json in all_models]
        return model_list, resp["total"]
    else:
        error_message = f"Listing Models Error: Failed to retrieve models. Status Code: {r.status_code}. Error: {resp}"
        logging.error(error_message)
        raise Exception(error_message)
