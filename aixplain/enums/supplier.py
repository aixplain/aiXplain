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
Date: September 25th 2023
Description:
    Supplier Enum
"""

import logging

from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from enum import Enum
from urllib.parse import urljoin
import re


def clean_name(name):
    cleaned_name = re.sub(r"[ -]+", "_", name)
    cleaned_name = re.sub(r"[^a-zA-Z0-9_]", "", cleaned_name)
    cleaned_name = re.sub(r"^\d+", "", cleaned_name)
    return cleaned_name.upper()


def load_suppliers():
    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    url = urljoin(backend_url, "sdk/suppliers")
    if aixplain_key != "":
        api_key = aixplain_key
        headers = {"x-aixplain-key": aixplain_key, "Content-Type": "application/json"}
    else:
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    r = _request_with_retry("get", url, headers=headers)
    if not 200 <= r.status_code < 300:
        raise Exception(
            f'Suppliers could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
        )
    resp = r.json()
    suppliers = Enum(
        "Supplier", {clean_name(w["name"]): {"id": w["id"], "name": w["name"], "code": w["code"]} for w in resp}, type=dict
    )

    return suppliers


Supplier = load_suppliers()
