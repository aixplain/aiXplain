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
from aixplain.utils.asset_cache import AssetCache
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class LanguageMetadata:
    """Metadata container for language information.

    This class holds metadata about a language including its identifier, value,
    label, dialects, and supported scripts.

    Attributes:
        id (str): ID of the language.
        value (str): Language code or value.
        label (str): Label for the language.
        dialects (List[Dict[str, str]]): List of dialect specifications.
        scripts (List[Any]): List of supported scripts for the language.
    """
    id: str
    value: str
    label: str
    dialects: List[Dict[str, str]] = field(default_factory=list)
    scripts: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert the language metadata to a dictionary.

        Returns:
            dict: Dictionary representation of the language metadata.
        """
        return {
            "id": self.id,
            "value": self.value,
            "label": self.label,
            "dialects": self.dialects,
            "scripts": self.scripts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LanguageMetadata":
        """Create a LanguageMetadata instance from a dictionary.

        Args:
            data (dict): Dictionary containing language metadata.

        Returns:
            LanguageMetadata: New instance created from the dictionary data.
        """
        return cls(
            id=data.get("id"),
            value=data.get("value"),
            label=data.get("label"),
            dialects=data.get("dialects", []),
            scripts=data.get("scripts", []),
        )

def load_languages() -> Enum:
    """Load language definitions from the backend or cache.

    This function attempts to load language definitions from the cache first.
    If the cache is invalid or doesn't exist, it fetches the data from the
    backend API. It creates a dynamic Enum class containing all available
    languages and their dialects.

    Returns:
        Enum: Dynamically created Language enum class with language codes and dialects.

    Raises:
        Exception: If languages cannot be loaded due to invalid API key or other errors.
    """
    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    url = urljoin(backend_url, "sdk/languages")
    cache = AssetCache(LanguageMetadata, cache_filename="languages")

    if cache.has_valid_cache():
        logging.info("Loading languages from cache...")
        lang_entries = list(cache.store.data.values())
    else:
        logging.info("Fetching languages from backend...")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        if not 200 <= r.status_code < 300:
            raise Exception(
                f'Languages could not be loaded, probably due to the set API key (e.g. "{api_key}") is not valid. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)'
            )
        resp = r.json()
        lang_entries = [LanguageMetadata.from_dict(item) for item in resp]
        cache.add_list(lang_entries)

    languages = {}
    for entry in lang_entries:
        language = entry.value
        label = "_".join(entry.label.split())
        languages[label] = {"language": language, "dialect": ""}
        for dialect in entry.dialects:
            dialect_label = "_".join(dialect["label"].split()).upper()
            dialect_value = dialect["value"]
            languages[f"{label}_{dialect_label}"] = {
                "language": language,
                "dialect": dialect_value,
            }

    return Enum("Language", languages, type=dict)


Language = load_languages()
