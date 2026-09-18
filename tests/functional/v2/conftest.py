import os
from urllib.parse import urlparse

import pytest


#: The backend an unset BACKEND_URL resolves to.
#:
#: This used to be dev-platform-api while CI ran these suites against
#: test-platform-api (ENG-3683). The hardcoded asset ids in tests/functional/v2/
#: exist on one backend at a time, so a developer with no BACKEND_URL was
#: validating them against a different environment than the one whose result
#: gates a merge -- and each side read as "it passes for me".
DEFAULT_BACKEND_URL = "https://test-platform-api.aixplain.com"

#: The only model-execution endpoint these suites speak.
MODELS_EXECUTE_PATH = "/api/v2/execute"


def _models_run_url(backend_url: str) -> str:
    """The v2 model-execution URL matching *backend_url*.

    Derived rather than defaulted independently: a developer who points
    BACKEND_URL at prod and leaves MODELS_RUN_URL unset would otherwise run the
    suite half against one environment and half against another.

    An explicit MODELS_RUN_URL contributes its *host* only. These suites speak
    the v2 execution API and nothing else, so the path is built here rather than
    trusted from an environment that may be shaped for a different suite.
    """
    explicit = os.getenv("MODELS_RUN_URL")
    if explicit:
        parts = urlparse(explicit)
        return f"{parts.scheme}://{parts.netloc}{MODELS_EXECUTE_PATH}"

    # "test-platform-api..." -> "test-", "dev-platform-api..." -> "dev-",
    # "platform-api..." -> "", which is exactly the models-host prefix.
    hostname = urlparse(backend_url).hostname or ""
    prefix = hostname.split("platform-api")[0]
    return f"https://{prefix}models.aixplain.com{MODELS_EXECUTE_PATH}"


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration for v2 tests."""
    # Require credentials from environment variables for security
    api_key = os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")

    backend_url = os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL

    from aixplain import Aixplain

    return Aixplain(
        api_key=api_key,
        backend_url=backend_url,
        model_url=_models_run_url(backend_url),
    )


@pytest.fixture(scope="module")
def slack_token():
    """Get Slack token for integration tests."""
    # Require Slack token from environment variable for security
    token = os.getenv("SLACK_TOKEN")
    if not token:
        pytest.skip("SLACK_TOKEN environment variable is required for Slack integration tests")
    return token
