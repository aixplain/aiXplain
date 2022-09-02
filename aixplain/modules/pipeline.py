__author__='lucaspavanelli'

"""
Copyright 2022 The aiXplain pipeline authors

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
import requests
import logging
from requests.adapters import HTTPAdapter, Retry

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

    def __polling(self, poll_url: str, name: str = "pipeline_process", wait_time: float = 1.0, timeout: float=20000.0):
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
        logging.debug(f"Start polling for {name} ({self.api_key})")
        start, end = time.time(), time.time()
        completed = False
        response_body = None
        while not completed and (end - start)<timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                logging.debug(f"Status of polling for {name} ({self.api_key}): {response_body}")
                completed = response_body['completed']

                end = time.time()
                time.sleep(wait_time)
                if wait_time < 60:
                    wait_time *= 1.1
            except Exception:
                logging.error(f"ERROR: polling for {name} ({self.api_key}): Continue")
        
        if response_body and response_body['status'] == 'SUCCESS':
            try:
                logging.debug(f"Final status of polling for {name} ({self.api_key}): SUCCESS - {response_body}")
                return True, response_body
            except Exception:
                logging.error(f"ERROR: Final status of polling for {name} ({self.api_key}): ERROR - {response_body}")
                return False, response_body
        else:
            logging.error(f"ERROR: Final status of polling for {name} ({self.api_key}): No response in {timeout} seconds - {response_body}")
            return False, response_body

    def poll(self, poll_url: str, name="pipeline_process"):
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
        resp = r.json()
        logging.info(f"Status of polling for {name} ({self.api_key}): {resp}")
        return resp


    def run(self, data: str, name: str = "pipeline_process"):
        """
        Runs a pipeline call.
        
        params:
        ---
            data: link to the input data
            name: Optional. ID given to a call
        """
        start = time.time()        
        try:           
            poll_url = self.run_async(data, name=name)
            end = time.time()
            success, response = self.__polling(poll_url, name=name)
            return { 'success': success, 'response': response, 'error': None, 'elapsed_time': end - start }
        except Exception:
            error_message = f'Error in request for {name} ({self.api_key})'
            logging.error(error_message)
            logging.exception()
            end = time.time()
            return { 'success': success, 'response': None, 'error': error_message, 'elapsed_time': end - start }

    def run_async(self, data, name="pipeline_process"):
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
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = json.dumps({ "data": data })
        
        logging.info(f"Start service for {name} ({self.api_key}) - {self.url} - {payload}")
        session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        r = session.post(self.url, headers=headers, data=payload)
        resp = r.json()
        logging.info(f'Result of request for {name} ({self.api_key}) - {r.status_code} - {resp}')
        
        poll_url = resp['url']
        return poll_url
