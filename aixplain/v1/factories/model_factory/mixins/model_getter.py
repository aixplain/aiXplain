"""Model getter mixin providing model retrieval functionality.

This module contains the ModelGetterMixin class which provides methods for retrieving
model instances from the backend by ID or name, with support for caching.
"""

import logging

from aixplain.factories.model_factory.utils import create_model_from_response
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.asset_cache import AssetCache
from urllib.parse import quote, urljoin
from typing import Optional, Text


class ModelGetterMixin:
    """Mixin class providing model retrieval functionality.

    This mixin provides methods for retrieving model instances from the backend,
    with support for caching to improve performance.
    """

    @classmethod
    def get(
        cls,
        model_id: Optional[Text] = None,
        name: Optional[Text] = None,
        api_key: Optional[Text] = None,
        use_cache: bool = False,
    ) -> Model:
        """Retrieve a model instance by its ID or name.

        This method attempts to retrieve a model from the cache if enabled,
        falling back to fetching from the backend if necessary.

        Args:
            model_id (Optional[Text], optional): ID of the model to retrieve.
            name (Optional[Text], optional): Name of the model to retrieve.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.
            use_cache (bool, optional): Whether to use the on-disk model cache.
                Defaults to False. When False, the cache is neither read nor
                written -- opting out of caching also opts out of persisting
                anything about the model (BUG-940).

        Returns:
            Model: Retrieved model instance.

        Raises:
            Exception: If the model cannot be retrieved or doesn't exist.
            ValueError: If neither model_id nor name is provided, or if both are provided.
        """
        # Validate that exactly one parameter is provided
        if not (model_id or name) or (model_id and name):
            raise ValueError("Must provide exactly one of 'model_id' or 'name'")

        # If name is provided, fetch by name (caching not supported for name-based queries)
        if name:
            return cls._fetch_model_by_name(name, api_key)

        # Continue with existing ID-based logic. The id is used verbatim as the
        # cache key -- percent-escaping is a URL concern and is applied where
        # the request is built. Escaping here keyed lookups on
        # "a%2Fb%2Fc" while every write keyed on the raw id, so slug ids
        # ("openai/gpt-4o-mini/openai") never hit the cache (BUG-940).
        if api_key is None:
            api_key = config.TEAM_API_KEY

        if use_cache:
            # Shared instance: building one reads and deserializes the whole
            # cache file, so a per-call instance made every get() O(cache size).
            cache = AssetCache.shared(Model)
            try:
                cached_model = cache.get(model_id)
                if cached_model is not None:
                    # The cache never stores a credential, so stamp the one this
                    # call is authorized with rather than leaking another
                    # caller's key or a stale configured one.
                    cached_model.api_key = api_key
                    return cached_model

                if not cache.has_valid_cache():
                    model_list_resp = cls.list(model_ids=None, api_key=api_key)
                    models = model_list_resp["results"]
                    # Additive: this is one page of the account's models, not
                    # the authoritative cache contents, so it must not discard
                    # entries this process never saw.
                    cache.add_many(models)
                    for model in models:
                        if model.id == model_id:
                            return model

                logging.info("Model not found in valid cache, fetching individually...")
                model = cls._fetch_model_by_id(model_id, api_key)
                # Key on the requested id: the backend may answer a slug with a
                # canonical id, and the next lookup will use the slug again.
                cache.add(model, key=model_id)
                return model
            except Exception as e:
                logging.warning(f"Cache lookup failed, falling back to direct fetch: {e}")

            # The cache was unusable, but the result is still worth keeping:
            # otherwise a failing bulk listing is re-attempted, with retries,
            # on every single call.
            model = cls._fetch_model_by_id(model_id, api_key)
            try:
                cache.add(model, key=model_id)
            except Exception as e:
                logging.warning(f"Could not cache directly fetched model: {e}")
            return model

        logging.info("Fetching model directly without cache...")
        return cls._fetch_model_by_id(model_id, api_key)

    @classmethod
    def _fetch_model_by_name(cls, name: Text, api_key: Optional[Text] = None) -> Model:
        """Fetch a model directly from the backend by its name.

        This internal method handles the direct API communication to retrieve
        a model's details from the backend using the model's name.

        Args:
            name (Text): Name of the model to fetch.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Model: Fetched model instance.

        Raises:
            Exception: If the API request fails or returns an error.
        """
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/models/by-name/{name}")
            headers = {
                "Authorization": f"Token {api_key or config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for GET Model by name - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            if resp and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = f"Model Get by Name: Status {status_code} - {resp['message']}"
            else:
                message = "Model Get by Name: Unspecified Error"
            logging.error(message)
            raise Exception(message)

        if 200 <= r.status_code < 300:
            resp["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                resp["api_key"] = api_key

            model = create_model_from_response(resp)
            logging.info(f"Model Get by Name: Model {name} instantiated.")
            return model
        else:
            error_message = (
                f"Model GET by Name Error: Failed to retrieve model {name}. Status Code: {r.status_code}. Error: {resp}"
            )
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def _fetch_model_by_id(cls, model_id: Text, api_key: Optional[Text] = None) -> Model:
        """Fetch a model directly from the backend by its ID.

        This internal method handles the direct API communication to retrieve
        a model's details from the backend.

        Args:
            model_id (Text): ID of the model to fetch.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Model: Fetched model instance.

        Raises:
            Exception: If the API request fails or returns an error.
        """
        resp = None
        try:
            # Escape here rather than at the caller: a slug id must not be read
            # as extra path segments, but the unescaped id is what identifies
            # the model everywhere else, the cache included.
            url = urljoin(cls.backend_url, f"sdk/models/{quote(model_id, safe='')}")
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
            error_message = (
                f"Model GET Error: Failed to retrieve model {model_id}. Status Code: {r.status_code}. Error: {resp}"
            )
            logging.error(error_message)
            raise Exception(error_message)
