"""Named backend asset ids for the functional suite (ENG-3685).

Every functional test that needed a platform asset carried the raw ObjectId
inline: 24 hex characters, no name, no owner, no way to point a run at a
different backend. The same default LLM appeared in four v2 files and the Slack
integration in seven, and three of the ids were copy-pasted byte-for-byte
between the agent and tool suites.

Those literals are not portable. CI validates them against
``test-platform-api``, a push to ``main`` validates them against production, and
a laptop with no ``BACKEND_URL`` set validates them against
``dev-platform-api`` (see ``DEFAULT_BACKEND_URL`` below). Those are three
separate id spaces, so a retired asset failed one leg at a time and each failure
read as an unrelated backend error from somewhere deep inside a test body.

This module is the single source. Ask for an asset by name::

    def test_something(client, assets):
        model = client.Model.get(assets.DEFAULT_LLM)

``assets`` is the session fixture in ``tests/functional/v2/conftest.py``. It
picks the id set for the backend this run points at and resolves every id once
before any test runs, so a retired asset fails the leg immediately and by name
rather than in whichever test happened to reach it first.

Retiring an id is a one-line change here. Overriding one for a single run is an
environment variable -- ``AIXPLAIN_TEST_<NAME>``, e.g.
``AIXPLAIN_TEST_DEFAULT_LLM=<id>`` -- which is also how a backend this module
does not know about (a branch deployment, a tunnel, a local stack) gets a
working id without a commit.

``tests/unit/test_functional_hygiene.py`` fails if a bare 24-hex literal
reappears anywhere under ``tests/functional/``, which is what keeps this module
the only source rather than merely the first one.

Scope: the v2 suite. The v1 functional legs still carry their own literals and
are deliberately untouched -- PROD-2918 deletes every one of those files, so
editing them here would mean resolving a delete/modify conflict over code that
is on its way out. The guard test names them explicitly for the same reason.
"""

import os
from dataclasses import dataclass, fields, replace
from typing import Dict, Mapping, Optional, Tuple

#: Prefix for the per-asset override, e.g. ``AIXPLAIN_TEST_SLACK_INTEGRATION``.
#: The suffix is the field name on :class:`AssetIds` exactly as spelled there.
ENV_PREFIX = "AIXPLAIN_TEST_"

#: Pins the id space when ``BACKEND_URL`` names a host this module does not
#: recognise. Values are the keys of :data:`ASSETS_BY_ENVIRONMENT`.
ENVIRONMENT_ENV = "AIXPLAIN_TEST_ENV"

#: The backend a run with no ``BACKEND_URL`` talks to. ``tests/functional/v2/
#: conftest.py`` imports this rather than repeating the literal, so the id space
#: this module selects and the backend the client is built against cannot drift
#: apart -- which is the whole failure mode ENG-3685 is about.
DEFAULT_BACKEND_URL = "https://dev-platform-api.aixplain.com"

#: Substring of ``BACKEND_URL`` -> environment key. Ordered longest-first
#: because ``platform-api.aixplain.com`` is a substring of both of the others;
#: matching on the shorter one first would read every backend as production.
_HOST_MARKERS: Tuple[Tuple[str, str], ...] = (
    ("dev-platform-api.aixplain.com", "dev"),
    ("test-platform-api.aixplain.com", "test"),
    ("platform-api.aixplain.com", "prod"),
)


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

    #: Two LLMs from different vendors, for cross-vendor behaviour (Arabic
    #: rendering, tool-calling style) rather than for any capability of their own.
    GPT_4O_LLM: str
    CLAUDE_LLM: str

    #: Emits tool-call deltas over a streaming connection.
    STREAMING_TOOL_CALL_MODEL: str

    #: One model that only advertises ``synchronous`` and one that only
    #: advertises ``asynchronous``, for the connection-type routing tests.
    SYNC_ONLY_MODEL: str
    ASYNC_ONLY_MODEL: str

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
    GOOGLE_SEARCH_UTILITY: str


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
#: ``resource`` is not inferable from the asset: ``GOOGLE_SEARCH_UTILITY`` is a
#: utility *model* that the agent tests fetch through ``client.Tool.get``, and
#: fetching it through ``client.Model.get`` would verify something the suite
#: never does. Each entry records the call the tests actually make.
SPECS: Dict[str, AssetSpec] = {
    "DEFAULT_LLM": AssetSpec("Model", "default text-generation LLM (GPT-5.4)"),
    "NON_DEFAULT_LLM": AssetSpec("Model", "non-default LLM (GPT-4.1 Nano)"),
    "GPT_4O_LLM": AssetSpec("Model", "OpenAI GPT-4o"),
    "CLAUDE_LLM": AssetSpec("Model", "Anthropic Claude Opus 4.6"),
    "STREAMING_TOOL_CALL_MODEL": AssetSpec("Model", "streaming tool-calling model"),
    "SYNC_ONLY_MODEL": AssetSpec("Model", "sync-only model (Cloud Translation)"),
    "ASYNC_ONLY_MODEL": AssetSpec("Model", "async-only model (Amazon Translate)"),
    "SEEDREAM_MODEL": AssetSpec("Model", "Seedream image model"),
    "RLM_MODEL": AssetSpec("Model", "RLM orchestrator/worker (Gemini 2.5 Pro)"),
    "SLACK_INTEGRATION": AssetSpec("Integration", "Slack integration"),
    "FIRECRAWL": AssetSpec("Tool", "Firecrawl connector tool"),
    "TAVILY": AssetSpec("Tool", "Tavily Web Search connector tool"),
    "GOOGLE_SEARCH_UTILITY": AssetSpec("Tool", "Google Search utility model, fetched as a tool"),
}


#: The ids the v2 suite has been running with. Captured from the literals the
#: tests carried before ENG-3685, which is `dev` by construction: that is what
#: `DEFAULT_BACKEND_URL` points at, so it is the id space every local run and
#: every id added by hand was validated against.
DEV = AssetIds(
    DEFAULT_LLM="69b7e5f1b2fe44704ab0e7d0",
    NON_DEFAULT_LLM="67fd9e2bef0365783d06e2f0",
    # Onboarded 2024-05-16 per the ObjectId timestamp, four days after GPT-4o's
    # release and five weeks before Claude 3.5 Sonnet's -- so the "Claude 3.5
    # Sonnet v1" comment the v1 suite attached to this id was the stale half of
    # the pair, not the `gpt-4o` label the Arabic test uses. Corroborated by
    # skills/aixplain-builder/references/models.md, which gives this id as the
    # id form of `openai/gpt-4o`.
    GPT_4O_LLM="6646261c6eb563165658bbb1",
    CLAUDE_LLM="698c87701239a117fd66b468",
    STREAMING_TOOL_CALL_MODEL="69727676c60248082d79932f",
    SYNC_ONLY_MODEL="66aa869f6eb56342c26057e1",
    ASYNC_ONLY_MODEL="6686e7946eb563a724229b84",
    SEEDREAM_MODEL="69f347e7de823633d9604dfd",
    RLM_MODEL="68d43005ce180d2fdb4deac7",
    SLACK_INTEGRATION="686432941223092cb4294d3f",
    FIRECRAWL="69442021f2e6cb73e286ff0f",
    # Fetched by id rather than by the marketplace path
    # tavily/tavily-search-api/Tavily, which collides with the Legacy Tavily
    # asset whose single generic `run` action breaks the tool tests.
    TAVILY="6931bdf462eb386b7158def3",
    GOOGLE_SEARCH_UTILITY="65c51c556eb563350f6e1bb1",
)

#: `test` and `prod` are separate id spaces from `dev`, but the v2 leg has been
#: running these same literals against all three, so they are recorded as shared
#: rather than guessed at per environment. That is a claim the session fixture
#: checks on every run: the first id that does not exist on a backend fails that
#: leg by name, and the fix is one line here --
#: ``TEST = replace(DEV, SEEDREAM_MODEL="<the test-backend id>")``.
TEST = replace(DEV)
PROD = replace(DEV)

ASSETS_BY_ENVIRONMENT: Dict[str, AssetIds] = {"dev": DEV, "test": TEST, "prod": PROD}

#: Every asset name, in declaration order.
ASSET_NAMES: Tuple[str, ...] = tuple(field.name for field in fields(AssetIds))


class UnknownBackendError(RuntimeError):
    """Raised when ``BACKEND_URL`` names a host with no known id space."""


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
            :data:`ENVIRONMENT_ENV` does not say which id space it mirrors.
            Failing here is the point: silently falling back to `dev` against an
            unknown backend is how a leg goes green while resolving nothing.
    """
    environ = os.environ if environ is None else environ

    pinned = environ.get(ENVIRONMENT_ENV)
    if pinned:
        if pinned not in ASSETS_BY_ENVIRONMENT:
            raise UnknownBackendError(f"{ENVIRONMENT_ENV}={pinned!r} is not one of {sorted(ASSETS_BY_ENVIRONMENT)}.")
        return pinned

    backend_url = backend_url or environ.get("BACKEND_URL") or DEFAULT_BACKEND_URL
    for marker, environment in _HOST_MARKERS:
        if marker in backend_url:
            return environment

    raise UnknownBackendError(
        f"BACKEND_URL={backend_url!r} is not one of the backends this suite has asset ids for "
        f"({', '.join(marker for marker, _ in _HOST_MARKERS)}). Set {ENVIRONMENT_ENV} to the id "
        f"space it mirrors ({', '.join(sorted(ASSETS_BY_ENVIRONMENT))}), or override the ids "
        f"individually with {ENV_PREFIX}<NAME>."
    )


def overrides_from(environ: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Return the ``AIXPLAIN_TEST_<NAME>`` overrides present in *environ*.

    Args:
        environ: Environment to read, defaulting to ``os.environ``.

    Returns:
        Asset name -> id, for the names actually overridden. An empty value is
        ignored rather than treated as an override, so an unset CI variable that
        expands to ``""`` does not blank out an id.
    """
    environ = os.environ if environ is None else environ
    return {name: environ[ENV_PREFIX + name] for name in ASSET_NAMES if environ.get(ENV_PREFIX + name)}


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
