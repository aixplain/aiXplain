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
import json
import logging
import traceback
from aixplain.enums import Function, Supplier
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
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
        try:
            response = self.run_async(
                data,
                name=name,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                context=context,
                prompt=prompt,
                history=history,
                parameters=parameters,
            )
            if response["status"] == "FAILED":
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            response = self.sync_poll(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            return response
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"LLM Run: Error in running for {name}: {e}")
            end = time.time()
            return {"status": "FAILED", "error": msg, "elapsed_time": end - start}

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
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        from aixplain.factories.file_factory import FileFactory

        data = FileFactory.to_link(data)
        if isinstance(data, dict):
            payload = data
        else:
            try:
                payload = json.loads(data)
                if isinstance(payload, dict) is False:
                    if isinstance(payload, int) is True or isinstance(payload, float) is True:
                        payload = str(payload)
                    payload = {"data": payload}
            except Exception:
                payload = {"data": data}
        parameters.update(
            {
                "context": payload["context"] if "context" in payload else context,
                "prompt": payload["prompt"] if "prompt" in payload else prompt,
                "history": payload["history"] if "history" in payload else history,
                "temperature": payload["temperature"] if "temperature" in payload else temperature,
                "max_tokens": payload["max_tokens"] if "max_tokens" in payload else max_tokens,
                "top_p": payload["top_p"] if "top_p" in payload else top_p,
            }
        )
        payload.update(parameters)
        payload = json.dumps(payload)

        call_url = f"{self.url}/{self.id}"
        r = _request_with_retry("post", call_url, headers=headers, data=payload)
        logging.info(f"Model Run Async: Start service for {name} - {self.url} - {payload} - {headers}")

        resp = None
        try:
            if 200 <= r.status_code < 300:
                resp = r.json()
                logging.info(f"Result of request for {name} - {r.status_code} - {resp}")
                poll_url = resp["data"]
                response = {"status": "IN_PROGRESS", "url": poll_url}
            else:
                if r.status_code == 401:
                    error = "Unauthorized API key: Please verify the spelling of the API key and its current validity."
                elif 460 <= r.status_code < 470:
                    error = "Subscription-related error: Please ensure that your subscription is active and has not expired."
                elif 470 <= r.status_code < 480:
                    error = "Billing-related error: Please ensure you have enough credits to run this model. "
                elif 480 <= r.status_code < 490:
                    error = "Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access."
                elif 490 <= r.status_code < 500:
                    resp = r.json()
                    error = f"{resp}"
                else:
                    status_code = str(r.status_code)
                    error = (
                        f"Status {status_code}: Unspecified error: An unspecified error occurred while processing your request."
                    )
                response = {"status": "FAILED", "error_message": error}
                logging.error(f"Error in request for {name} - {r.status_code}: {error}")
        except Exception:
            response = {"status": "FAILED"}
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Model Run Async: Error in running for {name}: {resp}")
            if resp is not None:
                response["error"] = msg
        return response
