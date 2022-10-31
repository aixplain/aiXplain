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
    Pipeline Factory Class
"""

from aixtend.modules.pipeline import Pipeline
from aixtend.utils.config import PIPELINES_RUN_URL

class PipelineFactory:

    @staticmethod
    def initialize(api_key: str, url: str = PIPELINES_RUN_URL) -> Pipeline:
        """
        params:
        ---
            api_key: API key of the pipeline
            url: API endpoint
        """
        return Pipeline(api_key=api_key, url=url)
