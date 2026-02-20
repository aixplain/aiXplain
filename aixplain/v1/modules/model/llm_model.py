"""Copyright 2024 The aiXplain SDK authors.

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

__author__ = "lucaspavanelli"
import time
import logging
import traceback
from aixplain.enums import Function, Supplier, FunctionType
from aixplain.modules.model import Model
from aixplain.modules.model.model_response_streamer import ModelResponseStreamer
from aixplain.modules.model.utils import build_payload, call_run_endpoint
from aixplain.utils import config
from typing import Union, Optional, List, Text, Dict
from aixplain.modules.model.response import ModelResponse
from aixplain.enums.response_status import ResponseStatus


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
        function_type (FunctionType, optional): type of the function. Defaults to FunctionType.AI.
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
        temperature: Optional[float] = None,
        function_type: Optional[FunctionType] = FunctionType.AI,
        **additional_info,
    ) -> None:
        """Initialize a new LLM instance.

        Args:
            id (Text): ID of the LLM model.
            name (Text): Name of the LLM model.
            description (Text, optional): Description of the model. Defaults to "".
            api_key (Text, optional): API key for the model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the model. Defaults to "aiXplain".
            version (Text, optional): Version of the model. Defaults to "1.0".
            function (Function, optional): Model's AI function. Must be Function.TEXT_GENERATION.
            is_subscribed (bool, optional): Whether the user is subscribed. Defaults to False.
            cost (Dict, optional): Cost of the model. Defaults to None.
            temperature (Optional[float], optional): Default temperature for text generation. Defaults to None.
            function_type (FunctionType, optional): Type of the function. Defaults to FunctionType.AI.
            **additional_info: Any additional model info to be saved.

        Raises:
            AssertionError: If function is not Function.TEXT_GENERATION.
        """
        assert function == Function.TEXT_GENERATION, (
            "LLM only supports large language models (i.e. text generation function)"
        )
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
            function_type=function_type,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.temperature = temperature

    def run(
        self,
        data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 128,
        top_p: Optional[float] = None,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False,
        response_format: Optional[Text] = None,
    ) -> Union[ModelResponse, ModelResponseStreamer]:
        """Run the LLM model synchronously to generate text.

        This method runs the LLM model to generate text based on the provided input.
        It supports both single-turn and conversational interactions, with options
        for streaming responses.

        Args:
            data (Text): The input text or last user utterance for text generation.
            context (Optional[Text], optional): System message or context for the model.
                Defaults to None.
            prompt (Optional[Text], optional): Prompt template or prefix to prepend to
                the input. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format
                (e.g., [{"role": "assistant", "content": "Hello!"}, ...]). Defaults to None.
            temperature (Optional[float], optional): Sampling temperature for text generation.
                Higher values make output more random. If None, uses the model's default.
                Defaults to None.
            max_tokens (int, optional): Maximum number of tokens to generate.
                Defaults to 128.
            top_p (Optional[float], optional): Nucleus sampling parameter. Only tokens with cumulative
                probability < top_p are considered. Defaults to None.
            name (Text, optional): Identifier for this model run. Useful for logging.
                Defaults to "model_process".
            timeout (float, optional): Maximum time in seconds to wait for completion.
                Defaults to 300.
            parameters (Optional[Dict], optional): Additional model-specific parameters.
                Defaults to None.
            wait_time (float, optional): Time in seconds between polling attempts.
                Defaults to 0.5.
            stream (bool, optional): Whether to stream the model's output tokens.
                Defaults to False.
            response_format (Optional[Union[str, dict, BaseModel]], optional):
                Specifies the desired output structure or format of the model’s response.

        Returns:
            Union[ModelResponse, ModelResponseStreamer]: If stream=False, returns a ModelResponse
                containing the complete generated text and metadata. If stream=True, returns
                a ModelResponseStreamer that yields tokens as they're generated.
        """
        start = time.time()
        parameters = parameters or {}

        if isinstance(data, dict):
            parameters = {**data, **parameters}
            data = data.get("data", "")

        parameters.setdefault("context", context)
        parameters.setdefault("prompt", prompt)
        parameters.setdefault("history", history)
        temp_value = temperature if temperature is not None else self.temperature
        if temp_value is not None:
            parameters.setdefault("temperature", temp_value)
        parameters.setdefault("max_tokens", max_tokens)
        if top_p is not None:
            parameters.setdefault("top_p", top_p)
        parameters.setdefault("response_format", response_format)

        if stream:
            return self.run_stream(data=data, parameters=parameters)

        payload = build_payload(data=data, parameters=parameters)
        logging.info(payload)
        url = f"{self.url}/{self.id}".replace("/api/v1/execute", "/api/v2/execute")
        logging.debug(f"Model Run Sync: Start service for {name} - {url} - {payload}")
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
            error_code=response.get("error_code", None),
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
        top_p: Optional[float] = None,
        name: Text = "model_process",
        parameters: Optional[Dict] = None,
        response_format: Optional[Text] = None,
    ) -> ModelResponse:
        """Run the LLM model asynchronously to generate text.

        This method starts an asynchronous text generation task and returns immediately
        with a response containing a polling URL. The actual result can be retrieved
        later using the polling URL.

        Args:
            data (Text): The input text or last user utterance for text generation.
            context (Optional[Text], optional): System message or context for the model.
                Defaults to None.
            prompt (Optional[Text], optional): Prompt template or prefix to prepend to
                the input. Defaults to None.
            history (Optional[List[Dict]], optional): Conversation history in OpenAI format
                (e.g., [{"role": "assistant", "content": "Hello!"}, ...]). Defaults to None.
            temperature (Optional[float], optional): Sampling temperature for text generation.
                Higher values make output more random. If None, uses the model's default.
                Defaults to None.
            max_tokens (int, optional): Maximum number of tokens to generate.
                Defaults to 128.
            top_p (Optional[float], optional): Nucleus sampling parameter. Only tokens with cumulative
                probability < top_p are considered. Defaults to None.
            name (Text, optional): Identifier for this model run. Useful for logging.
                Defaults to "model_process".
            parameters (Optional[Dict], optional): Additional model-specific parameters.
                Defaults to None.
            response_format (Optional[Text], optional): Desired output format specification.
                Defaults to None.

        Returns:
            ModelResponse: A response object containing:
                - status (ResponseStatus): Status of the request (e.g., IN_PROGRESS)
                - url (str): URL to poll for the final result
                - data (str): Empty string (result not available yet)
                - details (Dict): Additional response details
                - completed (bool): False (task not completed yet)
                - error_message (str): Error message if request failed
                Other fields may be present depending on the response.
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
        temp_value = temperature if temperature is not None else self.temperature
        if temp_value is not None:
            parameters.setdefault("temperature", temp_value)
        parameters.setdefault("max_tokens", max_tokens)
        if top_p is not None:
            parameters.setdefault("top_p", top_p)
        parameters.setdefault("response_format", response_format)
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
