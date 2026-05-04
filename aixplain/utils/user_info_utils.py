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

from __future__ import annotations

import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import requests
from babel.languages import get_official_languages


logger = logging.getLogger(__name__)

_IPINFO_URL = "https://ipinfo.io/json"
_IPINFO_TIMEOUT = 2.0


@lru_cache(maxsize=1)
def _fetch_ipinfo() -> Dict[str, Any]:
    """Fetch and cache the ipinfo.io payload for the current public IP."""
    try:
        response = requests.get(_IPINFO_URL, timeout=_IPINFO_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.debug("Failed to fetch ipinfo.io payload: %s", exc)
        return {}

    if not isinstance(payload, dict):
        return {}

    return payload


def _primary_language_for_territory(cc: str) -> Optional[str]:
    """Most preferred official language for the country code"""
    langs = get_official_languages(cc, de_facto=True)
    if not langs:
        langs = get_official_languages(cc)
    if not langs:
        return None
    return langs[0].split("_")[0].lower()


def _region_and_language_from_country(country: str) -> Tuple[Optional[str], Optional[str]]:
    """Build region and language from ipinfo country or (None, None) if unknown."""
    cc = country.strip().upper()
    if len(cc) != 2:
        return (None, None)
    lang = _primary_language_for_territory(cc)
    if not lang:
        return (None, None)
    return (f"{lang}-{cc}", lang)


def build_run_metadata() -> Dict[str, Any]:
    """Build metaData for agent run payloads.

    Returns:
        Dict[str, Any]: Metadata suitable for the metaData JSON field.
    """
    meta: Dict[str, Any] = {
        "userAgent": "sdk",
        "datetime": datetime.now().isoformat(),
        "region": None,
        "language": None,
        "ipAddress": None,
        "latitude": None,
        "longitude": None,
        "timezone": None,
    }

    info = _fetch_ipinfo()

    country = info.get("country")
    if isinstance(country, str) and len(country.strip()) == 2:
        region, language = _region_and_language_from_country(country.strip())
        meta["region"] = region
        meta["language"] = language

    ip = info.get("ip")
    if isinstance(ip, str) and ip.strip():
        meta["ipAddress"] = ip.strip()

    loc = info.get("loc")
    if isinstance(loc, str) and "," in loc:
        try:
            lat_s, lon_s = loc.split(",", 1)
            meta["latitude"] = float(lat_s.strip())
            meta["longitude"] = float(lon_s.strip())
        except ValueError:
            pass

    tz = info.get("timezone")
    if isinstance(tz, str) and tz.strip():
        meta["timezone"] = tz.strip()

    return meta
