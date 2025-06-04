__author__ = "lucaspavanelli"

"""
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
Description:
    Model Class
"""
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
    """This is ready-to-use AI model. This model can be run in both synchronous and asynchronous manner.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        url (Text, optional): endpoint of the model. Defaults to config.MODELS_RUN_URL.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Function, optional): model AI function. Defaults to None.
        url (str): URL to run the model.
        backend_url (str): URL of the backend.
        pricing (Dict, optional): model price. Defaults to None.
        **additional_info: Any additional Model info to be saved
        input_params (ModelParameters, optional): input parameters for the function.
        output_params (Dict, optional): output parameters for the function.
        model_params (ModelParameters, optional): parameters for the function.
        supports_streaming (bool, optional): whether the model supports streaming. Defaults to False.
        function_type (FunctionType, optional): type of the function. Defaults to FunctionType.AI.
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
        """Model Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Text, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            input_params (Dict, optional): input parameters for the function.
            output_params (Dict, optional): output parameters for the function.
            model_params (Dict, optional): parameters for the function.
            supports_streaming (bool, optional): whether the model supports streaming. Defaults to False.
            status (AssetStatus, optional): status of the model. Defaults to None.
            function_type (FunctionType, optional): type of the function. Defaults to FunctionType.AI.
            **additional_info: Any additional Model info to be saved
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
        """Get the model info as a Dictionary

        Returns:
            Dict: Model Information
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

    def get_parameters(self) -> ModelParameters:
        if self.model_params:
            return self.model_params
        return None

    def __repr__(self):
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
        """Keeps polling the platform to check whether an asynchronous call is done.

        Args:
            poll_url (Text): polling URL
            name (Text, optional): ID given to a call. Defaults to "model_process".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            timeout (float, optional): total polling time. Defaults to 300.

        Returns:
            Dict: response obtained by polling call
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
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (Text): polling
            name (Text, optional): ID given to a call. Defaults to "model_process".

        Returns:
            Dict: response obtained by polling call
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

            return ModelResponse(
                status=resp.pop("status", status),
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
        """Runs a model call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to None.
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            stream (bool, optional): whether the model supports streaming. Defaults to False.
        Returns:
            Union[ModelResponse, ModelStreamer]: parsed output from model
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
        data: Union[Text, Dict],
        name: Text = "model_process",
        parameters: Optional[Dict] = None,
    ) -> ModelResponse:
        """Runs asynchronously a model call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to None.

        Returns:
            dict: polling URL in response
        """
        url = f"{self.url}/{self.id}"
        payload = build_payload(data=data, parameters=parameters)
        logging.debug(f"Model Run Async: Start service for {name} - {url} - {payload}")
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
                    training_loss=(float(log["trainLoss"]) if "trainLoss" in log and log["trainLoss"] is not None else None),
                    validation_loss=(float(log["evalLoss"]) if "evalLoss" in log and log["evalLoss"] is not None else None),
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
        """Delete Model service"""
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

    @classmethod
    def from_dict(cls, data: Dict) -> "Model":
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
