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
import json
import time
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry

CACHE_FILE = ".aixplain_cache/licenses.json"
CACHE_DURATION = timedelta(hours=24)

def save_to_cache(licenses):
    cache_data = {
        "timestamp": time.time(),
        "licenses": licenses,
    }
    temp_file = CACHE_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(temp_file, "w") as f:
            json.dump(cache_data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, CACHE_FILE)
        logging.info("Licenses cache saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save licenses cache: {e}")

def load_from_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f)
            timestamp = cache_data["timestamp"]
            licenses = cache_data["licenses"]
            return licenses, timestamp
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Failed to load licenses cache: {e}")
        raise e
    
def load_licenses():
    if os.path.exists(CACHE_FILE):
        try:
            licenses, timestamp = load_from_cache()
            cache_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - cache_time < CACHE_DURATION:
                logging.info("Loaded licenses from cache.")
                return Enum("License", licenses, type=str)
        except Exception as e:
            logging.warning(f"Failed to load licenses cache: {e}. Refreshing licenses.")

    try:
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL

        url = urljoin(backend_url, "sdk/licenses")

        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        if not 200 <= r.status_code < 300:
            raise Exception(
                f'Licenses could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
            )
        resp = r.json()
        licenses = {"_".join(w["name"].split()): w["id"] for w in resp}
        
        save_to_cache(licenses)
        return Enum("License", licenses, type=str)
    except Exception as e:
        logging.exception("License Loading Error")
        raise Exception("License Loading Error")


License = load_licenses()
