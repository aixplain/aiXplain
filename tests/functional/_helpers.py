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
from typing import Any, List, NoReturn, Optional, Tuple

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
#: `_SEARCH_PAGES` pages of `_SEARCH_PAGE_SIZE` tools, and at most
#: `_MAX_ACTION_PROBES` LIST_ACTIONS requests across them. Bounded, so a tenant with
#: a large catalogue costs a handful of requests rather than a full walk.
_SEARCH_PAGES = 5
_SEARCH_PAGE_SIZE = 20
_MAX_ACTION_PROBES = 25

#: A *connected* tool exposing two or more actions. Unlike the ids in
#: `tests/functional/_assets.py` this one is tenant-specific, so it has no
#: default: unset, `resolve_multi_action_tool` searches for one instead. Set it to
#: skip the lookup and pin an exact tool.
_MULTI_ACTION_TOOL_ENV = "AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID"


def _action_count(tool) -> int:
    """How many actions *tool* lists. A failed listing propagates."""
    return len(tool.list_actions() or [])


def _probed_action_count(tool) -> Optional[int]:
    """`_action_count` for a search candidate, or ``None`` when the backend refuses *this* tool.

    A candidate from ``Tool.search`` can be one the key may not list (403), whose
    connection is gone (404) or whose credentials expired (4xx): that rules out
    the tool, not the run. Anything else -- a 5xx, a timeout, an auth failure on
    every call -- is the listing endpoint itself being broken, and propagates
    instead of being reported as "connect Slack in this tenant".
    """
    from aixplain.v2.exceptions import APIError

    try:
        return _action_count(tool)
    except APIError as error:
        if 400 <= error.status_code < 500 and error.status_code not in (401, 408, 429):
            return None
        raise


def _searched_tools(client) -> List[Any]:
    """Every tool in the first `_SEARCH_PAGES` pages of ``Tool.search``."""
    tools: List[Any] = []
    for page_number in range(_SEARCH_PAGES):
        page = client.Tool.search(page_number=page_number, page_size=_SEARCH_PAGE_SIZE)
        tools.extend(page.results)
        if not page.results or page_number + 1 >= page.page_total:
            break
    return tools


def resolve_multi_action_tool(client, slack_integration_id: str):
    """Return a connected tool exposing two or more actions.

    Prefers the tool pinned by ``AIXPLAIN_TEST_MULTI_ACTION_TOOL_ID``. Without
    one, searches up to `_SEARCH_PAGES` pages of tools and probes them for actions:
    tools backed by *slack_integration_id* first, then tools backed by any other
    integration, then the rest, stopping after `_MAX_ACTION_PROBES` probes. A
    connection id is tenant-specific, so there is no portable default to pin, and
    the multi-action tests need *a* tool with two or more actions, not Slack in
    particular. Not finding one fails: the tests cannot run without such a tool.

    Candidates are probed with ``list_actions()`` rather than filtered on
    ``actions_available``: the backend leaves that field unset (``None``) on
    search results and on integrations alike -- the Slack integration reports
    ``actions_available=None`` yet lists its actions -- so filtering on it ruled
    out every tool (first live CI run: "Searched 100 tool(s) ... none"). Only an
    explicit ``False`` is skipped.

    Args:
        client: The ``Aixplain`` client for this run.
        slack_integration_id: The integration whose tools are tried first. Callers
            pass ``assets.SLACK_INTEGRATION``, so the id comes from the shared
            registry like every other one.
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

    tools = [tool for tool in _searched_tools(client) if tool.actions_available is not False]
    slack_backed = [tool for tool in tools if tool.integration_id == slack_integration_id]
    other_backed = [tool for tool in tools if tool.integration_id and tool.integration_id != slack_integration_id]
    unbacked = [tool for tool in tools if not tool.integration_id]

    probed = []
    for tool in (slack_backed + other_backed + unbacked)[:_MAX_ACTION_PROBES]:
        count = _probed_action_count(tool)
        if count is not None and count >= 2:
            return tool
        probed.append(f"{tool.id}={'refused' if count is None else count}")

    missing_fixture(
        "a connected tool with two or more actions",
        f"Searched {len(tools)} tool(s) in up to {_SEARCH_PAGES} page(s) of {_SEARCH_PAGE_SIZE} "
        f"({len(slack_backed)} backed by the Slack integration {slack_integration_id}, {len(other_backed)} by "
        f"another integration) and probed {len(probed)} for actions (id=count): {', '.join(probed) or 'none'}. "
        "Connect Slack, or any integration whose tool exposes two or more actions, in this tenant.",
        env_var=_MULTI_ACTION_TOOL_ENV,
    )


def resolve_action_source(client, integration_id: str) -> Tuple[Any, List[Any]]:
    """Return something that lists actions, and the actions it lists.

    Tries the integration *integration_id* first (callers pass
    ``assets.SLACK_INTEGRATION``). When it lists no actions, falls back to the
    tool from `resolve_multi_action_tool`, which carries the same
    ``list_actions()`` / ``list_inputs()`` surface. Either way the result has at
    least one action, and nothing suitable is a failure, not a skip.

    ``actions_available`` is deliberately not consulted: the backend returns it
    unset even for an integration that lists actions (see
    `resolve_multi_action_tool`).

    Only an *empty* listing falls back. An exception from the integration's
    ``list_actions()`` propagates: a broken listing endpoint is a failure to
    report, and falling back past it would let the tests pass on a tool while
    the integration path they are meant to cover is down.

    Args:
        client: The ``Aixplain`` client for this run.
        integration_id: The integration to try first.

    Returns:
        A ``(source, actions)`` pair, where *source* is an ``Integration`` or a
        ``Tool`` and *actions* is its non-empty ``list_actions()`` result.
    """
    integration = client.Integration.get(integration_id)
    actions = integration.list_actions()
    if actions:
        return integration, actions

    tool = resolve_multi_action_tool(client, integration_id)
    actions = tool.list_actions()
    if not actions:
        missing_fixture(
            f"an integration or connected tool that lists actions (tried integration {integration_id}, then tool "
            f"{tool.id})",
            "Both returned an empty list_actions().",
            env_var=_MULTI_ACTION_TOOL_ENV,
        )
    return tool, actions
