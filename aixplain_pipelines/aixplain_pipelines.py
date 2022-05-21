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
Description:
    Pipeline Class
    
"""

import logging

import aixplain_pipelines.execution as execution
from aixplain_pipelines.utils.config import PIPELINES_RUN_URL

class Pipeline:
    def __init__(self, api_key:str, url:str=PIPELINES_RUN_URL):
        """
        params:
        ---
            api_key: API key of the pipeline
            url: API endpoint
        """
        self.url = url
        self.api_key = api_key


    def run(self, data:str, name:str="pipeline_process"):
        """
        params:
        ---
            data: link to the input data
            name: name to the process
        """
        logging.info(f"Started pipeline run with process name: {name}")
        result = execution.run(self.url, self.api_key, data, name=name)
        logging.info(f"Completed pipeline run with process name: {name}")
        return result