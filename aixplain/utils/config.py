"""Copyright 2022 The aiXplain SDK authors.

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

import os
import logging
from typing import Optional

import sentry_sdk

from aixplain.utils.url_safety import UnsafeURLError, validate_config_url

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "https://platform-api.aixplain.com")
MODELS_RUN_URL = os.getenv("MODELS_RUN_URL", "https://models.aixplain.com/api/v1/execute")

#: Set when a configured endpoint failed the policy at import time. The failure
#: is reported again, as a raise, by :func:`ensure_config_urls_safe`.
_DEFERRED_CONFIG_URL_ERROR: Optional[str] = None


def _check_config_url(url: str, name: str) -> None:
    """Apply the config-URL policy to *url*, deferring a failure to first use.

    ``BACKEND_URL`` and ``MODELS_RUN_URL`` are read straight from the
    environment, so any ``.env`` on the machine can choose where the team API
    key is sent -- the policy has to be applied (BUG-939). It is *not* applied
    as an import-time raise, though: this module is imported by ``import
    aixplain`` itself, so raising here would break ``aixplain --help`` and unit
    test collection on a machine with no valid environment (BUG-946).

    The failure is therefore logged once, at WARNING, and re-raised by
    :func:`ensure_config_urls_safe` before the first request actually goes out,
    so nothing is ever sent to a rejected endpoint.
    """
    global _DEFERRED_CONFIG_URL_ERROR
    try:
        validate_config_url(url, name)
    except UnsafeURLError as exc:
        if _DEFERRED_CONFIG_URL_ERROR is None:
            _DEFERRED_CONFIG_URL_ERROR = str(exc)
        logger.warning(f"{exc} No request will be sent until this is fixed.")


def ensure_config_urls_safe() -> None:
    """Raise if a configured endpoint failed the policy at import time.

    Called from the request choke point so an unsafe endpoint is refused before
    a socket is opened, rather than at ``import aixplain``.

    Raises:
        UnsafeURLError: If ``BACKEND_URL`` or ``MODELS_RUN_URL`` is not allowed.
    """
    if _DEFERRED_CONFIG_URL_ERROR is not None:
        raise UnsafeURLError(_DEFERRED_CONFIG_URL_ERROR)


_check_config_url(BACKEND_URL, "BACKEND_URL")
_check_config_url(MODELS_RUN_URL, "MODELS_RUN_URL")
# GET THE API KEY FROM CMD
TEAM_API_KEY = os.getenv("TEAM_API_KEY", "")
AIXPLAIN_API_KEY = os.getenv("AIXPLAIN_API_KEY", "")

ENV = "dev" if "dev" in BACKEND_URL else "test" if "test" in BACKEND_URL else "prod"


def _normalize_api_keys():
    """Reconcile the two API key environment variables. Never raises on absence.

    Importing this module must stay side-effect-safe when no credential is set:
    the unit test suite has to be collectible without one. Only *normalisation*
    happens eagerly, because roughly 40 v1 call sites bind ``config.TEAM_API_KEY``
    as a default argument value, which is evaluated once at import time - so the
    ``AIXPLAIN_API_KEY -> TEAM_API_KEY`` copy has to happen before those modules
    are imported.

    A missing key is instead reported at the point of use: ``Aixplain()`` (v2)
    refuses to construct without one. NOTE: v1 has no equivalent check -- the
    ``@check_api_key`` decorator in ``aixplain/v1/decorators`` is applied to no
    call site, so the import-time raise removed here was the only credential
    error v1 ever produced. A v1 caller with no key now gets a backend 401
    rather than an actionable message. v1 is deprecated, so this is accepted
    rather than fixed here; see ENG-3431.

    Two conflicting keys, on the other hand, are a misconfiguration that can
    only be intentional, so it still fails loudly and early (it cannot fire when
    no key is set, so it never blocks collection).

    Raises:
        Exception: If conflicting API keys are detected
    """
    global TEAM_API_KEY, AIXPLAIN_API_KEY

    if AIXPLAIN_API_KEY and TEAM_API_KEY and AIXPLAIN_API_KEY != TEAM_API_KEY:
        raise Exception(
            "Conflicting API keys: 'AIXPLAIN_API_KEY' and 'TEAM_API_KEY' are both provided but do not match. Please provide only one API key."
        )

    if AIXPLAIN_API_KEY and not TEAM_API_KEY:
        TEAM_API_KEY = AIXPLAIN_API_KEY


def validate_api_keys():
    """Centralized eager API key validation - normalize, then require a key.

    This function handles all API key validation logic:
    1. Auto-normalizes AIXPLAIN_API_KEY to TEAM_API_KEY if needed
    2. Prevents conflicting API keys
    3. Ensures at least one API key is provided

    It is no longer called at import time (see :func:`_normalize_api_keys`), but
    is kept for callers that want the eager, all-or-nothing check.

    Raises:
        Exception: If no API keys are provided or if conflicting keys are detected
    """
    _normalize_api_keys()
    check_api_keys_available()


def check_api_keys_available():
    """Runtime check to ensure API keys are available.

    This is used by decorators and other runtime validation.
    Uses the same validation logic as the module-level check.

    Raises:
        Exception: If no valid API keys are available
    """
    if not TEAM_API_KEY and not AIXPLAIN_API_KEY:
        raise Exception(
            "An API key is required to run this operation. Please set either 'AIXPLAIN_API_KEY' or 'TEAM_API_KEY'. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)"
        )


# Normalize (but do not validate) the API keys at module import time, so that
# importing aixplain never raises just because no credential is configured.
_normalize_api_keys()

PIPELINE_API_KEY = os.getenv("PIPELINE_API_KEY", "")
MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HF_TOKEN = os.getenv("HF_TOKEN", "")
SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENV,
        send_default_pii=True,
    )
