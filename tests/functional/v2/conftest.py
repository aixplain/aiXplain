import os
import re
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

#: Backend hosts whose models host follows the `<env>-platform-api` ->
#: `<env>-models` naming. Anything else -- localhost, a proxy, a host on another
#: domain -- has no models host that can be guessed from it.
_PLATFORM_API_HOST = re.compile(r"([a-z0-9]+-)?platform-api\.aixplain\.com", re.IGNORECASE)


def _models_run_url(backend_url: str) -> str:
    """The v2 model-execution URL matching *backend_url*.

    Derived rather than defaulted independently: a developer who points
    BACKEND_URL at prod and leaves MODELS_RUN_URL unset would otherwise run the
    suite half against one environment and half against another.

    An explicit MODELS_RUN_URL contributes its *host* only. These suites speak
    the v2 execution API and nothing else, so the path is always built here: a
    `/api/v1/` URL left over in a developer's shell cannot send them to the wrong
    endpoint.

    Raises:
        ValueError: MODELS_RUN_URL is set but is not an absolute URL, or it is
            unset and BACKEND_URL is not an aiXplain `platform-api` host, so
            there is no models host to derive. Guessing used to turn
            `http://localhost:8000` into `https://localhostmodels.aixplain.com`,
            and any host that merely *starts* with `platform-api` into the
            production models host (ENG-3683).
    """
    explicit = os.getenv("MODELS_RUN_URL")
    if explicit:
        parts = urlparse(explicit)
        if not parts.scheme or not parts.netloc:
            raise ValueError(
                f"MODELS_RUN_URL={explicit!r} is not an absolute URL; set it to something like "
                f"'https://test-models.aixplain.com{MODELS_EXECUTE_PATH}'."
            )
        return f"{parts.scheme}://{parts.netloc}{MODELS_EXECUTE_PATH}"

    hostname = urlparse(backend_url).hostname or ""
    match = _PLATFORM_API_HOST.fullmatch(hostname)
    if not match:
        raise ValueError(
            f"cannot derive the models host from BACKEND_URL={backend_url!r}: only "
            "'<env>-platform-api.aixplain.com' and 'platform-api.aixplain.com' map to a known models host. "
            "Set MODELS_RUN_URL explicitly for this backend."
        )

    # "test-" -> "test-models...", "dev-" -> "dev-models...", no prefix -> "models...".
    prefix = (match.group(1) or "").lower()
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
