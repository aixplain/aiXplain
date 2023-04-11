__author__ = "aiXplain"

"""
Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: March 20th 2023
Description:
    License Enum
"""

import logging
import os
import traceback

from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from enum import Enum


def load_licenses():
    try:
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL

        url = os.path.join(backend_url, "sdk/licenses")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        return Enum("Function", {"_".join(w["name"].split()): w["name"] for w in resp}, type=str)
    except Exception as e:
        logging.exception("License Loading Error")
        raise Exception("License Loading Error")


License = load_licenses()
