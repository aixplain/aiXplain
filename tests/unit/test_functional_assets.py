"""Unit tests for the functional suite's asset registry (ENG-3685).

`tests/functional/_assets.py` can only be *exercised* against a live backend,
but its contract -- which id space a BACKEND_URL selects, how an override
applies, what happens on a backend it has never heard of -- is pure, so it is
covered here rather than in a leg that needs a credential. Same split as
`tests/cleanup_guards.py` / `tests/unit/test_functional_cleanup.py`.
"""

import pytest

from tests.functional._assets import (
    ASSET_NAMES,
    ASSETS_BY_ENVIRONMENT,
    DEFAULT_BACKEND_URL,
    DEV,
    ENV_PREFIX,
    ENVIRONMENT_ENV,
    UnknownBackendError,
    assets_for,
    environment_for,
    overrides_from,
)

DEV_URL = "https://dev-platform-api.aixplain.com"
TEST_URL = "https://test-platform-api.aixplain.com"
PROD_URL = "https://platform-api.aixplain.com"


@pytest.mark.parametrize(
    ("backend_url", "expected"),
    [
        (DEV_URL, "dev"),
        (TEST_URL, "test"),
        (PROD_URL, "prod"),
    ],
)
def test_backend_url_selects_its_id_space(backend_url, expected):
    """The three backends CI, `main` and a laptop point at."""
    assert environment_for(backend_url, environ={}) == expected


def test_production_is_not_matched_by_its_own_substring():
    """`platform-api.aixplain.com` is a substring of the other two hosts.

    Ordering the markers shortest-last is the only thing stopping every backend
    from resolving to production -- which would validate the CI leg's ids
    against the wrong id space while looking entirely correct.
    """
    assert environment_for(TEST_URL, environ={}) == "test"
    assert environment_for(DEV_URL, environ={}) == "dev"


def test_backend_url_is_read_from_the_environment():
    assert environment_for(environ={"BACKEND_URL": PROD_URL}) == "prod"


def test_the_default_backend_is_the_one_the_v2_conftest_builds_against():
    """An unset BACKEND_URL must pick the id space the client actually talks to."""
    assert environment_for(environ={}) == environment_for(DEFAULT_BACKEND_URL, environ={})


def test_an_unknown_backend_is_an_error_not_a_silent_default():
    """Falling back to `dev` here is how a leg goes green while resolving nothing."""
    with pytest.raises(UnknownBackendError) as excinfo:
        environment_for("https://my-branch.aixplain.dev", environ={})

    message = str(excinfo.value)
    assert "my-branch.aixplain.dev" in message
    assert ENVIRONMENT_ENV in message, "the message must say how to unblock the run"


def test_an_unknown_backend_can_pin_the_id_space_it_mirrors():
    environ = {"BACKEND_URL": "https://my-branch.aixplain.dev", ENVIRONMENT_ENV: "test"}
    assert environment_for(environ=environ) == "test"


def test_a_pinned_id_space_must_be_one_that_exists():
    with pytest.raises(UnknownBackendError):
        environment_for(DEV_URL, environ={ENVIRONMENT_ENV: "staging"})


def test_an_override_replaces_one_id_and_leaves_the_rest():
    override = "a" * 24
    assets = assets_for(DEV_URL, environ={ENV_PREFIX + "DEFAULT_LLM": override})

    assert assets.DEFAULT_LLM == override
    assert assets.SLACK_INTEGRATION == DEV.SLACK_INTEGRATION


def test_an_empty_override_is_not_an_override():
    """An unset CI variable expands to "", which must not blank out an id."""
    assert overrides_from({ENV_PREFIX + "TAVILY": ""}) == {}
    assert assets_for(DEV_URL, environ={ENV_PREFIX + "TAVILY": ""}).TAVILY == DEV.TAVILY


def test_an_unrecognised_override_is_ignored():
    """`AIXPLAIN_TEST_ENV` shares the prefix, and is not an asset name."""
    assert overrides_from({ENV_PREFIX + "NOT_AN_ASSET": "x", ENVIRONMENT_ENV: "dev"}) == {}


@pytest.mark.parametrize("environment", sorted(ASSETS_BY_ENVIRONMENT))
def test_every_environment_defines_every_asset(environment):
    """A `None` here would reach the backend as a request for `/models/None`."""
    assets = ASSETS_BY_ENVIRONMENT[environment]
    missing = [name for name in ASSET_NAMES if not getattr(assets, name)]
    assert not missing, f"{environment} has no id for {missing}"


def test_the_default_llm_matches_the_sdk_default():
    """The suite's DEFAULT_LLM is meant to be the LLM an agent gets when it asks for none.

    `Agent.DEFAULT_LLM` is an SDK constant, not a test fixture, so this is a
    statement about the `dev` id space only -- the backend the SDK's own default
    was chosen against. If they diverge, either the SDK shipped a new default or
    this registry is describing an asset the suite no longer exercises, and both
    are worth a look rather than a silent mismatch.
    """
    from aixplain.v2.agent import Agent

    assert DEV.DEFAULT_LLM == Agent.DEFAULT_LLM


def test_the_non_default_llm_is_not_the_default():
    """`test_agent_llm_persistence.py` proves nothing if these two are the same id."""
    assert DEV.NON_DEFAULT_LLM != DEV.DEFAULT_LLM
