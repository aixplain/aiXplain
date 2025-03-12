__author__ = "lucaspavanelli"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: June 4th 2024
Description:
    Large Language Model Class
"""
import time
import logging
import traceback
from aixplain.enums import Function, Supplier
from aixplain.modules.model import Model
from aixplain.modules.model.utils import build_payload, call_run_endpoint, build_fallback_order
from aixplain.utils import config
from typing import Union, Optional, List, Text, Dict
from aixplain.modules.asset_router import AssetRouter
from aixplain.modules.model.response import ModelResponse
from aixplain.enums.response_status import ResponseStatus


class LLM(Model):
    """Ready-to-use LLM model. This model can be run in both synchronous and asynchronous manner.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Function, optional): model AI function. Defaults to None.
        is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
        cost (Dict, optional): model price. Defaults to None.
        temperature (float, optional): model temperature. Defaults to 0.001.
        fallback (bool, optional): If True, the model will use fallback models if the main model fails. If no fallback models are provided, the backup model will be chosen by aiXplain. Defaults to False.
        fallback_models (Optional[List[Text]], optional): List of fallback models to be used if the main model fails. Defaults to None.
        **additional_info: Any additional Model info to be saved
    """

    _fallback_order: Optional[AssetRouter] = None

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        temperature: float = 0.001,
        allow_fallback: bool = False,
        fallback_order: Optional[Union[AssetRouter, List[Union[Model, Text]]]] = None,
        **additional_info,
    ) -> None:
        """LLM Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            temperature (float, optional): model temperature. Defaults to 0.001.
            allow_fallback (bool, optional): If True, the model will use fallback models if the main model fails. If no fallback models are provided, the backup model will be chosen by aiXplain. Defaults to False.
            fallback_order (Optional[List[Text]], optional): List of fallback models to be used if the main model fails. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        assert function == Function.TEXT_GENERATION, "LLM only supports large language models (i.e. text generation function)"
        super().__init__(
            id=id,
            name=name,
            description=description,
            supplier=supplier,
            version=version,
            cost=cost,
            function=function,
            is_subscribed=is_subscribed,
            api_key=api_key,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.temperature = temperature
        self.allow_fallback = allow_fallback
        self._fallback_order = build_fallback_order(fallback_order)

    def run(
        self,
        data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 128,
        top_p: float = 1.0,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
    ) -> ModelResponse:
        """Synchronously running a Large Language Model (LLM) model.

        Args:
            data (Union[Text, Dict]): Text to LLM or last user utterance of a conversation.
            context (Optional[Text], optional): System message. Defaults to None.
            prompt (Optional[Text], optional): Prompt Message which comes on the left side of the last utterance. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format ([{ "role": "assistant", "content": "Hello, world!"}]). Defaults to None.
            temperature (Optional[float], optional): LLM temperature. Defaults to None.
            max_tokens (int, optional): Maximum Generation Tokens. Defaults to 128.
            top_p (float, optional): Top P. Defaults to 1.0.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to None.
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.

        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        parameters = parameters or {}

        if isinstance(data, dict):
            parameters = {**data, **parameters}
            data = data.get("data", "")

        parameters.setdefault("context", context)
        parameters.setdefault("prompt", prompt)
        parameters.setdefault("history", history)
        parameters.setdefault("temperature", temperature if temperature is not None else self.temperature)
        parameters.setdefault("max_tokens", max_tokens)
        parameters.setdefault("top_p", top_p)
        if self.allow_fallback is True:
            if "options" not in parameters:
                parameters["options"] = {}
            parameters["options"]["failover"] = self.allow_fallback
            parameters["options"]["failoverList"] = [asset.id for asset in self.fallback_order.assets]

        payload = build_payload(data=data, parameters=parameters)
        logging.info(payload)
        url = f"{self.url}/{self.id}".replace("/api/v1/execute", "/api/v2/execute")
        logging.debug(f"Model Run Sync: Start service for {name} - {url}")
        response = call_run_endpoint(payload=payload, url=url, api_key=self.api_key)
        if response["status"] == "IN_PROGRESS":
            try:
                poll_url = response["url"]
                end = time.time()
                return self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)

            except Exception as e:
                msg = f"Error in request for {name} - {traceback.format_exc()}"
                logging.error(f"Model Run: Error in running for {name}: {e}")
                end = time.time()
                response = {"status": "FAILED", "error": msg, "elapsed_time": end - start}
        return ModelResponse(
            status=response.pop("status", ResponseStatus.FAILED),
            data=response.pop("data", ""),
            details=response.pop("details", {}),
            completed=response.pop("completed", False),
            error_message=response.pop("error_message", ""),
            used_credits=response.pop("usedCredits", 0),
            run_time=response.pop("runTime", 0),
            usage=response.pop("usage", None),
            **response,
        )

    def run_async(
        self,
        data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 128,
        top_p: float = 1.0,
        name: Text = "model_process",
        parameters: Optional[Dict] = None,
    ) -> ModelResponse:
        """Runs asynchronously a model call.

        Args:
            data (Union[Text, Dict]): Text to LLM or last user utterance of a conversation.
            context (Optional[Text], optional): System message. Defaults to None.
            prompt (Optional[Text], optional): Prompt Message which comes on the left side of the last utterance. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format ([{ "role": "assistant", "content": "Hello, world!"}]). Defaults to None.
            temperature (Optional[float], optional): LLM temperature. Defaults to None.
            max_tokens (int, optional): Maximum Generation Tokens. Defaults to 128.
            top_p (float, optional): Top P. Defaults to 1.0.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to None.
        Returns:
            dict: polling URL in response
        """
        url = f"{self.url}/{self.id}"
        logging.debug(f"Model Run Async: Start service for {name} - {url}")
        parameters = parameters or {}

        if isinstance(data, dict):
            parameters = {**data, **parameters}
            data = data.get("data", "")

        parameters.setdefault("context", context)
        parameters.setdefault("prompt", prompt)
        parameters.setdefault("history", history)
        parameters.setdefault("temperature", temperature if temperature is not None else self.temperature)
        parameters.setdefault("max_tokens", max_tokens)
        parameters.setdefault("top_p", top_p)
        if self.allow_fallback is True:
            if "options" not in parameters:
                parameters["options"] = {}
            parameters["options"]["failover"] = self.allow_fallback
            parameters["options"]["failoverList"] = [asset.id for asset in self.fallback_order.assets]

        payload = build_payload(data=data, parameters=parameters)
        response = call_run_endpoint(payload=payload, url=url, api_key=self.api_key)
        return ModelResponse(
            status=response.pop("status", ResponseStatus.FAILED),
            data=response.pop("data", ""),
            details=response.pop("details", {}),
            completed=response.pop("completed", False),
            error_message=response.pop("error_message", ""),
            url=response.pop("url", None),
            **response,
        )

    @property
    def fallback_order(self) -> Optional[AssetRouter]:
        return self._fallback_order

    @fallback_order.setter
    def fallback_order(self, value: Optional[Union[AssetRouter, List[Union[Model, Text]]]]) -> None:
        self._fallback_order = build_fallback_order(value)
