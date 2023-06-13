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
Date: March 22th 2023
Description:
    Language Enum
"""

import logging

from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from enum import Enum
from urllib.parse import urljoin


def load_languages():
    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    url = urljoin(backend_url, "sdk/languages")
    if aixplain_key != "":
        api_key = aixplain_key
        headers = {"x-aixplain-key": aixplain_key, "Content-Type": "application/json"}
    else:
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    r = _request_with_retry("get", url, headers=headers)
    if not 200 <= r.status_code < 300:
        raise Exception(
            f'Languages could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
        )
    resp = r.json()
    languages = {}
    for w in resp:
        language = w["value"]
        language_label = "_".join(w["label"].split())
        languages[language_label] = {"language": language, "dialect": ""}
        for dialect in w["dialects"]:
            dialect_label = "_".join(dialect["label"].split()).upper()
            dialect_value = dialect["value"]

            languages[language_label + "_" + dialect_label] = {"language": language, "dialect": dialect_value}
    return Enum("Language", languages, type=dict)


Language = load_languages()
