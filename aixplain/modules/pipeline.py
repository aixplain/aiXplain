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
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from typing import Union


class Pipeline:
    """Representing a custom pipeline that was created on the aiXplain Platform

    Attributes:
        id (str): ID of the Pipeline.
        name (str): Name of the Pipeline.
        api_key (str): Team API Key to run the Pipeline.
        url (str): Running URL of the platform.
        additional_info (dict): Additional Pipeline info.
    """
    def __init__(self, id: str, name:str, api_key: str, url: str = config.PIPELINES_RUN_URL, **additional_info) -> None:
        """Create a Pipeline with the necessary information

        Args:
            id (str): ID of the Pipeline
            name (str): Name of the Pipeline
            api_key (str): Team API Key to run the Pipeline.
            url (str, optional): running URL of platform. Defaults to config.PIPELINES_RUN_URL.
            **additional_info: Any additional Pipeline info to be saved
        """
        self.id = id
        self.name = name
        self.api_key = api_key
        self.url = url
        self.additional_info = additional_info

    def __polling(self, poll_url: str, name: str = "pipeline_process", wait_time: float = 1.0, timeout: float = 20000.0) -> dict:
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
            logging.error(f"Polling for Pipeline: Final status of polling for {name} : No response in {timeout} seconds - {response_body}")
        return response_body

    def poll(self, poll_url: str, name: str = "pipeline_process") -> dict:
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (str): polling URL
            name (str, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            dict: response obtained by polling call
        """
    
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            logging.info(f"Single Poll for Pipeline: Status of polling for {name} : {resp}")
        except:
            resp = {"status": "FAILED"}
        return resp

    def run(self, data: Union[str, dict], name: str = "pipeline_process", timeout: float = 20000.0) -> dict:
        """Runs a pipeline call.

        Args:
            data (Union[str, dict]): link to the input data
            name (str, optional): ID given to a call. Defaults to "pipeline_process".
            timeout (float, optional): total polling time. Defaults to 20000.0.

        Returns:
            dict: parsed output from pipeline
        """
        start = time.time()
        try:
            success = False
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

    def run_async(self, data: Union[str, dict], name: str = "pipeline_process") -> dict:
        """Runs asynchronously a pipeline call.

        Args:
            data (Union[str, dict]): link to the input data
            name (str, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            dict: polling URL in response
        """
   
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        if isinstance(data, dict):
            payload = json.dumps(data)
        else:
            try:
                data_json = json.loads(data)
                payload = data
            except Exception as e:
                payload = json.dumps({"data": data})
        call_url = f"{self.url}/{self.id}"
        logging.info(f"Start service for {name}  - {call_url} - {payload}")
        r = _request_with_retry("post", call_url, headers=headers, data=payload)

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name}  - {r.status_code} - {resp}")

            poll_url = resp["url"]
            response = {"status": "IN_PROGRESS", "url": poll_url}
        except:
            response = {"status": "FAILED"}
            if resp is not None:
                response["error"] = resp
        return response
