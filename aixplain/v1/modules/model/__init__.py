"""Model module for aiXplain SDK.

This module provides the Model class and related functionality for working with
AI models in the aiXplain platform, including model execution, parameter management,
and status tracking.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: September 1st 2022
"""

__author__ = "lucaspavanelli"
import time
import logging
import traceback
from aixplain.enums import Supplier, Function, FunctionType
from aixplain.modules.asset import Asset
from aixplain.modules.model.model_response_streamer import ModelResponseStreamer
from aixplain.modules.model.utils import build_payload, call_run_endpoint
from aixplain.utils import config
from urllib.parse import urljoin
from aixplain.utils.request_utils import _request_with_retry
from typing import Union, Optional, Text, Dict
from datetime import datetime
from aixplain.modules.model.response import ModelResponse
from aixplain.enums.response_status import ResponseStatus
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.enums import AssetStatus


class Model(Asset):
    """A ready-to-use AI model that can be executed synchronously or asynchronously.

    This class represents a deployable AI model in the aiXplain platform. It provides
    functionality for model execution, parameter management, and status tracking.
    Models can be run with both synchronous and asynchronous APIs, and some models
    support streaming responses.

    Attributes:
        id (Text): ID of the model.
        name (Text): Name of the model.
        description (Text): Detailed description of the model's functionality.
        api_key (Text): Authentication key for API access.
        url (Text): Endpoint URL for model execution.
        supplier (Union[Dict, Text, Supplier, int]): Provider/creator of the model.
        version (Text): Version identifier of the model.
        function (Function): The AI function this model performs.
        backend_url (str): Base URL for the backend API.
        cost (Dict): Pricing information for model usage.
        input_params (ModelParameters): Parameters accepted by the model.
        output_params (Dict): Description of model outputs.
        model_params (ModelParameters): Configuration parameters for model behavior.
        supports_streaming (bool): Whether the model supports streaming responses.
        function_type (FunctionType): Category of function (AI, UTILITY, etc.).
        is_subscribed (bool): Whether the user has an active subscription.
        created_at (datetime): When the model was created.
        status (AssetStatus): Current status of the model.
        additional_info (dict): Additional model metadata.
    """

    def __init__(
        self,
        id: Text,
        name: Text = "",
        description: Text = "",
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        created_at: Optional[datetime] = None,
        input_params: Optional[Dict] = None,
        output_params: Optional[Dict] = None,
        model_params: Optional[Dict] = None,
        supports_streaming: bool = False,
        status: Optional[AssetStatus] = AssetStatus.ONBOARDED,  # default status for models is ONBOARDED
        function_type: Optional[FunctionType] = FunctionType.AI,
        **additional_info,
    ) -> None:
        """Initialize a new Model instance.

        Args:
            id (Text): ID of the Model.
            name (Text, optional): Name of the Model. Defaults to "".
            description (Text, optional): Description of the Model. Defaults to "".
            api_key (Text, optional): Authentication key for API access.
                Defaults to config.TEAM_API_KEY.
            supplier (Union[Dict, Text, Supplier, int], optional): Provider/creator
                of the model. Defaults to "aiXplain".
            version (Text, optional): Version identifier of the model. Defaults to None.
            function (Function, optional): The AI function this model performs.
                Defaults to None.
            is_subscribed (bool, optional): Whether the user has an active
                subscription. Defaults to False.
            cost (Dict, optional): Pricing information for model usage.
                Defaults to None.
            created_at (Optional[datetime], optional): When the model was created.
                Defaults to None.
            input_params (Dict, optional): Parameters accepted by the model.
                Defaults to None.
            output_params (Dict, optional): Description of model outputs.
                Defaults to None.
            model_params (Dict, optional): Configuration parameters for model
                behavior. Defaults to None.
            supports_streaming (bool, optional): Whether the model supports streaming
                responses. Defaults to False.
            status (AssetStatus, optional): Current status of the model.
                Defaults to AssetStatus.ONBOARDED.
            function_type (FunctionType, optional): Category of function.
                Defaults to FunctionType.AI.
            **additional_info: Additional model metadata.
        """
        super().__init__(id, name, description, supplier, version, cost=cost)
        self.api_key = api_key
        self.additional_info = additional_info
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.function = function
        self.is_subscribed = is_subscribed
        self.created_at = created_at
        self.input_params = input_params
        self.output_params = output_params
        self.model_params = ModelParameters(model_params) if model_params else None
        self.supports_streaming = supports_streaming
        self.function_type = function_type
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.ONBOARDED
        self.status = status

    def to_dict(self) -> Dict:
        """Convert the model instance to a dictionary representation.

        Returns:
            Dict: A dictionary containing the model's configuration with keys:
                - id: Unique identifier
                - name: Model name
                - description: Model description
                - supplier: Model provider
                - additional_info: Extra metadata (excluding None/empty values)
                - input_params: Input parameter configuration
                - output_params: Output parameter configuration
                - model_params: Model behavior parameters
                - function: AI function type
                - status: Current model status
        """
        clean_additional_info = {k: v for k, v in self.additional_info.items() if v not in [None, [], {}]}
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "supplier": self.supplier,
            "additional_info": clean_additional_info,
            "input_params": self.input_params,
            "output_params": self.output_params,
            "model_params": self.model_params.to_dict(),
            "function": self.function,
            "status": self.status,
        }

    def get_parameters(self) -> Optional[ModelParameters]:
        """Get the model's configuration parameters.

        Returns:
            Optional[ModelParameters]: The model's parameter configuration if set,
                None otherwise.
        """
        if self.model_params:
            return self.model_params
        return None

    def __repr__(self) -> str:
        """Return a string representation of the model.

        Returns:
            str: A string in the format "Model: <name> by <supplier> (id=<id>)".
        """
        try:
            return f"Model: {self.name} by {self.supplier['name']} (id={self.id})"
        except Exception:
            return f"Model: {self.name} by {self.supplier} (id={self.id})"

    def sync_poll(
        self,
        poll_url: Text,
        name: Text = "model_process",
        wait_time: float = 0.5,
        timeout: float = 300,
    ) -> ModelResponse:
        """Poll the platform until an asynchronous operation completes or times out.

        This method repeatedly checks the status of an asynchronous operation,
        implementing exponential backoff for the polling interval.

        Args:
            poll_url (Text): URL to poll for operation status.
            name (Text, optional): Identifier for the operation for logging.
                Defaults to "model_process".
            wait_time (float, optional): Initial wait time in seconds between polls.
                Will increase exponentially up to 60 seconds. Defaults to 0.5.
            timeout (float, optional): Maximum total time to poll in seconds.
                Defaults to 300.

        Returns:
            ModelResponse: The final response from the operation. If polling times
                out or fails, returns a failed response with appropriate error message.

        Note:
            The minimum wait time between polls is 0.2 seconds. The wait time
            increases by 10% after each poll up to a maximum of 60 seconds.
        """
        logging.info(f"Polling for Model: Start polling for {name}")
        start, end = time.time(), time.time()
        # keep wait time as 0.2 seconds the minimum
        wait_time = max(wait_time, 0.2)
        completed = False
        response_body = ModelResponse(status=ResponseStatus.FAILED, completed=False)
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                completed = response_body["completed"]

                end = time.time()
                if completed is False:
                    time.sleep(wait_time)
                    if wait_time < 60:
                        wait_time *= 1.1
            except Exception as e:
                response_body = ModelResponse(
                    status=ResponseStatus.FAILED,
                    completed=False,
                    error_message="No response from the service.",
                )
                logging.error(f"Polling for Model: polling for {name}: {e}")
                break
        if response_body["completed"] is True:
            logging.debug(f"Polling for Model: Final status of polling for {name}: {response_body}")
        else:
            response_body = ModelResponse(
                status=ResponseStatus.FAILED,
                completed=False,
                error_message="No response from the service.",
            )
            logging.error(
                f"Polling for Model: Final status of polling for {name}: No response in {timeout} seconds - {response_body}"
            )
        return response_body

    def poll(self, poll_url: Text, name: Text = "model_process") -> ModelResponse:
        """Make a single poll request to check operation status.

        Args:
            poll_url (Text): URL to poll for operation status.
            name (Text, optional): Identifier for the operation for logging.
                Defaults to "model_process".

        Returns:
            ModelResponse: The current status of the operation. Contains completion
                status, any results or errors, and usage statistics.

        Note:
            This is a low-level method used by sync_poll. Most users should use
            sync_poll instead for complete operation handling.
        """
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            if resp["completed"] is True:
                status = ResponseStatus.SUCCESS
                if "error_message" in resp or "supplierError" in resp:
                    status = ResponseStatus.FAILED
            else:
                status = ResponseStatus.IN_PROGRESS

            logging.debug(f"Single Poll for Model: Status of polling for {name}: {resp}")

            raw_status = resp.pop("status", status)
            # Convert string status to ResponseStatus enum if needed
            if isinstance(raw_status, str):
                try:
                    raw_status = ResponseStatus(raw_status)
                except ValueError:
                    # If string doesn't match enum, use the computed status
                    raw_status = status

            return ModelResponse(
                status=raw_status,
                data=resp.pop("data", ""),
                details=resp.pop("details", {}),
                completed=resp.pop("completed", False),
                error_message=resp.pop("error_message", ""),
                used_credits=resp.pop("usedCredits", 0),
                run_time=resp.pop("runTime", 0),
                usage=resp.pop("usage", None),
                error_code=resp.get("error_code", None),
                **resp,
            )
        except Exception as e:
            resp = {"status": "FAILED"}
            logging.error(f"Single Poll for Model: Error of polling for {name}: {e}")
            return ModelResponse(
                status=ResponseStatus.FAILED,
                error_message=str(e),
                completed=False,
            )

    def run_stream(
        self,
        data: Union[Text, Dict],
        parameters: Optional[Dict] = None,
    ) -> ModelResponseStreamer:
        """Execute the model with streaming response.

        Args:
            data (Union[Text, Dict]): The input data for the model.
            parameters (Optional[Dict], optional): Additional parameters for model
                execution. Defaults to None.

        Returns:
            ModelResponseStreamer: A streamer object that yields response chunks.

        Raises:
            AssertionError: If the model doesn't support streaming.
        """
        assert self.supports_streaming, f"Model '{self.name} ({self.id})' does not support streaming"
        payload = build_payload(data=data, parameters=parameters, stream=True)
        url = f"{self.url}/{self.id}".replace("api/v1/execute", "api/v2/execute")
        logging.debug(f"Model Run Stream: Start service for {url} - {payload}")
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("post", url, headers=headers, data=payload, stream=True)
        return ModelResponseStreamer(r.iter_lines(decode_unicode=True))

    def run(
        self,
        data: Union[Text, Dict],
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False,
    ) -> Union[ModelResponse, ModelResponseStreamer]:
        """Execute the model and wait for results.

        This method handles both synchronous and streaming execution modes. For
        asynchronous operations, it polls until completion or timeout.

        Args:
            data (Union[Text, Dict]): The input data for the model.
            name (Text, optional): Identifier for the operation for logging.
                Defaults to "model_process".
            timeout (float, optional): Maximum time to wait for completion in seconds.
                Defaults to 300.
            parameters (Dict, optional): Additional parameters for model execution.
                Defaults to None.
            wait_time (float, optional): Initial wait time between polls in seconds.
                Defaults to 0.5.
            stream (bool, optional): Whether to use streaming mode. Requires model
                support. Defaults to False.

        Returns:
            Union[ModelResponse, ModelResponseStreamer]: The model's response. For
                streaming mode, returns a streamer object. For regular mode,
                returns a response object with results or error information.

        Note:
            If the model execution becomes asynchronous, this method will poll
            for completion using sync_poll with the specified timeout and wait_time.
        """
        if stream:
            return self.run_stream(data=data, parameters=parameters)
        start = time.time()
        payload = build_payload(data=data, parameters=parameters)
        url = f"{self.url}/{self.id}".replace("api/v1/execute", "api/v2/execute")
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
                response = {
                    "status": "FAILED",
                    "error_message": msg,
                    "runTime": end - start,
                }
        raw_status = response.pop("status", ResponseStatus.FAILED)
        # Convert string status to ResponseStatus enum if needed
        if isinstance(raw_status, str):
            try:
                raw_status = ResponseStatus(raw_status)
            except ValueError:
                raw_status = ResponseStatus.FAILED

        return ModelResponse(
            status=raw_status,
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
        data: Union[Text, Dict],
        name: Text = "model_process",
        parameters: Optional[Dict] = None,
    ) -> ModelResponse:
        """Start asynchronous model execution.

        This method initiates model execution but doesn't wait for completion.
        Use sync_poll to check the operation status later.

        Args:
            data (Union[Text, Dict]): The input data for the model.
            name (Text, optional): Identifier for the operation for logging.
                Defaults to "model_process".
            parameters (Dict, optional): Additional parameters for model execution.
                Defaults to None.

        Returns:
            ModelResponse: Initial response containing:
                - status: Current operation status
                - url: URL for polling operation status
                - error_message: Any immediate errors
                - other response metadata
        """
        url = f"{self.url}/{self.id}"
        payload = build_payload(data=data, parameters=parameters)
        logging.debug(f"Model Run Async: Start service for {name} - {url} - {payload}")
        response = call_run_endpoint(payload=payload, url=url, api_key=self.api_key)
        raw_status = response.pop("status", ResponseStatus.FAILED)
        # Convert string status to ResponseStatus enum if needed
        if isinstance(raw_status, str):
            try:
                raw_status = ResponseStatus(raw_status)
            except ValueError:
                raw_status = ResponseStatus.FAILED

        return ModelResponse(
            status=raw_status,
            data=response.pop("data", ""),
            details=response.pop("details", {}),
            completed=response.pop("completed", False),
            error_message=response.pop("error_message", ""),
            url=response.pop("url", None),
            **response,
        )

    def check_finetune_status(self, after_epoch: Optional[int] = None):
        """Check the status of the FineTune model.

        Args:
            after_epoch (Optional[int], optional): status after a given epoch. Defaults to None.

        Raises:
            Exception: If the 'TEAM_API_KEY' is not provided.

        Returns:
            FinetuneStatus: The status of the FineTune model.
        """
        from aixplain.enums import AssetStatus
        from aixplain.modules.finetune.status import FinetuneStatus

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        resp = None
        try:
            url = urljoin(self.backend_url, f"sdk/finetune/{self.id}/ml-logs")
            logging.info(f"Start service for GET Check FineTune status Model  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            finetune_status = AssetStatus(resp["finetuneStatus"])
            model_status = AssetStatus(resp["modelStatus"])
            logs = sorted(resp["logs"], key=lambda x: float(x["epoch"]))
            target_epoch = None
            if after_epoch is not None:
                logs = [log for log in logs if float(log["epoch"]) > after_epoch]
                if len(logs) > 0:
                    target_epoch = float(logs[0]["epoch"])
            elif len(logs) > 0:
                target_epoch = float(logs[-1]["epoch"])
            if target_epoch is not None:
                log = None
                for log_ in logs:
                    if int(log_["epoch"]) == target_epoch:
                        if log is None:
                            log = log_
                        else:
                            if log_["trainLoss"] is not None:
                                log["trainLoss"] = log_["trainLoss"]
                            if log_["evalLoss"] is not None:
                                log["evalLoss"] = log_["evalLoss"]
                status = FinetuneStatus(
                    status=finetune_status,
                    model_status=model_status,
                    epoch=(float(log["epoch"]) if "epoch" in log and log["epoch"] is not None else None),
                    training_loss=(
                        float(log["trainLoss"]) if "trainLoss" in log and log["trainLoss"] is not None else None
                    ),
                    validation_loss=(
                        float(log["evalLoss"]) if "evalLoss" in log and log["evalLoss"] is not None else None
                    ),
                )
            else:
                status = FinetuneStatus(
                    status=finetune_status,
                    model_status=model_status,
                )

            logging.info(f"Response for GET Check FineTune status Model - Id {self.id} / Status {status.status.value}.")
            return status
        except Exception:
            message = ""
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Status {status_code} - {message}"
            error_message = f"Check FineTune status Model: Error {message}"
            logging.exception(error_message)

    def delete(self) -> None:
        """Delete this model from the aiXplain platform.

        This method attempts to delete the model from the platform. It will fail
        if the user doesn't have appropriate permissions.

        Raises:
            Exception: If deletion fails or if the user doesn't have permission.
        """
        try:
            url = urljoin(self.backend_url, f"sdk/models/{self.id}")
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for DELETE Model  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Model Deletion Error: Make sure the model exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

    def add_additional_info_for_benchmark(self, display_name: str, configuration: Dict) -> None:
        """Add benchmark-specific information to the model.

        This method updates the model's additional_info with benchmark-related
        metadata.

        Args:
            display_name (str): Name for display in benchmarks.
            configuration (Dict): Model configuration settings for benchmarking.
        """
        self.additional_info["displayName"] = display_name
        self.additional_info["configuration"] = configuration

    @classmethod
    def from_dict(cls, data: Dict) -> "Model":
        """Create a Model instance from a dictionary representation.

        Args:
            data (Dict): Dictionary containing model configuration with keys:
                - id: Model identifier
                - name: Model name
                - description: Model description
                - api_key: API key for authentication
                - supplier: Model provider information
                - version: Model version
                - function: AI function type
                - is_subscribed: Subscription status
                - cost: Pricing information
                - created_at: Creation timestamp (ISO format)
                - input_params: Input parameter configuration
                - output_params: Output parameter configuration
                - model_params: Model behavior parameters
                - additional_info: Extra metadata

        Returns:
            Model: A new Model instance populated with the dictionary data.
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            api_key=data.get("api_key", config.TEAM_API_KEY),
            supplier=data.get("supplier", "aiXplain"),
            version=data.get("version", "1.0"),
            function=Function(data.get("function")),
            is_subscribed=data.get("is_subscribed", False),
            cost=data.get("cost"),
            created_at=(datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None),
            input_params=data.get("input_params"),
            output_params=data.get("output_params"),
            model_params=data.get("model_params"),
            **data.get("additional_info", {}),
        )
