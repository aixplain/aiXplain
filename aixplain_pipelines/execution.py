__author__='thiagocastroferreira'

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

Author: Duraikrishna Selvaraju and Thiago Castro Ferreira
Date: May 9th 2022
Author: Duraikrishna Selvaraju and Thiago Castro Ferreira
Date: May 9th 2022
Description:
    Simple script to call a platform pipeline through its URL and API key
"""

import time
import json
import requests
import logging

def polling(url:str, api_key:str, name:str="pipeline_process", wait_time:float=1.0, timeout:float=20000.0):
    """
    Keeps polling the platform to check whether an asynchronous call is done
    
    params:
    ---
        url: polling URL
        api_key: api key of the pipeline
        name: Optional. ID given to a call
        wait_time: wait time in seconds between polling calls
        timeout: total polling time
        
    return:
    ---
        success: Boolean variable indicating whether the call finished successfully or not
        resp: response obtained by polling call
    """
    logging.debug(f"Start polling for {name} ({api_key})")
    start, end = time.time(), time.time()
    headers = {
      'x-api-key': api_key,
      'Content-Type': 'application/json'
    }
    completed = False
    response_body = None
    while not completed and (end-start)<timeout:
        try:
            response = requests.get(url, headers=headers)
            response_body = response.json()
            logging.debug(f"Status of polling for {name} ({api_key}): {response_body}")
            completed = response_body['completed']

            end = time.time()
            time.sleep(wait_time)
            if wait_time < 60:
                wait_time *= 1.1
        except Exception:
            logging.exception(f"ERROR: polling for {name} ({api_key}): Continue")
    
    if response_body and response_body['status'] == 'SUCCESS':
        try:
            logging.debug(f"Final status of polling for {name} ({api_key}): SUCCESS - {response_body}")
            return True, response_body
        except Exception:
            logging.debug(f"ERROR: Final status of polling for {name} ({api_key}): ERROR - {response_body}")
            return False, response_body
    else:
        logging.debug(f"ERROR: Final status of polling for {name} ({api_key}): No response in {timeout} seconds - {response_body}")
        return False, response_body


def run(url:str, api_key:str, data:object, name:str="pipeline_process"):
    """
    Runs a pipeline call
    
    params:
    ---
        url: URL of aiXplain's platform where a pipeline call request should be done
        api_key: API key of the pipeline
        data: URL link with the input data to be processed. For now, such link should be a public s3 one
        name: (Optional) ID given to a call
    """
    start = time.time()
    headers = {
      'x-api-key': api_key,
      'Content-Type': 'application/json'
    }
    if type(data) == dict:
        payload = json.dumps(data)
    else:
        payload = json.dumps({ "data": data })
    
    try:
        logging.debug(f"Start service for {name} ({api_key}) - {url} - {payload}")
        r = requests.post(url, headers=headers, data=payload)
        resp = r.json()
        logging.debug(f"Result of request for {name} ({api_key}) - {r.status_code} - {resp}")
        
        poll_url = resp['url']
        end = time.time()
        success, response = polling(poll_url, api_key, name=name)
        return { 'success': success, 'response': response, 'error': None, 'elapsed_time': end-start }
    except Exception:
        error_message = f"Error in request for {name} ({api_key}) - Status code: {r.status_code}"
        logging.error(error_message)
        logging.exception()
        end = time.time()
        return { 'success': False, 'response': None, 'error': error_message, 'elapsed_time': end-start }