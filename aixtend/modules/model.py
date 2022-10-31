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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira and Lucas Pavanelli
Date: September 1st 2022
Description:
    Model Class
"""

import time
import json
import requests
import logging
import traceback
from requests.adapters import HTTPAdapter, Retry

class Model:  
    def __init__(self, api_key: str, url: str) -> None:
        """
        params:
        ---
            api_key: API key of the pipeline
            url: API endpoint
        """
        self.api_key = api_key
        self.url = url
    
    def __polling(self, poll_url: str, name: str = "model_process", wait_time: int = 1, timeout: float = 300):
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
        logging.info(f"Start polling for {name} ({self.api_key})")
        start, end = time.time(), time.time()
        completed = False
        response_body = { 'status': 'FAILED', 'completed': False }
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                completed = response_body['completed']

                end = time.time()
                time.sleep(wait_time)
                if wait_time < 60:
                    wait_time *= 1.1
            except Exception as e:
                logging.error(f"ERROR: polling for {name} ({self.api_key}): Continue")
                break
        
        if response_body['completed'] is True:
            try:
                response_body['status'] = 'SUCCESS'
                logging.info(f"Final status of polling for {name} ({self.api_key}): SUCCESS - {response_body}")
            except Exception as e:
                response_body['status'] = 'ERROR'
                logging.error(f"ERROR: Final status of polling for {name} ({self.api_key}): ERROR - {response_body}")
        else:
            response_body['status'] = 'ERROR'
            logging.error(f"ERROR: Final status of polling for {name} ({self.api_key}): No response in {timeout} seconds - {response_body}")
        return response_body

    def poll(self, poll_url: str, name: str = "model_process"):
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
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        r = session.get(poll_url, headers=headers)
        try:
            resp = r.json()
            if resp['completed'] is True:
                resp['status'] = 'SUCCESS'
            else:
                resp['status'] = 'IN_PROGRESS'
            logging.info(f"Status of polling for {name} ({self.api_key}): {resp}")
        except:
            resp = { 'status': 'FAILED' }
        return resp

    def run(self, data: str, name: str = "model_process", timeout: float = 300):
        """
        Runs a model call.
        
        params:
        ---
            data: link to the input data
            name: Optional. ID given to a call
            timeout: total polling time
        
        return:
        ---
            Output: parsed output from model
        """
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
            print(msg)
            end = time.time()
            return { 'status': 'FAILED', 'error': error_message, 'elapsed_time': end - start }

    def run_async(self, data: str, name: str = "model_process"):
        """
        Runs asynchronously a model call.
        
        params:
        ---
            data: link to the input data
            name: Optional. ID given to a call

        return:
        ---
            poll_url: polling URL
        """
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({ "data": data })

        session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        logging.info(f"Start service for {name} ({self.api_key}) - {self.url} - {payload}")
        r = session.post(self.url, headers=headers, data=payload)
        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name} ({self.api_key}) - {r.status_code} - {resp}")
        
            poll_url = resp['data']
            response = {
                'status': 'IN_PROGRESS',
                'url': poll_url
            }
        except:
            response = { 'status': 'FAILED' }
            if resp is not None:
                response['error'] = resp
        return response