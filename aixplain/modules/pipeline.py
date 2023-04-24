__author__ = "aiXplain"

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
    Pipeline Class
"""

import time
import json
import logging
from aixplain.factories.file_factory import FileFactory
from aixplain.modules.asset import Asset
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from typing import Dict, Optional, Text, Union


class Pipeline(Asset):
    """Representing a custom pipeline that was created on the aiXplain Platform

    Attributes:
        id (Text): ID of the Pipeline
        name (Text): Name of the Pipeline
        api_key (Text): Team API Key to run the Pipeline.
        url (Text, optional): running URL of platform. Defaults to config.PIPELINES_RUN_URL.
        supplier (Text, optional): Pipeline supplier. Defaults to "aiXplain".
        version (Text, optional): version of the pipeline. Defaults to "1.0".
        **additional_info: Any additional Pipeline info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        api_key: Text,
        url: Text = config.PIPELINES_RUN_URL,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        **additional_info,
    ) -> None:
        """Create a Pipeline with the necessary information

        Args:
            id (Text): ID of the Pipeline
            name (Text): Name of the Pipeline
            api_key (Text): Team API Key to run the Pipeline.
            url (Text, optional): running URL of platform. Defaults to config.PIPELINES_RUN_URL.
            supplier (Text, optional): Pipeline supplier. Defaults to "aiXplain".
            version (Text, optional): version of the pipeline. Defaults to "1.0".
            **additional_info: Any additional Pipeline info to be saved
        """
        super().__init__(id, name, "", supplier, version)
        self.api_key = api_key
        self.url = url
        self.additional_info = additional_info

    def __polling(
        self, poll_url: Text, name: Text = "pipeline_process", wait_time: float = 1.0, timeout: float = 20000.0
    ) -> Dict:
        """Keeps polling the platform to check whether an asynchronous call is done.

        Args:
            poll_url (str): polling URL
            name (str, optional): ID given to a call. Defaults to "pipeline_process".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 1.0.
            timeout (float, optional): total polling time. Defaults to 20000.0.

        Returns:
            dict: response obtained by polling call
        """

        logging.debug(f"Polling for Pipeline: Start polling for {name} ")
        start, end = time.time(), time.time()
        completed = False
        response_body = {"status": "FAILED"}
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                logging.debug(f"Polling for Pipeline: Status of polling for {name} : {response_body}")
                completed = response_body["completed"]

                end = time.time()
                time.sleep(wait_time)
                if wait_time < 60:
                    wait_time *= 1.1
            except Exception as e:
                logging.error(f"Polling for Pipeline: polling for {name} : Continue")
        if response_body and response_body["status"] == "SUCCESS":
            try:
                logging.debug(f"Polling for Pipeline: Final status of polling for {name} : SUCCESS - {response_body}")
            except Exception as e:
                logging.error(f"Polling for Pipeline: Final status of polling for {name} : ERROR - {response_body}")
        else:
            logging.error(
                f"Polling for Pipeline: Final status of polling for {name} : No response in {timeout} seconds - {response_body}"
            )
        return response_body

    def poll(self, poll_url: Text, name: Text = "pipeline_process") -> Dict:
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (Text): polling URL
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            Dict: response obtained by polling call
        """

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            logging.info(f"Single Poll for Pipeline: Status of polling for {name} : {resp}")
        except Exception as e:
            resp = {"status": "FAILED"}
        return resp

    def run(self, data: Union[Text, Dict], name: Text = "pipeline_process", timeout: float = 20000.0) -> Dict:
        """Runs a pipeline call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (str, optional): ID given to a call. Defaults to "pipeline_process".
            timeout (float, optional): total polling time. Defaults to 20000.0.

        Returns:
            Dict: parsed output from pipeline
        """
        start = time.time()
        try:
            response = self.run_async(data, name=name)
            if response["status"] == "FAILED":
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            response = self.__polling(poll_url, name=name, timeout=timeout)
            return response
        except Exception as e:
            error_message = f"Error in request for {name} "
            logging.error(error_message)
            logging.exception(error_message)
            end = time.time()
            return {"status": "FAILED", "error": error_message, "elapsed_time": end - start}

    def run_async(self, data: Union[Text, Dict], name: str = "pipeline_process") -> Dict:
        """Runs asynchronously a pipeline call.

        Args:
            data (Union[Text, Dict]): link to the input data
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            Dict: polling URL in response
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
        payload = json.dumps(payload)
        call_url = f"{self.url}/{self.id}"
        logging.info(f"Start service for {name}  - {call_url} - {payload}")
        r = _request_with_retry("post", call_url, headers=headers, data=payload)

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name}  - {r.status_code} - {resp}")

            poll_url = resp["url"]
            response = {"status": "IN_PROGRESS", "url": poll_url}
        except Exception as e:
            response = {"status": "FAILED"}
            if resp is not None:
                response["error"] = resp
        return response
