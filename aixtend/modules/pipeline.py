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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira and Lucas Pavanelli
Date: September 1st 2022
Description:
    Pipeline Class
"""

import time
import json
import logging
from aixtend.utils.file_utils import _request_with_retry
from typing import Union


class Pipeline:
    def __init__(self, api_key: str, url: str) -> None:
        """
        params:
        ---
            api_key: API key of the pipeline
            url: API endpoint
        """
        self.api_key = api_key
        self.url = url

    def __polling(self, poll_url: str, name: str = "pipeline_process", wait_time: float = 1.0, timeout: float = 20000.0):
        """
        Keeps polling the platform to check whether an asynchronous call is done.

        params:
        ---
            poll_url: polling URL
            name: Optional. ID given to a call
            wait_time: wait time in seconds between polling calls
            timeout: total polling time

        return:
        ---
            success: Boolean variable indicating whether the call finished successfully or not
            resp: response obtained by polling call
        """
        logging.debug(f"Start polling for {name} ")
        start, end = time.time(), time.time()
        completed = False
        response_body = {"status": "FAILED"}
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                logging.debug(f"Status of polling for {name} : {response_body}")
                completed = response_body["completed"]

                end = time.time()
                time.sleep(wait_time)
                if wait_time < 60:
                    wait_time *= 1.1
            except Exception as e:
                logging.error(f"ERROR: polling for {name} : Continue")

        if response_body and response_body["status"] == "SUCCESS":
            try:
                logging.debug(f"Final status of polling for {name} : SUCCESS - {response_body}")
            except Exception as e:
                logging.error(f"ERROR: Final status of polling for {name} : ERROR - {response_body}")
        else:
            logging.error(f"ERROR: Final status of polling for {name} : No response in {timeout} seconds - {response_body}")
        return response_body

    def poll(self, poll_url: str, name: str = "pipeline_process"):
        """
        Poll the platform to check whether an asynchronous call is done.

        params:
        ---
            poll_url: polling URL
            name: Optional. ID given to a call

        return:
        ---
            resp: response obtained by polling call
        """
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            logging.info(f"Status of polling for {name} : {resp}")
        except:
            resp = {"status": "FAILED"}
        return resp

    def run(self, data: Union[str, dict], name: str = "pipeline_process", timeout: float = 20000.0):
        """
        Runs a pipeline call.

        params:
        ---
            data: link to the input data
            name: Optional. ID given to a call
            timeout: total polling time
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

    def run_async(self, data: Union[str, dict], name: str = "pipeline_process", size=None):
        """
        Runs asynchronously a pipeline call.

        params:
        ---
            data: link to the input data
            name: Optional. ID given to a call

        return:
        ---
            poll_url: polling URL
        """
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        if isinstance(data, dict):
            if size is not None:
                data['size'] = size
            payload = json.dumps(data)
        else:
            try:
                data_json = json.loads(data)
                if size is not None:
                    data_json['size'] = size
                payload = json.dumps(data_json)
            except Exception as e:
                payload = {"data": data}
                if size is not None:
                    payload["size"] = size
                payload = json.dumps(payload)
        
        logging.info(f"Start service for {name}  - {self.url} - {payload}")
        r = _request_with_retry("post", self.url, headers=headers, data=payload)

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
