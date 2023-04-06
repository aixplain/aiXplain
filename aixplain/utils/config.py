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
"""
import warnings
import os
import logging

logger = logging.getLogger(__name__)

PIPELINES_RUN_URL = os.getenv("PIPELINES_RUN_URL", "https://platform-api.aixplain.com/assets/pipeline/execution/run")
MODELS_RUN_URL = os.getenv("MODELS_RUN_URL", "https://models.aixplain.com/api/v1/execute")
BENCHMARKS_BACKEND_URL = os.getenv("BENCHMARKS_BACKEND_URL", "https://platform-api.aixplain.com")
# GET THE API KEY FROM CMD
TEAM_API_KEY = os.getenv("TEAM_API_KEY", "")
if TEAM_API_KEY == "":
    logger.warning("'TEAM_API_KEY' has not been set properly. For help, please refer to the documentation(https://github.com/aixplain/aiXtend#api-key-setup)")
PIPELINE_API_KEY = os.getenv("PIPELINE_API_KEY", "")
MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")