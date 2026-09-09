"""Tests for attaching built-in toolkits to a v2 Agent (ENG-3699).

Covers the three things that make ``BuiltinTool`` more than a typed dict: the row
reaches the wire untouched, a persisted row comes back as a ``BuiltinTool``, and
the agent's save machinery never mistakes one for an unsaved asset.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import Aixplain
from aixplain.v2 import BuiltinTool

FILE_ROW = {
    "type": "builtin",
    "toolkit": "file",
    "include": ["read_file", "glob", "grep"],
    "max_read_bytes": 262144,
    "max_results": 500,
}
PYTHON_ROW = {"type": "builtin", "toolkit": "python", "include": ["run_python"], "timeout_s": 10, "expose_files": False}
BASH_ROW = {
    "type": "builtin",
    "toolkit": "bash",
    "include": ["run_command"],
    "timeout_s": 60,
    "max_output_bytes": 65536,
    "deny_patterns": [r"^\s*rm\s+-rf\s+/"],
}


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


# ---------------------------------------------------------------------------
# Save payload
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", [FILE_ROW, PYTHON_ROW, BASH_ROW], ids=["file", "python", "bash"])
def test_a_builtin_tool_reaches_the_payload_untouched(aix, row):
    """`_normalize_tool_dict_for_api` must not rewrite the worker's snake_case keys.

    Its key map covers `asset_id` / `allow_multi` / `supports_variables` only, so
    every builtin setting passes through verbatim today. Pinned here because a
    future entry added to that map would silently camelCase a setting and the
    worker would fall back to its default without complaining.
    """
    settings = {key: value for key, value in row.items() if key != "type"}
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(**settings)])

    assert agent.build_save_payload()["tools"] == [row]


def test_a_builtin_row_carries_no_asset_identity(aix):
    """A builtin toolkit is not an onboarded asset; an id would make the backend look one up."""
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="file")])

    (serialized,) = agent.build_save_payload()["tools"]

    assert not {"id", "assetId", "asset_id", "workspace_root"} & set(serialized)


def test_builtin_and_asset_tools_coexist(aix):
    """Attaching a toolkit must not disturb how the other entries normalize."""
    snapshot = {"id": "some-tool-id", "type": "model", "name": "Translate"}
    agent = aix.Agent(
        name="mixed-agent",
        tools=[
            BuiltinTool(toolkit="python", timeout_s=30),
            "some-tool-id",
            {"id": "other-tool-id", "type": "model", "asset_id": "other-tool-id"},
        ],
    )

    with patch.object(type(agent), "_resolve_tool_snapshot", return_value=snapshot):
        tools = agent.build_save_payload()["tools"]

    assert tools[0] == {"type": "builtin", "toolkit": "python", "timeout_s": 30}
    assert tools[1]["id"] == "some-tool-id"
    assert tools[1]["type"] == "model"
    assert tools[2]["assetId"] == "other-tool-id"
    assert tools[2]["type"] == "model"


def test_several_toolkits_can_be_attached_at_once(aix):
    """The headline use case: a filesystem plus an interpreter."""
    agent = aix.Agent(
        name="workspace-agent",
        tools=[BuiltinTool(toolkit="file", include=["read_file"]), BuiltinTool(toolkit="python", timeout_s=30)],
    )

    assert [tool["toolkit"] for tool in agent.build_save_payload()["tools"]] == ["file", "python"]


# ---------------------------------------------------------------------------
# Hydration and round-trip
# ---------------------------------------------------------------------------


def test_from_dict_hydrates_a_builtin_row_without_a_client_context():
    """Builtin rows reference no asset, so hydration must not wait for a context.

    ``_hydrate_tools`` returns early when there is no context — correct for asset
    tools, which need the backend to resolve. A toolkit is pure configuration, so
    it converts on an unbound Agent too.
    """
    from aixplain.v2.agent import Agent

    agent = Agent.from_dict({"id": "agent-id", "name": "workspace-agent", "tools": [FILE_ROW]})

    (tool,) = agent.tools
    assert isinstance(tool, BuiltinTool)
    assert tool.toolkit == "file"
    assert tool.max_read_bytes == 262144


def test_get_returns_builtin_tools_and_re_saves_them_unchanged(aix):
    """`agent.tools` after `get()` is symmetric with what the user passed in."""
    aix.client.get = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [FILE_ROW, PYTHON_ROW]})

    agent = aix.Agent.get("agent-id")

    assert [type(tool) for tool in agent.tools] == [BuiltinTool, BuiltinTool]
    assert agent.build_save_payload()["tools"] == [FILE_ROW, PYTHON_ROW]


def test_a_fetched_toolkit_can_be_reconfigured_by_attribute(aix):
    """The reason for hydrating at all: edit a setting instead of rebuilding a dict."""
    aix.client.get = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [PYTHON_ROW]})
    agent = aix.Agent.get("agent-id")

    agent.tools[0].timeout_s = 60

    assert agent.build_save_payload()["tools"] == [{**PYTHON_ROW, "timeout_s": 60}]


def test_a_malformed_builtin_row_degrades_to_a_dict_and_still_serializes():
    """Hydration is best-effort: an unmappable row must not break construction."""
    from aixplain.v2.agent import Agent

    row = {"type": "builtin", "toolkit": "quantum"}
    agent = Agent.from_dict({"id": "agent-id", "name": "workspace-agent", "tools": [row]})

    assert agent.tools == [row]
    assert agent.build_save_payload()["tools"] == [row]


def test_save_leaves_the_caller_s_builtin_tool_object_in_place(aix):
    """The create response rebuilds `tools` as dicts; the restore path must re-type them."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [PYTHON_ROW]})
    tool = BuiltinTool(toolkit="python", timeout_s=10)
    agent = aix.Agent(name="workspace-agent", tools=[tool])

    agent.save()

    assert agent.tools == [tool]


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------


def test_editing_a_toolkit_setting_marks_the_agent_modified(aix):
    """A builtin row has no id, so an id/type signature would miss every edit."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [PYTHON_ROW]})
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="python", timeout_s=10)])
    agent.save()
    assert not agent.is_modified

    agent.tools[0].timeout_s = 60

    assert agent.is_modified


def test_swapping_one_toolkit_for_another_marks_the_agent_modified(aix):
    """`file` and `python` both reduce to `{id: None, type: None}` without the branch."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [FILE_ROW]})
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="file")])
    agent.save()
    assert not agent.is_modified

    agent.tools[0] = BuiltinTool(toolkit="python")

    assert agent.is_modified


# ---------------------------------------------------------------------------
# The save machinery must not treat a toolkit as an unsaved asset
# ---------------------------------------------------------------------------


def test_a_builtin_only_agent_passes_dependency_validation(aix):
    """`_validate_dependencies` flags any tool with a falsy `id`; a toolkit has none."""
    tool = BuiltinTool(toolkit="file")
    agent = aix.Agent(name="workspace-agent", tools=[tool])

    agent._validate_dependencies()

    assert agent.tools == [tool]


def test_save_subcomponents_does_not_try_to_save_a_toolkit(aix):
    """`_save_subcomponents` calls `save()` on tools that expose one; a toolkit does not."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [FILE_ROW]})
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="file")])

    agent.save(save_subcomponents=True)

    assert aix.client.request.call_args.kwargs["json"]["tools"] == [{"type": "builtin", "toolkit": "file"}]
