"""Failure helpers that keep a missing functional-test fixture from turning into a skip (ENG-3684).

Why this module exists
----------------------
A functional test that *discovers* the asset it needs -- "search the tools, take
the first one with actions" -- has two outcomes when the backend does not supply
one: it can skip, or it can fail. Skipping is the tempting choice, because the
test cannot check anything without the asset. It is also the wrong one: the leg
then reports green for a suite that verified nothing, which is the whole
ENG-3544/ENG-3684 defect at the level of a single test. `tests/functional/v2`
carried dozens of such skips, and one of them, in a module-scoped fixture, took
a whole file's tool tests out on its own (ENG-3684).

So the rule here is: the test environment must carry the fixtures the tests need.
An absent one is a test-infra failure, and these helpers state it as one, with
the id in the message so whoever reads the CI log knows exactly what to onboard.

Asset ids do not live here. Every portable id is a named field in
`tests/functional/_assets.py` (ENG-3685), read through the `assets` fixture and
overridable per run with ``AIXPLAIN_TEST_<NAME>``. The one id this module reads
itself is the multi-action tool's: a connection belongs to the account that made
it, so there is no portable default to register, only the
``AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID`` override.
"""

import os
from typing import NoReturn

import pytest


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


#: How far `resolve_multi_action_tool` searches before giving up: at most
#: `_SEARCH_PAGES` pages of `_SEARCH_PAGE_SIZE` tools. Bounded, so a tenant with a
#: large catalogue costs a handful of requests rather than a full walk.
_SEARCH_PAGES = 5
_SEARCH_PAGE_SIZE = 20

#: A *connected* tool exposing two or more actions. Unlike the ids in
#: `tests/functional/_assets.py` this one is tenant-specific, so it has no
#: default: unset, `resolve_multi_action_tool` searches for a tool backed by the
#: Slack integration instead. Set it to skip the lookup and pin an exact tool.
_MULTI_ACTION_TOOL_ENV = "AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID"


def _action_count(tool) -> int:
    """How many actions *tool* lists, or 0 when listing them fails."""
    try:
        return len(tool.list_actions() or [])
    except Exception:
        return 0


def resolve_multi_action_tool(client, slack_integration_id: str):
    """Return a connected tool exposing two or more actions.

    Prefers the tool pinned by ``AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID``. Without
    one, searches up to `_SEARCH_PAGES` pages of tools for one backed by
    *slack_integration_id* -- a connection id is tenant-specific, so there is no
    portable default to pin. Either way the tool must list at least two actions,
    and *not finding one fails*: the multi-action tests cannot run without such a
    tool, and the tenant is expected to carry a Slack connection.

    Args:
        client: The ``Aixplain`` client for this run.
        slack_integration_id: The Slack integration the searched-for tool must be
            backed by. Callers pass ``assets.SLACK_INTEGRATION``, so the id comes
            from the shared registry like every other one.
    """
    pinned = (os.getenv(_MULTI_ACTION_TOOL_ENV) or "").strip()
    if pinned:
        tool = client.Tool.get(pinned)
        count = _action_count(tool)
        if count < 2:
            missing_fixture(
                f"a connected tool with two or more actions at {pinned}",
                f"The pinned tool lists {count} action(s).",
                env_var=_MULTI_ACTION_TOOL_ENV,
            )
        return tool

    searched = 0
    slack_backed = []
    for page_number in range(_SEARCH_PAGES):
        page = client.Tool.search(page_number=page_number, page_size=_SEARCH_PAGE_SIZE)
        searched += len(page.results)
        for tool in page.results:
            # Both fields come with the search result, so only a tool that passes
            # them costs a LIST_ACTIONS request.
            if not (tool.actions_available and tool.integration_id == slack_integration_id):
                continue
            slack_backed.append(tool.id)
            if _action_count(tool) >= 2:
                return tool
        if not page.results or page_number + 1 >= page.page_total:
            break

    missing_fixture(
        f"a connected tool backed by the Slack integration {slack_integration_id} with two or more actions",
        f"Searched {searched} tool(s) in up to {_SEARCH_PAGES} page(s) of {_SEARCH_PAGE_SIZE}, filtering on "
        f"integration_id == {slack_integration_id}; Slack-backed tools with actions available: "
        f"{slack_backed or 'none'}, none listing two or more. Connect Slack in this tenant.",
        env_var=_MULTI_ACTION_TOOL_ENV,
    )
