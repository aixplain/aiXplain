import logging

from aixplain.factories.model_factory.utils import create_model_from_response
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.asset_cache import AssetCache
from urllib.parse import urljoin
from typing import Optional, Text


class ModelGetterMixin:
    @classmethod
    def get(cls, model_id: Text, api_key: Optional[Text] = None, use_cache: bool = False) -> Model:
        """Create a 'Model' object from model id"""
        model_id = model_id.replace("/", "%2F")
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
