"""Fixtures for the v2 functional leg: a configured client, and named asset ids."""

import os

import pytest

from tests.functional._assets import DEFAULT_BACKEND_URL, LazyAssets, assets_for, environment_for


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
    """
    return os.getenv("BACKEND_URL") or DEFAULT_BACKEND_URL


def _build_client():
    """Construct an Aixplain client against the configured backend."""
    # V2 tests require V2 model URL - ensure we use /api/v2/ even if env has /api/v1/
    model_url = os.getenv("MODELS_RUN_URL") or "https://dev-models.aixplain.com/api/v2/execute"
    model_url = model_url.replace("/api/v1/", "/api/v2/")

    from aixplain import Aixplain

    return Aixplain(
        api_key=_api_key(),
        backend_url=_backend_url(),
        model_url=model_url,
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
