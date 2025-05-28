import logging
import requests

from aixplain.enums import Function, FunctionType, AssetStatus, DataType
from aixplain.modules.model import Model
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.model.index_model import IndexModel
from aixplain.modules.model.connector import ConnectorModel
from aixplain.modules.model.connection import ConnectionModel
from aixplain.modules.model.utility_model import ScriptModel
from aixplain.modules.model.utility_model import UtilityModelInput
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.asset_cache import AssetCache
from datetime import datetime
from urllib.parse import urljoin
from typing import Dict, Optional, Text


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
            else:
                values = [w["value"] for w in param["defaultValues"]]
                if len(values) > 0:
                    parameters[param["name"]] = values

    additional_kwargs = {}
    attributes = response.get("attributes", None)
    if attributes:
        embedding_model = next((item["code"] for item in attributes if item["name"] == "embeddingmodel"), None)
        if embedding_model:
            additional_kwargs["embedding_model"] = embedding_model
        embedding_size = next((item["value"] for item in attributes if item["name"] == "embeddingSize"), None)
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
    elif function_type == FunctionType.CONNECTOR:
        ModelClass = ConnectorModel
    elif function_type == FunctionType.CONNECTION:
        ModelClass = ConnectionModel
    elif function == Function.UTILITIES:
        ModelClass = ScriptModel
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
        **additional_kwargs,
    )


class ModelGetterMixin:
    @classmethod
    def get(cls, model_id: Text, api_key: Optional[Text] = None, use_cache: bool = False) -> Model:
        """Create a 'Model' object from model id"""
        cache = AssetCache(Model)

        if use_cache:
            if cache.has_valid_cache():
                cached_model = cache.store.data.get(model_id)
                if cached_model:
                    return cached_model
                logging.info("Model not found in valid cache, fetching individually...")
                model = cls._fetch_model_by_id(model_id, api_key)
                cache.add(model)
                return model
            else:
                try:
                    model_list_resp = cls.list(model_ids=None, api_key=api_key)
                    models = model_list_resp["results"]
                    cache.add_list(models)
                    for model in models:
                        if model.id == model_id:
                            return model
                except Exception as e:
                    logging.error(f"Error fetching model list: {e}")
                    raise e

        logging.info("Fetching model directly without cache...")
        model = cls._fetch_model_by_id(model_id, api_key)
        cache.add(model)
        return model

    @classmethod
    def _fetch_model_by_id(cls, model_id: Text, api_key: Optional[Text] = None) -> Model:
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/models/{model_id}")
            headers = {
                "Authorization": f"Token {api_key or config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for GET Model  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            if resp and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = f"Model Creation: Status {status_code} - {resp['message']}"
            else:
                message = "Model Creation: Unspecified Error"
            logging.error(message)
            raise Exception(message)

        if 200 <= r.status_code < 300:
            resp["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                resp["api_key"] = api_key

            model = create_model_from_response(resp)
            logging.info(f"Model Creation: Model {model_id} instantiated.")
            return model
        else:
            error_message = f"Model GET Error: Failed to retrieve model {model_id}. Status Code: {r.status_code}. Error: {resp}"
            logging.error(error_message)
            raise Exception(error_message)
