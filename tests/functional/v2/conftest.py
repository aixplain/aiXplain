"""Fixtures for the v2 functional leg: a configured client, and named asset ids."""

import os

import pytest

from tests.functional._assets import (
    ASSET_NAMES,
    DEFAULT_BACKEND_URL,
    ENV_PREFIX,
    SPECS,
    assets_for,
    environment_for,
)


def _api_key():
    """Return the functional-suite credential, or None."""
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
    if not _api_key():
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
    """
    return assets_for(_backend_url())


@pytest.fixture(scope="session", autouse=True)
def verify_assets_resolve(assets):
    """Resolve every named asset once, before any test runs.

    Without this, a retired or environment-specific id surfaces as a 404 inside
    whichever test reaches it first, in a leg whose other failures look the
    same. Resolving up front turns that into one message naming the asset, the
    id, the backend and the override that unblocks the run.

    Every id is attempted before anything is reported, so a backend the suite
    has never run against lists all of its gaps in one go rather than one per
    push.
    """
    if not _api_key():
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")

    client = _build_client()
    backend_url = _backend_url()
    environment = environment_for(backend_url)

    missing = []
    for name in ASSET_NAMES:
        spec = SPECS[name]
        asset_id = getattr(assets, name)
        try:
            getattr(client, spec.resource).get(asset_id)
        except Exception as error:  # noqa: BLE001 - any failure to resolve is the failure being reported
            missing.append(f"  {name} ({spec.description}) = {asset_id} via client.{spec.resource}.get: {error}")

    if missing:
        pytest.fail(
            f"{len(missing)} of {len(ASSET_NAMES)} functional-test assets did not resolve on "
            f"{backend_url} (id space {environment!r}):\n"
            + "\n".join(missing)
            + f"\n\nFix the id in tests/functional/_assets.py, or point one name elsewhere for this "
            f"run with {ENV_PREFIX}<NAME>=<id>.",
            pytrace=False,
        )


@pytest.fixture(scope="module")
def slack_token():
    """Get Slack token for integration tests."""
    # Require Slack token from environment variable for security
    token = os.getenv("SLACK_TOKEN")
    if not token:
        pytest.skip("SLACK_TOKEN environment variable is required for Slack integration tests")
    return token
