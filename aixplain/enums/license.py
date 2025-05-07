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
from enum import Enum
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.asset_cache import AssetCache, CACHE_FOLDER

from dataclasses import dataclass

@dataclass
class LicenseMetadata:
    id: str
    name: str
    description: str
    url: str
    allowCustomUrl: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "allowCustomUrl": self.allowCustomUrl,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            url=data.get("url"),
            allowCustomUrl=data.get("allowCustomUrl", False),
        )


def load_licenses():

    try:
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL

        url = urljoin(backend_url, "sdk/licenses")
        cache = AssetCache(LicenseMetadata, cache_filename="licenses")

        if cache.has_valid_cache():
            logging.info("Loading licenses from cache...")
            license_objects = list(cache.store.data.values())
        else:
            logging.info("Fetching licenses from backend...")
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            if not 200 <= r.status_code < 300:
                raise Exception(
                    f'Licenses could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation.'
                )
            resp = r.json()
            license_objects = [LicenseMetadata.from_dict(item) for item in resp]
            cache.add_list(license_objects)

        licenses = {"_".join(lic.name.split()): lic.id for lic in license_objects}
        return Enum("License", licenses, type=str)
    except Exception:
        logging.exception("License Loading Error")
        raise Exception("License Loading Error")


License = load_licenses()
