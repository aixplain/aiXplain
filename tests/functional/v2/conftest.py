"""Fixtures for the v2 functional leg: a configured client, and named asset ids."""

import os
import re
from urllib.parse import urlparse

import pytest

from tests.functional._assets import DEFAULT_BACKEND_URL, LazyAssets, assets_for, environment_for

#: The only model-execution endpoint these suites speak.
MODELS_EXECUTE_PATH = "/api/v2/execute"

#: Backend hosts whose models host follows the `<env>-platform-api` ->
#: `<env>-models` naming. Anything else -- localhost, a proxy, a host on another
#: domain -- has no models host that can be guessed from it.
_PLATFORM_API_HOST = re.compile(r"([a-z0-9]+-)?platform-api\.aixplain\.com", re.IGNORECASE)


def _api_key():
    """Return the functional-suite credential, or None.

    The fixtures below that skip on a missing credential repeat this read inline
    rather than calling it: `tests/unit/test_ci_matrix_coverage.py` recognises a
    guarded skip by its `os.getenv` call, and cannot see one behind a helper
    (ENG-3544).
    """
    return os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")


def _backend_url():
    """Return the backend this run targets.

    The default is shared with `tests/functional/_assets.py` rather than
    repeated here: the id space that module selects and the backend this client
    talks to have to be the same one, and two copies of the literal is exactly
    how they would stop being (ENG-3685).

    That default is the test backend, the one CI's non-`main` runs use. It used
    to be dev-platform-api while CI ran these suites against test-platform-api
    (ENG-3683). The asset ids in tests/functional/ exist on one backend at a
    time, so a developer with no BACKEND_URL was validating them against a
    different environment than the one whose result gates a merge -- and each
    side read as "it passes for me".
    """
    return os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL


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


def _build_client():
    """Construct an Aixplain client against the configured backend."""
    from aixplain import Aixplain

    backend_url = _backend_url()
    return Aixplain(
        api_key=_api_key(),
        backend_url=backend_url,
        model_url=_models_run_url(backend_url),
    )


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration for v2 tests."""
    # Require credentials from environment variables for security
    if not (os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")):
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")

    return _build_client()


@pytest.fixture(scope="session")
def assets():
    """The named backend asset ids for the backend this run targets (ENG-3685).

    Tests ask for an asset by name -- ``assets.DEFAULT_LLM``, not a 24-hex
    literal -- so retiring an asset is a one-line change in
    `tests/functional/_assets.py` instead of a sweep through the suite, and a
    single run can point one name somewhere else with
    ``AIXPLAIN_TEST_<NAME>=<id>``.

    Each name is resolved against the backend the first time a test reads it,
    and the outcome is cached for the session (`LazyAssets`). A retired or
    environment-specific id therefore fails only the tests that use it, with a
    message naming the asset, the id, the backend and the override, rather than
    a 404 from deep inside a test body -- and a leg that uses no asset makes no
    resolution call.

    The credential check comes first, so a run with no key skips here even when
    `BACKEND_URL` names a host the asset module does not recognise.
    """
    if not (os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")):
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")

    backend_url = _backend_url()
    return LazyAssets(assets_for(backend_url), _build_client, backend_url, environment_for(backend_url))


@pytest.fixture(scope="module")
def slack_token():
    """Get Slack token for integration tests."""
    # Require Slack token from environment variable for security
    token = os.getenv("SLACK_TOKEN")
    if not token:
        pytest.skip("SLACK_TOKEN environment variable is required for Slack integration tests")
    return token
