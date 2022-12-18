__author__='lucaspavanelli'

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
import requests
import logging
import traceback
from typing import List
from aixtend.utils import config
from aixtend.utils.file_utils import _request_with_retry


class Model:  
    def __init__(self, id:str, name:str, supplier:str, api_key: str = None, subscription_id:str = None, **additional_info) -> None:
        """Create a Model with the necessary information

        Args:
            id (str): ID of the Model
            name (str): Name of the Model
            supplier (str): supplier of the Model
            api_key (str, optional): API key of the Model. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        self.url = config.MODELS_RUN_URL
        self.id = id
        self.name = name
        self.supplier = supplier
        self.api_key = api_key
        self.subscription_id = subscription_id
        self.additional_info = additional_info
    

    def _is_subscribed(self) -> bool:
        """Returns if the model is subscribed to

        Returns:
            bool: True if subscribed
        """
        return self.api_key is not None


    def get_asset_info(self) -> dict:
        """Get the model info as a Dictionary

        Returns:
            dict: Model Information
        """
        self.additional_info["subscribed"] = self._is_subscribed()
        clean_additional_info = {k: v for k, v in self.additional_info.items() if v is not None}
        return {'id': self.id, 'name': self.name, 'supplier': self.supplier, 'additional_info': clean_additional_info}


    def __polling(self, poll_url: str, name: str = "model_process", wait_time: int = 1, timeout: float = 300) -> dict:
        """ Keeps polling the platform to check whether an asynchronous call is done.

        Args:
            poll_url (str): polling URL
            name (str, optional): ID given to a call. Defaults to "model_process".
            wait_time (int, optional): wait time in seconds between polling calls. Defaults to 1.
            timeout (float, optional): total polling time. Defaults to 300.

        Returns:
            dict: response obtained by polling call
        """
        logging.info(f"Polling for Model: Start polling for {name}")
        start, end = time.time(), time.time()
        completed = False
        response_body = { 'status': 'FAILED', 'completed': False }
        if self.api_key is None:
            logging.error(f"Polling for Model: Error in polling for {name}: 'api_key' not found. Please subscribe to the model")
            response_body['status'] = 'ERROR'
            return response_body
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                completed = response_body['completed']

                end = time.time()
                time.sleep(wait_time)
                if wait_time < 60:
                    wait_time *= 1.1
            except Exception as e:
                logging.error(f"Polling for Model: polling for {name}: {e}")
                break
        if response_body['completed'] is True:
            try:
                response_body['status'] = 'SUCCESS'
                logging.info(f"Polling for Model: Final status of polling for {name}: SUCCESS - {response_body}")
            except Exception as e:
                response_body['status'] = 'ERROR'
                logging.error(f"Polling for Model:: Final status of polling for {name}: ERROR - {response_body}")
        else:
            response_body['status'] = 'ERROR'
            logging.error(f"Polling for Model: Final status of polling for {name}: No response in {timeout} seconds - {response_body}")
        return response_body


    def poll(self, poll_url: str, name: str = "model_process") -> dict:
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (str): polling
            name (str, optional): ID given to a call. Defaults to "model_process".

        Returns:
            dict: response obtained by polling call
        """
        if self.api_key is None:
            response_body = { 'status': 'ERROR', 'completed': False }
            logging.error(f"Single Poll for Model: Error in polling for {name}: 'api_key' not found. Please subscribe to the model")
            return response_body
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            if resp['completed'] is True:
                resp['status'] = 'SUCCESS'
            else:
                resp['status'] = 'IN_PROGRESS'
            logging.info(f"Single Poll for Model: Status of polling for {name}: {resp}")
        except Exception as e:
            resp = { 'status': 'FAILED' }
            logging.error(f"Single Poll for Model: Error of polling for {name}: {e}")
        return resp


    def run(self, data: str, name: str = "model_process", timeout: float = 300) -> dict:
        """Runs a model call.

        Args:
            data (str): link to the input data
            name (str, optional): ID given to a call. Defaults to "model_process".
            timeout (float, optional): total polling time. Defaults to 300.

        Returns:
            dict: parsed output from model
        """
        if self.api_key is None:
            response_body = { 'status': 'ERROR', 'completed': False }
            logging.error(f"Model Run: Error in running for {name}: 'api_key' not found. Please subscribe to the model")
            return response_body
        start = time.time()
        try:           
            response = self.run_async(data, name=name)
            if response['status'] == 'FAILED':
                end = time.time()
                response['elapsed_time'] = end - start
                return response
            poll_url = response['url']
            end = time.time()
            response = self.__polling(poll_url, name=name, timeout=timeout)
            return response
        except Exception as e:
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Model Run: Error in running for {name}: {e}")
            end = time.time()
            return { 'status': 'FAILED', 'error': msg, 'elapsed_time': end - start }

    def run_async(self, data: str, name: str = "model_process") -> dict:
        """Runs asynchronously a model call.

        Args:
            data (str): link to the input data
            name (str, optional): ID given to a call. Defaults to "model_process".

        Returns:
            dict: polling URL
        """
        if self.api_key is None:
            response_body = { 'status': 'ERROR', 'completed': False }
            logging.error(f"Model Run Async: Error in running for {name}: 'api_key' not found. Please subscribe to the model")
            return response_body
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({ "data": data })
        r = _request_with_retry("post", self.url, headers=headers, data=payload)
        logging.info(f"Model Run Async: Start service for {name} - {self.url} - {payload}")
        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} - {r.status_code} - {resp}")
        
            poll_url = resp['data']
            response = {
                'status': 'IN_PROGRESS',
                'url': poll_url
            }
        except Exception as e:
            response = { 'status': 'FAILED' }
            msg = f"Error in request for {name} - {traceback.format_exc()}"
            logging.error(f"Model Run Async: Error in running for {name}: {e}")
            if resp is not None:
                response['error'] = msg
        return response
    