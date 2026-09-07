"""Client-side run metadata attached to agent execution payloads.

Agent runs carry a ``metaData`` object built by :func:`build_run_metadata`. It
reports the caller's environment to the aiXplain backend so runs can be
locale-aware: ``region``, ``language`` and ``timezone``, plus the public
``ipAddress`` and city-level ``latitude`` / ``longitude`` they are derived from.

Those values come from a single ``https://ipinfo.io/json`` request made from the
machine running the SDK, cached once per process and skipped silently on failure.
See ``docs/run-metadata.md`` for the user-facing disclosure: every field, why it
is collected, which call sites send it, and what happens when the lookup is
blocked.

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
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import requests
from babel.languages import get_official_languages


logger = logging.getLogger(__name__)

_IPINFO_URL = "https://ipinfo.io/json"
_IPINFO_TIMEOUT = 2.0


@lru_cache(maxsize=1)
def _fetch_ipinfo() -> Dict[str, Any]:
    """Fetch and cache the ipinfo.io payload for the current public IP.

    Issues one ``GET https://ipinfo.io/json`` from the machine running the SDK,
    bounded by a ``_IPINFO_TIMEOUT``-second timeout. The response describes the
    host's egress connection — its public IP, country, city-level coordinates and
    IANA timezone; :func:`build_run_metadata` forwards those fields to the
    backend. ipinfo.io receives only the bare request: no API key, no query text,
    and no agent data.

    ``lru_cache(maxsize=1)`` makes this exactly one request per Python process,
    on the first agent run. The cache also memoises failures, so a blocked or
    unreachable lookup costs the timeout once and never retries.

    All errors degrade silently to ``{}`` — this is auxiliary metadata
    and an outage / network-isolation / test-mock should never break a
    caller's run.

    Returns:
        Dict[str, Any]: The decoded ipinfo.io response, or ``{}`` on any failure.
    """
    try:
        response = requests.get(_IPINFO_URL, timeout=_IPINFO_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        # Best-effort telemetry/geo lookup: it must never break an agent run, no matter
        # what requests raises (network errors, JSON errors, or a test's requests_mock
        # NoMockAddress, which is not a requests.RequestException).
        logger.debug("Failed to fetch ipinfo.io payload: %s", exc)
        return {}

    if not isinstance(payload, dict):
        return {}

    return payload


def _primary_language_for_territory(cc: str) -> Optional[str]:
    """Most preferred official language for the country code."""
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
    """Build the ``metaData`` object sent with every agent run payload.

    The returned dict is forwarded verbatim to the backend by the v2 agent run
    path (:meth:`aixplain.v2.agent.Agent.build_run_payload`) and by the legacy v1
    agent / team-agent run and session-bootstrap paths. It is derived from one
    cached ``https://ipinfo.io/json`` lookup (see :func:`_fetch_ipinfo`).

    Keys, all present on every call:

    * ``userAgent`` — always ``"sdk"``, marking the traffic as SDK-originated.
    * ``region`` / ``language`` — locale derived from the lookup's country code,
      used for locale-aware agent execution.
    * ``ipAddress`` — the SDK host's public IP address.
    * ``latitude`` / ``longitude`` — city-level coordinates for that IP.
    * ``timezone`` — IANA timezone name for that IP.

    Every key except ``userAgent`` is ``None`` when the lookup failed, was blocked
    or omitted the underlying field; a run is never blocked by it.
    ``docs/run-metadata.md`` carries the user-facing disclosure.

    Returns:
        Dict[str, Any]: The run payload's ``metaData`` value.
    """
    meta: Dict[str, Any] = {
        "userAgent": "sdk",
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
