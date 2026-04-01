"""Helpers for attaching client-side user metadata to execution payloads.

Copyright 2024 The aiXplain SDK authors

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

import logging
from datetime import datetime
from functools import lru_cache
from typing import Dict

import requests


logger = logging.getLogger(__name__)

_IPINFO_URL = "https://ipinfo.io/json"
_IPINFO_TIMEOUT = 2.0


@lru_cache(maxsize=1)
def get_user_location() -> Dict[str, str]:
    """Fetch and cache the user's region and country from ipinfo.io."""
    try:
        response = requests.get(_IPINFO_URL, timeout=_IPINFO_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.debug("Failed to fetch user location from ipinfo.io: %s", exc)
        return {}

    if not isinstance(payload, dict):
        return {}

    location: Dict[str, str] = {}

    region = payload.get("region")
    if isinstance(region, str) and region.strip():
        location["region"] = region.strip()

    country = payload.get("country")
    if isinstance(country, str) and country.strip():
        location["country"] = country.strip()

    return location


def build_user_info() -> Dict[str, str]:
    """Build user metadata for execution payloads.

    Returns:
        Dict[str, str]: User metadata derived from the local client system.
    """
    user_info = {"datetime": datetime.now().astimezone().isoformat()}
    user_info.update(get_user_location())
    return user_info
