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
import json
import logging
import traceback
from typing import List
from aixplain.factories.file_factory import FileFactory
from aixplain.enums import Function
from aixplain.modules.asset import Asset
from aixplain.utils import config
from urllib.parse import urljoin
from aixplain.utils.file_utils import _request_with_retry
from typing import Union, Optional, Text, Dict


class Model(Asset):
    """This is ready-to-use AI model. This model can be run in both synchronous and asynchronous manner.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        url (Text, optional): endpoint of the model. Defaults to config.MODELS_RUN_URL.
        supplier (Text, optional): model supplier. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Text, optional): model AI function. Defaults to None.
        url (str): URL to run the model.
        backend_url (str): URL of the backend.
        **additional_info: Any additional Model info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        function: Optional[Text] = None,
        **additional_info,
    ) -> None:
        """Model Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Text, optional): model supplier. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Text, optional): model AI function. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        super().__init__(id, name, description, supplier, version)
        self.api_key = api_key
        self.additional_info = additional_info
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.function = function

    def _is_subscribed(self) -> bool:
        """Returns if the model is subscribed to

        Returns:
            bool: True if subscribed
        """
        return self.api_key is not None

    def to_dict(self) -> Dict:
        """Get the model info as a Dictionary

        Returns:
            Dict: Model Information
        """
        clean_additional_info = {k: v for k, v in self.additional_info.items() if v is not None}
        return {"id": self.id, "name": self.name, "supplier": self.supplier, "additional_info": clean_additional_info}

    def __repr__(self):
        return f"<Model: {self.name} by {self.supplier}>"

    def __polling(self, poll_url: Text, name: Text = "model_process", wait_time: float = 0.5, timeout: float = 300) -> Dict:
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
        response_body = {"status": "FAILED", "completed": False}
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
                response_body = {"status": "ERROR", "completed": False, "error": "No response from the service."}
                logging.error(f"Polling for Model: polling for {name}: {e}")
                break
        if response_body["completed"] is True:
            try:
                response_body["status"] = "SUCCESS"
                logging.info(f"Polling for Model: Final status of polling for {name}: SUCCESS - {response_body}")
            except Exception as e:
                response_body["status"] = "ERROR"
                logging.error(f"Polling for Model:: Final status of polling for {name}: ERROR - {response_body}")
        else:
            response_body["status"] = "ERROR"
            logging.error(
                f"Polling for Model: Final status of polling for {name}: No response in {timeout} seconds - {response_body}"
            )
        return response_body

    def poll(self, poll_url: Text, name: Text = "model_process") -> Dict:
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
                resp["status"] = "SUCCESS"
            else:
                resp["status"] = "IN_PROGRESS"
            logging.info(f"Single Poll for Model: Status of polling for {name}: {resp}")
        except Exception as e:
            resp = {"status": "FAILED"}
            logging.error(f"Single Poll for Model: Error of polling for {name}: {e}")
        return resp

    def run(
        self,
        data: Union[Text, Dict],
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Dict = {},
        wait_time: float = 0.5,
    ) -> Dict:
        """Runs a model call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (Text, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.

        Returns:
            Dict: parsed output from model
        """
        start = time.time()
        try:
            response = self.run_async(data, name=name, parameters=parameters)
            if response["status"] == "FAILED":
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            response = self.__polling(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            return response
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Model Run: Error in running for {name}: {e}")
            end = time.time()
            return {"status": "FAILED", "error": msg, "elapsed_time": end - start}

    def run_async(self, data: Union[Text, Dict], name: Text = "model_process", parameters: Dict = {}) -> Dict:
        """Runs asynchronously a model call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (Text, optional): ID given to a call. Defaults to "model_process".
            parameters (Dict, optional): optional parameters to the model. Defaults to "{}".

        Returns:
            dict: polling URL in response
        """
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

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
            except Exception as e:
                payload = {"data": data}
        payload.update(parameters)
        payload = json.dumps(payload)

        call_url = f"{self.url}/{self.id}"
        r = _request_with_retry("post", call_url, headers=headers, data=payload)
        logging.info(f"Model Run Async: Start service for {name} - {self.url} - {payload} - {headers}")

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")

            poll_url = resp["data"]
            response = {"status": "IN_PROGRESS", "url": poll_url}
        except Exception as e:
            response = {"status": "FAILED"}
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Model Run Async: Error in running for {name}: {resp}")
            if resp is not None:
                response["error"] = msg
        return response

    def check_finetune_status(self):
        """Check the status of the FineTune model.

        Raises:
            Exception: If the 'TEAM_API_KEY' is not provided.

        Returns:
            str: The status of the FineTune model.
        """
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        try:
            url = urljoin(self.backend_url, f"sdk/models/{self.id}")
            logging.info(f"Start service for GET Check FineTune status Model  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            status = resp["status"]
            logging.info(f"Response for GET Check FineTune status Model - Id {self.id} / Status {status}.")
            return status
        except Exception as e:
            message = ""
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Status {status_code} - {message}"
            error_message = f"Check FineTune status Model: Error {message}"
            logging.exception(error_message)
