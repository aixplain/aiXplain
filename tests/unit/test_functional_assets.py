"""Unit tests for the functional suite's asset registry (ENG-3685).

`tests/functional/_assets.py` can only be *exercised* against a live backend,
but its contract -- which id space a BACKEND_URL selects, how an override
applies, what happens on a backend it has never heard of -- is pure, so it is
covered here rather than in a leg that needs a credential. Same split as
`tests/cleanup_guards.py` / `tests/unit/test_functional_cleanup.py`.
"""

import pytest

import ast
from pathlib import Path

from tests.functional._assets import (
    ASSET_NAMES,
    ASSETS_BY_ENVIRONMENT,
    DEFAULT_BACKEND_URL,
    DEV,
    ENV_PREFIX,
    ENVIRONMENT_ENV,
    SPECS,
    ConflictingEnvironmentError,
    LazyAssets,
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


def test_production_is_not_matched_by_its_own_suffix():
    """`platform-api.aixplain.com` is a suffix of the other two hosts.

    A substring match would read every backend as production -- validating the
    CI leg's ids against the wrong id space while looking entirely correct --
    so hosts are looked up exactly.
    """
    assert environment_for(TEST_URL, environ={}) == "test"
    assert environment_for(DEV_URL, environ={}) == "dev"


def test_backend_url_is_read_from_the_environment():
    """With no argument, `BACKEND_URL` picks the id space."""
    assert environment_for(environ={"BACKEND_URL": PROD_URL}) == "prod"


def test_the_host_is_matched_case_insensitively():
    """Hostnames are case-insensitive, so an upper-cased URL is still the test backend."""
    assert environment_for("https://TEST-Platform-API.aixplain.com/api/v2", environ={}) == "test"


@pytest.mark.parametrize(
    "backend_url",
    [
        "https://staging-platform-api.aixplain.com",
        "https://example.com/?u=test-platform-api.aixplain.com",
        "https://test-platform-api.aixplain.com.example.com",
    ],
    ids=["staging-host", "host-in-query-string", "host-as-subdomain"],
)
def test_only_the_exact_host_selects_an_id_space(backend_url):
    """A host that merely contains a known one is not that backend."""
    with pytest.raises(UnknownBackendError):
        environment_for(backend_url, environ={})


def test_the_default_backend_is_the_one_the_v2_conftest_builds_against():
    """An unset BACKEND_URL must pick the id space the client actually talks to."""
    assert environment_for(environ={}) == environment_for(DEFAULT_BACKEND_URL, environ={})


def test_an_unset_backend_selects_the_test_id_space():
    """The default backend is the one CI's non-`main` runs use, not dev (ENG-3683).

    `TEST` is `DEV` until an entry in `_assets.py` says otherwise, so moving the
    default changed which id space is selected but not which ids are read.
    """
    assert DEFAULT_BACKEND_URL == TEST_URL
    assert environment_for(environ={}) == "test"
    assert assets_for(environ={}) == ASSETS_BY_ENVIRONMENT["test"]


def test_an_unknown_backend_is_an_error_not_a_silent_default():
    """Falling back to `dev` here is how a leg goes green while resolving nothing."""
    with pytest.raises(UnknownBackendError) as excinfo:
        environment_for("https://my-branch.aixplain.dev", environ={})

    message = str(excinfo.value)
    assert "my-branch.aixplain.dev" in message
    assert ENVIRONMENT_ENV in message, "the message must say how to unblock the run"


def test_an_unknown_backend_can_pin_the_id_space_it_mirrors():
    """`AIXPLAIN_TEST_ENV` names the id space a backend this module does not know mirrors."""
    environ = {"BACKEND_URL": "https://my-branch.aixplain.dev", ENVIRONMENT_ENV: " test "}
    assert environment_for(environ=environ) == "test"


def test_a_whitespace_only_pin_is_not_a_pin():
    """A blank `AIXPLAIN_TEST_ENV` must not stand in for a real choice."""
    with pytest.raises(UnknownBackendError):
        environment_for("https://my-branch.aixplain.dev", environ={ENVIRONMENT_ENV: "   "})


def test_a_pinned_id_space_must_be_one_that_exists():
    """A typo in `AIXPLAIN_TEST_ENV` is an error, whatever the backend."""
    with pytest.raises(UnknownBackendError):
        environment_for(DEV_URL, environ={ENVIRONMENT_ENV: "staging"})


def test_a_pin_that_agrees_with_a_recognised_host_is_accepted():
    """Pinning the id space a host already selects changes nothing."""
    assert environment_for(TEST_URL, environ={ENVIRONMENT_ENV: "test"}) == "test"


def test_a_pin_that_contradicts_a_recognised_host_is_an_error():
    """Either answer would validate one backend's ids against another backend."""
    with pytest.raises(ConflictingEnvironmentError) as excinfo:
        environment_for(TEST_URL, environ={ENVIRONMENT_ENV: "prod"})

    message = str(excinfo.value)
    assert ENVIRONMENT_ENV in message
    assert "'test'" in message and "'prod'" in message


def test_an_override_replaces_one_id_and_leaves_the_rest():
    """`AIXPLAIN_TEST_<NAME>` swaps exactly one id."""
    override = "a" * 24
    assets = assets_for(DEV_URL, environ={ENV_PREFIX + "DEFAULT_LLM": override})

    assert assets.DEFAULT_LLM == override
    assert assets.SLACK_INTEGRATION == DEV.SLACK_INTEGRATION


def test_an_empty_override_is_not_an_override():
    """An unset CI variable expands to "", which must not blank out an id."""
    assert overrides_from({ENV_PREFIX + "TAVILY": ""}) == {}
    assert assets_for(DEV_URL, environ={ENV_PREFIX + "TAVILY": ""}).TAVILY == DEV.TAVILY


def test_a_whitespace_only_override_is_not_an_override():
    """A value of spaces is as unset as an empty one, and a real value loses its padding."""
    assert overrides_from({ENV_PREFIX + "TAVILY": "  \t"}) == {}
    assert overrides_from({ENV_PREFIX + "TAVILY": " " + "b" * 24 + "\n"}) == {"TAVILY": "b" * 24}


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


# ---------------------------------------------------------------------------
# LazyAssets: per-name resolution through SPECS
# ---------------------------------------------------------------------------


class _FakeResource:
    """Stands in for `client.Model` and friends: records each `get` and fails for *missing* ids."""

    def __init__(self, name, calls, missing):
        self._name = name
        self._calls = calls
        self._missing = missing

    def get(self, asset_id):
        self._calls.append((self._name, asset_id))
        if asset_id in self._missing:
            raise RuntimeError(f"404 {asset_id} not found")
        return object()


class _FakeClient:
    """An `Aixplain` client whose resources are `_FakeResource`s sharing one call log."""

    def __init__(self, missing=()):
        self.calls = []
        for resource in {spec.resource for spec in SPECS.values()}:
            setattr(self, resource, _FakeResource(resource, self.calls, set(missing)))


def _lazy(client, ids=DEV):
    """A `LazyAssets` over *ids* that builds *client* on demand and counts how often."""
    built = []

    def factory():
        built.append(client)
        return client

    return LazyAssets(ids, factory, DEV_URL, "dev"), built


def test_lazy_assets_resolve_nothing_until_read():
    """A leg that uses no asset must not touch the backend, or even build a client."""
    client = _FakeClient()
    assets, built = _lazy(client)

    assert client.calls == []
    assert built == []
    assert isinstance(assets, LazyAssets)


def test_a_read_resolves_through_its_spec_once_and_returns_the_id():
    """`assets.X` is the id string, after one `client.<resource>.get(id)`, and only for X."""
    client = _FakeClient()
    assets, built = _lazy(client)

    assert assets.FIRECRAWL == DEV.FIRECRAWL
    assert getattr(assets, "FIRECRAWL") == DEV.FIRECRAWL
    assert assets.DEFAULT_LLM == DEV.DEFAULT_LLM

    assert client.calls == [(SPECS["FIRECRAWL"].resource, DEV.FIRECRAWL), ("Model", DEV.DEFAULT_LLM)]
    assert len(built) == 1, "the client is built once, on the first resolution"


def test_a_missing_asset_fails_the_reading_test_by_name():
    """The failure names the asset, its id, the backend, the call and the override."""
    client = _FakeClient(missing={DEV.TAVILY})
    assets, _ = _lazy(client)

    with pytest.raises(pytest.fail.Exception) as excinfo:
        assets.TAVILY

    message = str(excinfo.value)
    for expected in ("TAVILY", SPECS["TAVILY"].description, DEV.TAVILY, DEV_URL, "'dev'", "client.Tool.get"):
        assert expected in message
    assert f"404 {DEV.TAVILY} not found" in message
    assert f"{ENV_PREFIX}TAVILY=<id>" in message


def test_a_failure_is_cached_so_a_rerun_does_not_repeat_the_request():
    """`@flaky` reruns read the same name again; the backend is asked once."""
    client = _FakeClient(missing={DEV.TAVILY})
    assets, _ = _lazy(client)

    for _ in range(3):
        with pytest.raises(pytest.fail.Exception):
            assets.TAVILY

    assert client.calls == [("Tool", DEV.TAVILY)]


def test_one_missing_asset_does_not_fail_the_others():
    """The blast radius of a retired id is the tests that read it."""
    client = _FakeClient(missing={DEV.SEEDREAM_MODEL})
    assets, _ = _lazy(client)

    with pytest.raises(pytest.fail.Exception):
        assets.SEEDREAM_MODEL
    assert assets.SLACK_INTEGRATION == DEV.SLACK_INTEGRATION


def test_a_client_that_cannot_be_built_fails_the_read_rather_than_the_session():
    """Construction errors are resolution errors, reported against the asset that needed them."""

    def factory():
        raise ValueError("bad model url")

    assets = LazyAssets(DEV, factory, DEV_URL, "dev")

    with pytest.raises(pytest.fail.Exception, match="bad model url"):
        assets.DEFAULT_LLM


def test_an_unknown_name_is_an_attribute_error():
    """A typo is a plain AttributeError, not a backend call."""
    client = _FakeClient()
    assets, built = _lazy(client)

    with pytest.raises(AttributeError, match="NOT_AN_ASSET"):
        assets.NOT_AN_ASSET
    assert built == []


V2_CONFTEST = Path(__file__).resolve().parents[1] / "functional" / "v2" / "conftest.py"


def test_no_autouse_fixture_in_the_v2_conftest_resolves_assets():
    """Resolution is per name, on read; an autouse fixture would put it back on every leg."""
    autouse = [
        node.name
        for node in ast.walk(ast.parse(V2_CONFTEST.read_text()))
        if isinstance(node, ast.FunctionDef)
        and any("autouse" in ast.dump(decorator) for decorator in node.decorator_list)
    ]
    assert autouse == [], f"autouse fixtures in tests/functional/v2/conftest.py: {autouse}"
