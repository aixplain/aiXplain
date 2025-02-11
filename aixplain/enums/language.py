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

from enum import Enum
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.cache_utils import save_to_cache, load_from_cache, CACHE_FOLDER

CACHE_FILE = f"{CACHE_FOLDER}/languages.json"


def load_languages():
    resp = load_from_cache(CACHE_FILE)
    if resp is None:
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL

        url = urljoin(backend_url, "sdk/languages")

        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        if not 200 <= r.status_code < 300:
            raise Exception(
                f'Languages could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
            )
        resp = r.json()
        save_to_cache(CACHE_FILE, resp)

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
