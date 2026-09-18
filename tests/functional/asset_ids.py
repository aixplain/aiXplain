"""Pinned backend asset ids for the functional suite, and the failure helpers
that keep a missing one from turning into a skip (ENG-3684).

Why this module exists
----------------------
A functional test that *discovers* the asset it needs -- "search the tools, take
the first one with actions" -- has two outcomes when the backend does not supply
one: it can skip, or it can fail. Skipping is the tempting choice, because the
test cannot check anything without the asset. It is also the wrong one: the leg
then reports green for a suite that verified nothing, which is the whole
ENG-3544/ENG-3684 defect at the level of a single test. `tests/functional/v2`
carried 37 such skips; one of them, in a module-scoped fixture, took ~40 tests
out on its own.

So the rule here is: the test environment must carry the fixtures the tests need.
An id that is absent is a test-infra failure, and these helpers state it as one,
with the id in the message so whoever reads the CI log knows exactly what to
onboard.

Ids are pinned rather than searched so a test exercises the same asset on every
run; each is overridable by environment variable so a tenant that onboarded a
different asset can point the suite at it without a code change.
"""

import os
from typing import NoReturn

import pytest


def _pinned(env_var: str, default: str) -> str:
    """The id to use for a fixture: the environment's override, or the default."""
    value = os.getenv(env_var)
    return value.strip() if value and value.strip() else default


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

#: GPT-5.4. The general-purpose text-generation model the v2 tests run against.
TEXT_MODEL_ID = _pinned("AIXPLAIN_TEST_TEXT_MODEL_ID", "69b7e5f1b2fe44704ab0e7d0")

#: A text-generation model that streams *and* emits OpenAI-style tool-call
#: deltas. Pinned rather than discovered: "find a model that supports streaming"
#: silently degrades into "skip" the moment the catalogue shifts, which is how
#: test_model.py's streaming coverage went dark.
STREAMING_TOOL_CALL_MODEL_ID = _pinned("AIXPLAIN_TEST_STREAMING_MODEL_ID", "69727676c60248082d79932f")

#: Cloud Translation -- synchronous-only, used to assert connection_type metadata.
SYNC_MODEL_ID = _pinned("AIXPLAIN_TEST_SYNC_MODEL_ID", "66aa869f6eb56342c26057e1")

#: Amazon Translate -- asynchronous-only, the other half of that pair.
ASYNC_MODEL_ID = _pinned("AIXPLAIN_TEST_ASYNC_MODEL_ID", "6686e7946eb563a724229b84")

# ---------------------------------------------------------------------------
# Integrations and tools
# ---------------------------------------------------------------------------

#: The Slack integration. Its actions/inputs are the fixture behind the
#: Actions -> Action -> Inputs -> Input hierarchy tests.
SLACK_INTEGRATION_ID = _pinned("AIXPLAIN_TEST_SLACK_INTEGRATION_ID", "686432941223092cb4294d3f")

#: "Tavily Web Search" connector tool (single action: search). Fetched by id: the
#: marketplace path tavily/tavily-search-api/Tavily collides with the Legacy
#: Tavily asset (6736411c...), whose single generic 'run' action breaks these tests.
TAVILY_TOOL_ID = _pinned("AIXPLAIN_TEST_TAVILY_TOOL_ID", "6931bdf462eb386b7158def3")

#: A *connected* tool exposing two or more actions. Unlike the ids above this one
#: is tenant-specific -- a connection belongs to the account that made it -- so it
#: has no portable default and is resolved from `SLACK_INTEGRATION_ID` when the
#: override is unset. Set the override to skip the lookup and pin an exact tool.
MULTI_ACTION_TOOL_ID = _pinned("AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID", "")

# ---------------------------------------------------------------------------
# Guardrail models
# ---------------------------------------------------------------------------

#: Canonical marketplace paths for the onboarded AWS guards. A guard that is not
#: onboarded is an environment that cannot run the inspector suite, not a reason
#: to pass the leg.
PROMPT_ATTACK_GUARD_PATH = "aws/detect-prompt-attacks-guardrail/aws"
SENSITIVE_INFO_GUARD_PATH = "aws/sensitive-information-guardrail/aws"
CONTEXTUAL_GROUNDING_GUARD_PATH = "aws/contextual-grounding-check-guardrail/aws"


# ---------------------------------------------------------------------------
# Failure helpers
# ---------------------------------------------------------------------------


def missing_fixture(what: str, detail: str = "", env_var: str = "") -> NoReturn:
    """Fail the test because the backend does not carry a fixture it needs.

    `pytest.fail`, never `pytest.skip`: a fixture the test environment was
    supposed to provide and does not is a defect in the environment, and a leg
    that quietly skips past it reports success for code nobody ran.

    Args:
        what: The fixture that is missing, named the way a reader would search
            for it (an id, a path, a description).
        detail: Anything else that helps -- the exception text, what was searched.
        env_var: The override that lets this environment point at its own asset.
    """
    message = f"Test fixture missing from this environment: {what}."
    if detail:
        message += f" {detail}"
    if env_var:
        message += f" Onboard it, or point the suite at an equivalent asset with {env_var}."
    else:
        message += " Onboard it in the test tenant; this is a test-infra failure, not a skip."
    pytest.fail(message)


def require_env(name: str, purpose: str) -> str:
    """Return environment variable *name*, failing the test when it is unset.

    The variables this guards are supplied by the workflow (see the `Set
    environment variables` step in .github/workflows/main.yaml). An unset one
    means the job lost a secret, which must be visible rather than skipped past.
    """
    value = os.getenv(name)
    if not value or not value.strip():
        pytest.fail(
            f"{name} is not set, so {purpose} cannot run. It is supplied by the workflow's "
            "`Set environment variables` step; if it is missing there, add it (repository "
            "secret) rather than letting the leg skip these tests."
        )
    return value.strip()


def resolve_multi_action_tool(client):
    """Return a connected tool exposing two or more actions.

    Prefers the pinned `MULTI_ACTION_TOOL_ID`. Without one, looks for a tool
    backed by the pinned Slack integration -- a connection id is tenant-specific,
    so there is no portable default to pin. Either way, *not finding one fails*:
    the multi-action tests cannot run without such a tool, and the tenant is
    expected to carry a Slack connection.
    """
    if MULTI_ACTION_TOOL_ID:
        return client.Tool.get(MULTI_ACTION_TOOL_ID)

    candidates = client.Tool.search(page_size=20).results
    for tool in candidates:
        if tool.actions_available and tool.integration_id == SLACK_INTEGRATION_ID:
            return tool

    missing_fixture(
        f"a connected tool backed by integration {SLACK_INTEGRATION_ID}",
        f"Searched the first {len(candidates)} tool(s) and found none with actions available.",
        env_var="AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID",
    )
