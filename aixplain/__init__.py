"""
aiXplain SDK Library.
---

aiXplain SDK enables python programmers to add AI functions
to their software.

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

# Set default logging handler to avoid "No handler found" warnings.
import os
import logging
from logging import NullHandler

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logging.getLogger(__name__).addHandler(NullHandler())

# Load Environment Variables
from dotenv import load_dotenv

load_dotenv()

# Validate API keys
from aixplain.utils import config

if config.TEAM_API_KEY == "" and config.AIXPLAIN_API_KEY == "":
    raise Exception(
        "'TEAM_API_KEY' has not been set properly and is empty. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)"
    )
