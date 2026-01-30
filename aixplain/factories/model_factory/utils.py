import json
import logging
from aixplain.modules.model import Model
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.model.index_model import IndexModel
from aixplain.modules.model.integration import Integration
from aixplain.modules.model.connection import ConnectionTool
from aixplain.modules.model.mcp_connection import MCPConnection
from aixplain.modules.model.utility_model import UtilityModel
from aixplain.modules.model.utility_model import UtilityModelInput
from aixplain.enums import DataType, Function, FunctionType, Language, OwnershipType, Supplier, SortBy, SortOrder, AssetStatus
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from datetime import datetime
from typing import Dict, Union, List, Optional, Tuple
from urllib.parse import urljoin
import requests


def create_model_from_response(response: Dict) -> Model:
    """Convert API response JSON into appropriate Model object.

    This function creates the correct type of Model object (Model, LLM, IndexModel,
    Integration, ConnectionTool, MCPConnection, or UtilityModel) based on the
    function type and parameters in the response.

    Args:
        response (Dict): API response containing model information including:
            - id: Model identifier
            - name: Model name
            - function: Function type information
            - params: Model parameters
            - api_key: Optional API key
            - attributes: Optional model attributes
            - code: Optional model code
            - version: Optional version information

    Returns:
        Model: Instantiated model object of the appropriate subclass based on
        the function type.

    Raises:
        Exception: If required code is not found for UtilityModel.
    """
    if "api_key" not in response:
        response["api_key"] = config.TEAM_API_KEY

    parameters = {}
    if "params" in response:
        for param in response["params"]:
            if "language" in param["name"]:
                parameters[param["name"]] = [w["value"] for w in param["values"]]
            else:
                values = [w["value"] for w in param["defaultValues"]]
                if len(values) > 0:
                    parameters[param["name"]] = values

    additional_kwargs = {}
    attributes = response.get("attributes", None)
    if attributes:
        embedding_model = next(
            (item.get("code") for item in attributes if item.get("name") == "embeddingmodel" and "code" in item), None
        )
        if embedding_model:
            additional_kwargs["embedding_model"] = embedding_model
        embedding_size = next(
            (item.get("value") for item in attributes if item.get("name") == "embeddingSize" and "value" in item), None
        )
        if embedding_size:
            additional_kwargs["embedding_size"] = embedding_size

    function_id = response["function"]["id"]
    function = Function(function_id)
    function_type = FunctionType(response.get("functionType", "ai"))
    function_input_params, function_output_params = function.get_input_output_params()
    model_params = {param["name"]: param for param in response["params"]}

    code = response.get("code", "")

    inputs, temperature = [], None
    input_params, output_params = function_input_params, function_output_params

    ModelClass = Model

    if function == Function.TEXT_GENERATION:
        ModelClass = LLM
        f = [p for p in response.get("params", []) if p["name"] == "temperature"]
        if len(f) > 0 and len(f[0].get("defaultValues", [])) > 0:
            temperature = float(f[0]["defaultValues"][0]["value"])
    elif function == Function.SEARCH:
        ModelClass = IndexModel
    elif function_type == FunctionType.INTEGRATION:
        ModelClass = Integration
    elif function_type == FunctionType.CONNECTION:
        ModelClass = ConnectionTool
    elif function_type == FunctionType.MCP_CONNECTION:
        ModelClass = MCPConnection
    elif function == Function.UTILITIES:
        ModelClass = UtilityModel
        inputs = [
            UtilityModelInput(name=param["name"], description=param.get("description", ""), type=DataType(param["dataType"]))
            for param in response["params"]
        ]
        input_params = model_params
        if not code:
            if "version" in response and response["version"]:
                version_link = response["version"]["id"]
                if version_link:
                    try:
                        version_content = requests.get(version_link).text
                        code = version_content
                    except Exception:
                        code = ""
            else:
                raise Exception("Utility Model Error: Code not found")

    status = AssetStatus(response.get("status", AssetStatus.DRAFT.value))

    created_at = None
    if "createdAt" in response and response["createdAt"]:
        created_at = datetime.fromisoformat(response["createdAt"].replace("Z", "+00:00"))

    return ModelClass(
        response["id"],
        response["name"],
        description=response.get("description", ""),
        code=code if code else "",
        supplier=response["supplier"],
        api_key=response["api_key"],
        cost=response["pricing"],
        function=function,
        created_at=created_at,
        parameters=parameters,
        input_params=input_params,
        output_params=output_params,
        model_params=model_params,
        is_subscribed=True if "subscription" in response else False,
        version=response["version"]["id"],
        inputs=inputs,
        temperature=temperature,
        supports_streaming=response.get("supportsStreaming", False),
        status=status,
        function_type=function_type,
        attributes=attributes,
        **additional_kwargs,
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
    api_key: Optional[str] = None,
) -> List[Model]:
    """Retrieve a paginated list of models with specified filters.

    This function fetches a page of models from the aiXplain platform, applying
    various filters such as function type, suppliers, languages, and ownership.

    Args:
        query: Search query string to filter models.
        page_number (int): Page number to retrieve (0-based).
        page_size (int): Number of models per page.
        function (Function): Function type to filter models by.
        suppliers (Union[Supplier, List[Supplier]]): Single supplier or list of
            suppliers to filter models by.
        source_languages (Union[Language, List[Language]]): Source language(s)
            supported by the models.
        target_languages (Union[Language, List[Language]]): Target language(s)
            for translation models.
        is_finetunable (bool, optional): Filter for fine-tunable models.
            Defaults to None.
        ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
            Filter by model ownership type. Defaults to None.
        sort_by (Optional[SortBy], optional): Field to sort results by.
            Defaults to None.
        sort_order (SortOrder, optional): Sort direction (ascending/descending).
            Defaults to SortOrder.ASCENDING.
        api_key (Optional[str], optional): API key for authentication.
            Defaults to None, using the configured TEAM_API_KEY.

    Returns:
        Tuple[List[Model], int]: A tuple containing:
            - List of Model objects matching the filters
            - Total number of models matching the filters

    Raises:
        Exception: If the API request fails or returns an error.
    """
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
    """Retrieve multiple models by their IDs.

    This function fetches multiple models from the aiXplain platform in a single
    request using their unique identifiers.

    Args:
        model_ids (List[str]): List of model IDs to retrieve.
        api_key (Optional[str], optional): API key for authentication.
            Defaults to None, using the configured TEAM_API_KEY.

    Returns:
        List[Model]: List of Model objects corresponding to the provided IDs.
            Each model will be instantiated as the appropriate subclass based
            on its function type.

    Raises:
        Exception: If the API request fails or returns an error, including
            cases where models are not found or access is denied.
    """
    from aixplain.factories.model_factory.utils import create_model_from_response

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

        def process_items(items):
            """Helper function to process model items and add API key"""
            for item in items:
                item["api_key"] = config.TEAM_API_KEY
                if api_key is not None:
                    item["api_key"] = api_key
                models.append(create_model_from_response(item))

        # Check if pagination is needed ( pageNumber: 0 indicates pagination required)
        if "pageTotal" in resp:
            # Handle paginated response - need to fetch all pages
            page_number = 1
            total_fetched = resp.get("pageTotal", 0)
            page_items = resp.get("items", [])
            total_items = resp.get("total", 0)
            process_items(page_items)

            while True:
                # Make request for current page
                paginated_url = urljoin(config.BACKEND_URL, f"sdk/models?ids={','.join(model_ids)}&pageNumber={page_number}")
                logging.info(f"Fetching page {page_number} - {paginated_url}")
                page_r = _request_with_retry("get", paginated_url, headers=headers)
                page_resp = page_r.json()

                if not (200 <= page_r.status_code < 300):
                    error_message = f"Model GET Error: Failed to retrieve models page {page_number}. Status Code: {page_r.status_code}. Error: {page_resp}"
                    logging.error(error_message)
                    raise Exception(error_message)

                # Process items from current page
                page_items = page_resp.get("items", [])
                if not page_items:
                    break

                process_items(page_items)
                total_fetched += len(page_items)

                if total_fetched >= total_items:
                    break

                page_number += 1
        else:
            # Handle non-paginated response (original logic)
            process_items(resp["items"])

        return models
    else:
        error_message = f"Model GET Error: Failed to retrieve models {model_ids}. Status Code: {r.status_code}. Error: {resp}"
        logging.error(error_message)
        raise Exception(error_message)
