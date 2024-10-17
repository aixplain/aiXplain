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
from aixplain.modules.model.utils import build_payload, call_run_endpoint
from aixplain.utils import config
from typing import Union, Optional, List, Text, Dict


class LLM(Model):
    """Ready-to-use LLM model. This model can be run in both synchronous and asynchronous manner.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        url (Text, optional): endpoint of the model. Defaults to config.MODELS_RUN_URL.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Text, optional): model AI function. Defaults to None.
        url (str): URL to run the model.
        backend_url (str): URL of the backend.
        pricing (Dict, optional): model price. Defaults to None.
        **additional_info: Any additional Model info to be saved
    """

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

    def run(
        self,
        data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.001,
        max_tokens: int = 128,
        top_p: float = 1.0,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Dict = {},
        wait_time: float = 0.5,
    ) -> Dict:
        """Synchronously running a Large Language Model (LLM) model.

        Args:
            data (Union[Text, Dict]): Text to LLM or last user utterance of a conversation.
            context (Optional[Text], optional): System message. Defaults to None.
            prompt (Optional[Text], optional): Prompt Message which comes on the left side of the last utterance. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format ([{ "role": "assistant", "content": "Hello, world!"}]). Defaults to None.
            temperature (float, optional): LLM temperature. Defaults to 0.001.
            max_tokens (int, optional): Maximum Generation Tokens. Defaults to 128.
            top_p (float, optional): Top P. Defaults to 1.0.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.

        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        parameters.update(
            {
                "context": parameters["context"] if "context" in parameters else context,
                "prompt": parameters["prompt"] if "prompt" in parameters else prompt,
                "history": parameters["history"] if "history" in parameters else history,
                "temperature": parameters["temperature"] if "temperature" in parameters else temperature,
                "max_tokens": parameters["max_tokens"] if "max_tokens" in parameters else max_tokens,
                "top_p": parameters["top_p"] if "top_p" in parameters else top_p,
            }
        )
        payload = build_payload(data=data, parameters=parameters)
        url = f"{self.url}/{self.id}".replace("/api/v1/execute", "/api/v2/execute")
        logging.debug(f"Model Run Sync: Start service for {name} - {url}")
        response = call_run_endpoint(payload=payload, url=url, api_key=self.api_key)
        if response["status"] == "IN_PROGRESS":
            try:
                poll_url = response["url"]
                end = time.time()
                response = self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            except Exception as e:
                msg = f"Error in request for {name} - {traceback.format_exc()}"
                logging.error(f"Model Run: Error in running for {name}: {e}")
                end = time.time()
                response = {"status": "FAILED", "error": msg, "elapsed_time": end - start}
        return response

    def run_async(
        self,
        data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: float = 0.001,
        max_tokens: int = 128,
        top_p: float = 1.0,
        name: Text = "model_process",
        parameters: Dict = {},
    ) -> Dict:
        """Runs asynchronously a model call.

        Args:
            data (Union[Text, Dict]): Text to LLM or last user utterance of a conversation.
            context (Optional[Text], optional): System message. Defaults to None.
            prompt (Optional[Text], optional): Prompt Message which comes on the left side of the last utterance. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format ([{ "role": "assistant", "content": "Hello, world!"}]). Defaults to None.
            temperature (float, optional): LLM temperature. Defaults to 0.001.
            max_tokens (int, optional): Maximum Generation Tokens. Defaults to 128.
            top_p (float, optional): Top P. Defaults to 1.0.
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".

        Returns:
            dict: polling URL in response
        """
        url = f"{self.url}/{self.id}"
        logging.debug(f"Model Run Async: Start service for {name} - {url}")
        parameters.update(
            {
                "context": parameters["context"] if "context" in parameters else context,
                "prompt": parameters["prompt"] if "prompt" in parameters else prompt,
                "history": parameters["history"] if "history" in parameters else history,
                "temperature": parameters["temperature"] if "temperature" in parameters else temperature,
                "max_tokens": parameters["max_tokens"] if "max_tokens" in parameters else max_tokens,
                "top_p": parameters["top_p"] if "top_p" in parameters else top_p,
            }
        )
        payload = build_payload(data=data, parameters=parameters)
        response = call_run_endpoint(payload=payload, url=url, api_key=self.api_key)
        return response
