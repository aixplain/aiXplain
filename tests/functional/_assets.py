"""Named backend asset ids for the functional suite (ENG-3685).

Before this module, every functional test that needed a platform asset carried
the raw ObjectId inline: 24 hex characters, no name, no owner, no way to point a
run at a different backend. The same default LLM appeared in four v2 files and
the Slack integration in six, and the Firecrawl and Tavily ids were repeated
between the agent and tool suites.

Those literals are not portable. CI validates them against
``test-platform-api``, a push to ``main`` validates them against production, and
a laptop validated them against ``dev-platform-api`` -- the suite's default
backend until ENG-3683 moved it to ``test-platform-api`` (see
``DEFAULT_BACKEND_URL`` below). Those are three separate id spaces, so a retired
asset failed one leg at a time and each failure read as an unrelated backend
error from somewhere deep inside a test body.

This module is the single source. Ask for an asset by name::

    def test_something(client, assets):
        model = client.Model.get(assets.DEFAULT_LLM)

``assets`` is the session fixture in ``tests/functional/v2/conftest.py``. It
picks the id set for the backend this run points at and hands back a
:class:`LazyAssets`, which resolves a name the first time a test reads it. A
retired asset therefore fails the tests that use it, by name, with the id, the
backend and the override that unblocks the run -- and no other test. A leg that
reads no asset makes no resolution call at all.

Retiring an id is a one-line change here. Overriding one for a single run is an
environment variable -- ``AIXPLAIN_TEST_<NAME>``, e.g.
``AIXPLAIN_TEST_DEFAULT_LLM=<id>`` -- which is also how a backend this module
does not know about (a branch deployment, a tunnel, a local stack) gets a
working id without a commit.

``tests/unit/test_functional_hygiene.py`` fails if a bare 24-hex literal
reappears anywhere under ``tests/functional/``, which is what keeps this module
the only source rather than merely the first one. ``tests/functional/v2`` is the
whole functional suite now that the v1 legs are gone (PROD-2918), so the guard
has no exemptions.

Copyright 2022 The aiXplain SDK authors

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
from dataclasses import dataclass, fields, replace
from typing import Any, Callable, Dict, Mapping, Optional, Tuple
from urllib.parse import urlparse

import pytest

#: Prefix for the per-asset override, e.g. ``AIXPLAIN_TEST_SLACK_INTEGRATION``.
#: The suffix is the field name on :class:`AssetIds` exactly as spelled there.
ENV_PREFIX = "AIXPLAIN_TEST_"

#: Pins the id space when ``BACKEND_URL`` names a host this module does not
#: recognise. Values are the keys of :data:`ASSETS_BY_ENVIRONMENT`. Ignored for
#: a recognised host unless it disagrees, which is an error rather than a
#: silent choice between the two.
ENVIRONMENT_ENV = "AIXPLAIN_TEST_ENV"

#: The backend a run with no ``BACKEND_URL`` talks to. ``tests/functional/v2/
#: conftest.py`` imports this rather than repeating the literal, so the id space
#: this module selects and the backend the client is built against cannot drift
#: apart -- which is the whole failure mode ENG-3685 is about.
#:
#: It is the test backend because that is the one CI's non-``main`` runs (PRs,
#: pushes to ``test``, the nightly) use. It used to be ``dev-platform-api``, so a
#: developer with no ``BACKEND_URL`` validated the suite against a different
#: environment than the one whose result gates a merge, and each side read as
#: "it passes for me" (ENG-3683). An unset ``BACKEND_URL`` therefore selects the
#: ``test`` id space.
DEFAULT_BACKEND_URL = "https://test-platform-api.aixplain.com"

#: ``BACKEND_URL`` hostname -> environment key. Matched exactly against the
#: parsed, lower-cased hostname: ``platform-api.aixplain.com`` is a suffix of
#: both of the others, and a substring test would also read a host such as
#: ``staging-platform-api`` -- or a query string that merely mentions one of
#: these -- as a backend it is not.
_HOSTS: Dict[str, str] = {
    "dev-platform-api.aixplain.com": "dev",
    "test-platform-api.aixplain.com": "test",
    "platform-api.aixplain.com": "prod",
}


@dataclass(frozen=True)
class AssetIds:
    """The platform assets the v2 functional suite needs, one field per asset.

    Fields are upper-case because the name is part of the contract twice over:
    tests read ``assets.DEFAULT_LLM`` and a run overrides it with
    ``AIXPLAIN_TEST_DEFAULT_LLM``. Every field needs an entry in :data:`SPECS`,
    which says how to resolve it and what to call it when it is gone;
    ``tests/unit/test_functional_hygiene.py`` asserts the two stay in step.
    """

    #: Text-generation LLM the suite defaults to. Currently the same id as
    #: ``aixplain.v2.agent.Agent.DEFAULT_LLM``, which is an SDK constant rather
    #: than a test fixture -- the tests that assert against the SDK default read
    #: it from ``client.Agent.DEFAULT_LLM``, not from here.
    DEFAULT_LLM: str

    #: A stable non-default LLM, for tests that must prove a configured LLM
    #: survives a round-trip. Must differ from ``client.Agent.DEFAULT_LLM``.
    NON_DEFAULT_LLM: str

    #: A second-vendor LLM, paired with ``DEFAULT_LLM`` (GPT-5.4) for cross-vendor
    #: behaviour (Arabic rendering, tool-calling style) rather than for any
    #: capability of its own.
    CLAUDE_LLM: str

    #: Emits tool-call deltas over a streaming connection.
    STREAMING_TOOL_CALL_MODEL: str

    #: A vision-capable LLM (Gemini) that accepts image attachments on an agent
    #: run, so an attachment's content can be proved to reach the model.
    VISION_LLM: str

    #: One model that only advertises ``synchronous`` and one that only
    #: advertises ``asynchronous``, for the connection-type routing tests.
    SYNC_ONLY_MODEL: str
    ASYNC_ONLY_MODEL: str

    #: A translation model carrying a ``sourcelanguage`` input, so a per-tool
    #: parameter override can be proved to survive save -> fetch -> run.
    TRANSLATION_MODEL: str

    #: Image model whose sync run returns a final output URL that must not be
    #: polled.
    SEEDREAM_MODEL: str

    #: Orchestrator and worker for the Recursive Language Model tests.
    RLM_MODEL: str

    #: Integration with a rich action catalogue, used to exercise
    #: Actions/Inputs, ``list_actions`` and the snake_case field mapping.
    SLACK_INTEGRATION: str

    #: Connector tools an agent can be handed to reach the live web.
    FIRECRAWL: str
    TAVILY: str


@dataclass(frozen=True)
class AssetSpec:
    """How to resolve one asset, and what to call it when resolution fails."""

    #: Attribute on the ``Aixplain`` client whose ``get()`` resolves this id.
    resource: str

    #: Human name, so a missing asset reads as "FIRECRAWL (Firecrawl connector
    #: tool) -- resolved with client.Tool.get" rather than as a bare 404.
    description: str


#: Resolution metadata, keyed by :class:`AssetIds` field name.
#:
#: ``resource`` is not inferable from the asset, so each entry records the call
#: the tests actually make.
SPECS: Dict[str, AssetSpec] = {
    "DEFAULT_LLM": AssetSpec("Model", "default text-generation LLM (GPT-5.4)"),
    "NON_DEFAULT_LLM": AssetSpec("Model", "non-default LLM (GPT-4.1 Nano)"),
    "CLAUDE_LLM": AssetSpec("Model", "Anthropic Claude Opus 4.6"),
    "STREAMING_TOOL_CALL_MODEL": AssetSpec("Model", "streaming tool-calling model"),
    "VISION_LLM": AssetSpec("Model", "vision-capable LLM for image attachments (Gemini)"),
    "SYNC_ONLY_MODEL": AssetSpec("Model", "sync-only model (Cloud Translation)"),
    "ASYNC_ONLY_MODEL": AssetSpec("Model", "async-only model (Amazon Translate)"),
    "TRANSLATION_MODEL": AssetSpec("Model", "translation model with a source-language input"),
    "SEEDREAM_MODEL": AssetSpec("Model", "Seedream image model"),
    "RLM_MODEL": AssetSpec("Model", "RLM orchestrator/worker (Gemini 2.5 Pro)"),
    "SLACK_INTEGRATION": AssetSpec("Integration", "Slack integration"),
    "FIRECRAWL": AssetSpec("Tool", "Firecrawl connector tool"),
    "TAVILY": AssetSpec("Tool", "Tavily Web Search connector tool"),
}


#: The ids the v2 suite has been running with. Captured from the literals the
#: tests carried before ENG-3685, which is `dev` by construction: that was the
#: suite's default backend until ENG-3683 moved `DEFAULT_BACKEND_URL` to `test`,
#: so it is the id space every local run and every id added by hand was
#: validated against.
DEV = AssetIds(
    DEFAULT_LLM="69b7e5f1b2fe44704ab0e7d0",
    NON_DEFAULT_LLM="67fd9e2bef0365783d06e2f0",
    CLAUDE_LLM="698c87701239a117fd66b468",
    STREAMING_TOOL_CALL_MODEL="69727676c60248082d79932f",
    VISION_LLM="6a2846019a0a2598b61e12b8",
    SYNC_ONLY_MODEL="66aa869f6eb56342c26057e1",
    ASYNC_ONLY_MODEL="6686e7946eb563a724229b84",
    TRANSLATION_MODEL="678025ac6eb563a2566829b1",
    SEEDREAM_MODEL="69f347e7de823633d9604dfd",
    RLM_MODEL="68d43005ce180d2fdb4deac7",
    SLACK_INTEGRATION="686432941223092cb4294d3f",
    FIRECRAWL="69442021f2e6cb73e286ff0f",
    # Fetched by id rather than by the marketplace path
    # tavily/tavily-search-api/Tavily, which collides with the Legacy Tavily
    # asset whose single generic `run` action breaks the tool tests.
    TAVILY="6931bdf462eb386b7158def3",
)

#: `test` and `prod` are separate id spaces from `dev`, but the v2 leg has been
#: running these same literals against all three, so they are recorded as shared
#: rather than guessed at per environment. That is a claim :class:`LazyAssets`
#: checks on every run: an id that does not exist on a backend fails the tests
#: that read it, by name, and the fix is one line here --
#: ``TEST = replace(DEV, SEEDREAM_MODEL="<the test-backend id>")``.
#:
#: `TEST` is also what a run with no ``BACKEND_URL`` selects (see
#: :data:`DEFAULT_BACKEND_URL`). Moving the default from `dev` to `test` changed
#: no id, since `TEST` is `DEV` until an entry here says otherwise.
TEST = replace(DEV)
PROD = replace(DEV)

ASSETS_BY_ENVIRONMENT: Dict[str, AssetIds] = {"dev": DEV, "test": TEST, "prod": PROD}

#: Every asset name, in declaration order.
ASSET_NAMES: Tuple[str, ...] = tuple(field.name for field in fields(AssetIds))


class UnknownBackendError(RuntimeError):
    """Raised when ``BACKEND_URL`` names a host with no known id space."""


class ConflictingEnvironmentError(RuntimeError):
    """Raised when :data:`ENVIRONMENT_ENV` names a different id space from a recognised ``BACKEND_URL``."""


def _setting(environ: Mapping[str, str], key: str) -> Optional[str]:
    """Return *key* from *environ* with surrounding whitespace removed, or None when blank."""
    value = (environ.get(key) or "").strip()
    return value or None


def environment_for(backend_url: Optional[str] = None, environ: Optional[Mapping[str, str]] = None) -> str:
    """Return the id space to use: ``"dev"``, ``"test"`` or ``"prod"``.

    Args:
        backend_url: The backend, defaulting to ``BACKEND_URL`` and then to
            :data:`DEFAULT_BACKEND_URL`.
        environ: Environment to read, defaulting to ``os.environ``.

    Returns:
        The key into :data:`ASSETS_BY_ENVIRONMENT`.

    Raises:
        UnknownBackendError: If the host is unrecognised and
            :data:`ENVIRONMENT_ENV` does not say which id space it mirrors, or
            names one that does not exist. Failing here is the point: silently
            falling back to `dev` against an unknown backend is how a leg goes
            green while resolving nothing.
        ConflictingEnvironmentError: If the host is recognised and
            :data:`ENVIRONMENT_ENV` names a different id space. Either choice
            would validate one backend's ids against another backend.
    """
    environ = os.environ if environ is None else environ

    pinned = _setting(environ, ENVIRONMENT_ENV)
    if pinned is not None and pinned not in ASSETS_BY_ENVIRONMENT:
        raise UnknownBackendError(f"{ENVIRONMENT_ENV}={pinned!r} is not one of {sorted(ASSETS_BY_ENVIRONMENT)}.")

    backend_url = backend_url or environ.get("BACKEND_URL") or DEFAULT_BACKEND_URL
    recognised = _HOSTS.get((urlparse(backend_url).hostname or "").lower())

    if recognised is not None:
        if pinned is not None and pinned != recognised:
            raise ConflictingEnvironmentError(
                f"{ENVIRONMENT_ENV}={pinned!r} contradicts BACKEND_URL={backend_url!r}, which is the "
                f"{recognised!r} backend. {ENVIRONMENT_ENV} only pins the id space of a host this suite does "
                f"not recognise; unset it, or override individual ids with {ENV_PREFIX}<NAME>."
            )
        return recognised
    if pinned is not None:
        return pinned

    raise UnknownBackendError(
        f"BACKEND_URL={backend_url!r} is not one of the backends this suite has asset ids for "
        f"({', '.join(_HOSTS)}). Set {ENVIRONMENT_ENV} to the id space it mirrors "
        f"({', '.join(sorted(ASSETS_BY_ENVIRONMENT))}), or override the ids individually with "
        f"{ENV_PREFIX}<NAME>."
    )


def overrides_from(environ: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Return the ``AIXPLAIN_TEST_<NAME>`` overrides present in *environ*.

    Args:
        environ: Environment to read, defaulting to ``os.environ``.

    Returns:
        Asset name -> id, for the names actually overridden, with surrounding
        whitespace removed. An empty or whitespace-only value is ignored rather
        than treated as an override, so an unset CI variable that expands to
        ``""`` does not blank out an id.
    """
    environ = os.environ if environ is None else environ
    overrides = {name: _setting(environ, ENV_PREFIX + name) for name in ASSET_NAMES}
    return {name: value for name, value in overrides.items() if value is not None}


def assets_for(backend_url: Optional[str] = None, environ: Optional[Mapping[str, str]] = None) -> AssetIds:
    """Return the asset ids for a backend, with environment overrides applied.

    Args:
        backend_url: The backend, defaulting to ``BACKEND_URL`` and then to
            :data:`DEFAULT_BACKEND_URL`.
        environ: Environment to read, defaulting to ``os.environ``.

    Returns:
        The :class:`AssetIds` for that backend.
    """
    base = ASSETS_BY_ENVIRONMENT[environment_for(backend_url, environ)]
    return replace(base, **overrides_from(environ))


class LazyAssets:
    """Asset ids that are resolved against the backend the first time a test reads them.

    ``assets.DEFAULT_LLM`` returns the id string, exactly as the plain
    :class:`AssetIds` would, after one ``client.<resource>.get(id)`` per name
    per session (see :data:`SPECS`). A name that does not resolve fails the
    reading test with ``pytest.fail``, naming the asset, the id, the backend,
    the call and the ``AIXPLAIN_TEST_<NAME>`` override.

    Resolving per name rather than all up front keeps one retired asset from
    erroring every leg: only the tests that read it fail, and a leg that reads
    no asset never touches the backend. A success is cached, and so is a
    failure that asking again cannot fix (see :func:`_is_permanent`), so a
    ``@flaky`` rerun reports a retired id again without repeating the request.
    Any other failure -- a 5xx, a 429, a timeout, a dropped connection -- is not
    cached: the next read asks again, so one blip fails one test rather than
    every later test in the worker. The cache lives on this object, and the
    session fixture that builds it succeeds even when a name later fails, so
    pytest-rerunfailures (which only discards the cached results of fixtures
    that errored) keeps it across reruns.
    """

    def __init__(
        self,
        ids: AssetIds,
        client_factory: Callable[[], Any],
        backend_url: str,
        environment: str,
    ) -> None:
        """Wrap *ids*; *client_factory* is called once, on the first resolution."""
        self._ids = ids
        self._client_factory = client_factory
        self._client: Any = None
        self._backend_url = backend_url
        self._environment = environment
        #: Asset name -> None once resolved, or the permanent failure message to repeat.
        self._outcomes: Dict[str, Optional[str]] = {}

    def __getattr__(self, name: str) -> str:
        """Return the id for asset *name*, resolving it on first access."""
        if name.startswith("_") or name not in SPECS:
            raise AttributeError(f"{type(self).__name__} has no asset named {name!r}; see tests/functional/_assets.py")
        return self.resolve(name)

    def resolve(self, name: str) -> str:
        """Return the id for asset *name*, or fail the current test if it does not resolve."""
        if name in self._outcomes:
            failure = self._outcomes[name]
        else:
            failure, permanent = self._attempt(name)
            if failure is None or permanent:
                self._outcomes[name] = failure
        if failure is not None:
            pytest.fail(failure, pytrace=False)
        return getattr(self._ids, name)

    def _attempt(self, name: str) -> Tuple[Optional[str], bool]:
        """Resolve *name* once; return ``(None, True)`` on success, else the message and whether it is permanent."""
        spec = SPECS[name]
        asset_id = getattr(self._ids, name)
        try:
            if self._client is None:
                try:
                    self._client = self._client_factory()
                except Exception as error:  # noqa: BLE001 - a client that cannot be built will not build next time
                    return self._failure(name, error), True
            getattr(self._client, spec.resource).get(asset_id)
        except Exception as error:  # noqa: BLE001 - any failure to resolve is the failure being reported
            return self._failure(name, error), _is_permanent(error)
        return None, True

    def _failure(self, name: str, error: BaseException) -> str:
        """The message a test that reads *name* fails with."""
        spec = SPECS[name]
        return (
            f"functional-test asset {name} ({spec.description}) = {getattr(self._ids, name)} did not resolve on "
            f"{self._backend_url} (id space {self._environment!r}) via client.{spec.resource}.get: "
            f"{error}\n\nFix the id in tests/functional/_assets.py, or point it elsewhere for this run "
            f"with {ENV_PREFIX}{name}=<id>."
        )


#: 4xx statuses that are about load or timing rather than the request, so asking again can succeed.
_TRANSIENT_CLIENT_STATUSES = frozenset({408, 409, 425, 429})


def _is_permanent(error: BaseException) -> bool:
    """Whether a failed ``client.<resource>.get`` would fail the same way if asked again.

    Only a definite answer is cached: an API error with a 4xx status other than
    the load and timing ones (a 404 for a retired id, a 403 for an asset the key
    cannot see), or a response that came back but could not be deserialized. A
    5xx, a 429, a timeout or a dropped connection is not, and neither is any
    error this cannot classify -- retrying an unknown error costs one request,
    while caching a transient one fails every later test in the worker.
    """
    from aixplain.v2.exceptions import APIError, ResourceError

    if isinstance(error, APIError):
        if error.retryable is not None:
            return not error.retryable
        return 400 <= error.status_code < 500 and error.status_code not in _TRANSIENT_CLIENT_STATUSES
    return isinstance(error, ResourceError)
