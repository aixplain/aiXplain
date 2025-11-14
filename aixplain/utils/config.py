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
import sentry_sdk

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "https://platform-api.aixplain.com")
MODELS_RUN_URL = os.getenv(
    "MODELS_RUN_URL", "https://models.aixplain.com/api/v1/execute"
)
# GET THE API KEY FROM CMD
TEAM_API_KEY = os.getenv("TEAM_API_KEY", "")
AIXPLAIN_API_KEY = os.getenv("AIXPLAIN_API_KEY", "")

ENV = "dev" if "dev" in BACKEND_URL else "test" if "test" in BACKEND_URL else "prod"


def validate_api_keys():
    """Centralized API key validation function - single source of truth.

    This function handles all API key validation logic:
    1. Ensures at least one API key is provided
    2. Prevents conflicting API keys
    3. Auto-normalizes AIXPLAIN_API_KEY to TEAM_API_KEY if needed

    Raises:
        Exception: If no API keys are provided or if conflicting keys are detected
    """
    global TEAM_API_KEY, AIXPLAIN_API_KEY

    if not TEAM_API_KEY and not AIXPLAIN_API_KEY:
        raise Exception(
            "Neither 'AIXPLAIN_API_KEY' nor 'TEAM_API_KEY' has been set. Please set either environment variable. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)"
        )

    if AIXPLAIN_API_KEY and TEAM_API_KEY and AIXPLAIN_API_KEY != TEAM_API_KEY:
        raise Exception(
            "Conflicting API keys: 'AIXPLAIN_API_KEY' and 'TEAM_API_KEY' are both provided but do not match. Please provide only one API key."
        )

    if AIXPLAIN_API_KEY and not TEAM_API_KEY:
        TEAM_API_KEY = AIXPLAIN_API_KEY


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


# Perform initial validation at module import time
validate_api_keys()

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
