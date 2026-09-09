"""Tests for attaching built-in toolkits to a v2 Agent (ENG-3699).

Covers the three things that make ``BuiltinTool`` more than a typed dict: the row
reaches the wire untouched, a persisted row comes back as a ``BuiltinTool``, and
the agent's save machinery never mistakes one for an unsaved asset.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import Aixplain
from aixplain.v2 import BuiltinTool

#: The rows the worker accepts, verbatim from the ENG-3699 contract. Kept
#: byte-identical with the copy in the sibling built-in toolkit test module:
#: pytest runs with --import-mode=importlib and tests/unit/v2 is not a package,
#: so a shared module is not importable from here without restructuring.
FILE_ROW = {
    "type": "builtin",
    "toolkit": "file",
    "include": ["read_file", "list_directory", "glob", "grep", "write_file", "edit_file"],
    "max_read_bytes": 262144,
    "max_results": 500,
}
PYTHON_ROW = {
    "type": "builtin",
    "toolkit": "python",
    "include": ["run_python"],
    "timeout_s": 10,
    "expose_files": False,
}
BASH_ROW = {
    "type": "builtin",
    "toolkit": "bash",
    "include": ["run_command"],
    "timeout_s": 60,
    "max_output_bytes": 65536,
    "deny_patterns": [r"^\s*rm\s+-rf\s+/"],
}
CONTRACT_ROWS = [FILE_ROW, PYTHON_ROW, BASH_ROW]
CONTRACT_IDS = ["file", "python", "bash"]


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


# ---------------------------------------------------------------------------
# Save payload
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", CONTRACT_ROWS, ids=CONTRACT_IDS)
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

    # Identity, not equality: the point is that the caller's object survived the
    # response round-trip, not that an equal one was rebuilt from the dicts.
    assert agent.tools[0] is tool


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


def test_a_builtin_only_agent_passes_run_dependency_validation(aix):
    """`_validate_run_dependencies` is a separate walk from the save-time one.

    It formats an unsaved tool as ``tool '{tool.name}'`` without a getattr guard,
    so a toolkit that ever grew an ``id`` would raise ``AttributeError`` here
    rather than the clean message the save-time path produces.
    """
    tool = BuiltinTool(toolkit="bash", timeout_s=60)
    agent = aix.Agent(name="workspace-agent", tools=[tool])

    agent._validate_run_dependencies()

    assert agent.tools == [tool]


def test_save_subcomponents_does_not_try_to_save_a_toolkit(aix):
    """`_save_subcomponents` calls `save()` on tools that expose one; a toolkit does not."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [FILE_ROW]})
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="file")])

    agent.save(save_subcomponents=True)

    assert aix.client.request.call_args.kwargs["json"]["tools"] == [{"type": "builtin", "toolkit": "file"}]


def test_the_client_exposes_builtin_tool(aix):
    """`aix.BuiltinTool` is the documented entry point alongside `aix.Agent`/`aix.Tool`."""
    assert aix.BuiltinTool is BuiltinTool


def test_a_builtin_toolkit_is_skipped_by_run_time_parameter_overrides(aix):
    """`_build_tool_overrides` walks every `ToolableMixin`; a toolkit has no id to key on.

    Without the id guard it would emit `{"id": None, ...}` and the backend would
    fail to match it against any tool.
    """
    agent = aix.Agent(name="workspace-agent", tools=[BuiltinTool(toolkit="python", timeout_s=30)])

    assert agent._build_tool_overrides() == []


def test_an_unknown_server_key_survives_a_fetch_and_re_save(aix):
    """A backend newer than the SDK must not lose settings by being fetched and saved."""
    row = {"type": "builtin", "toolkit": "python", "timeout_s": 10, "sandbox_profile": "strict"}
    aix.client.get = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "tools": [row]})

    agent = aix.Agent.get("agent-id")

    assert isinstance(agent.tools[0], BuiltinTool)
    assert agent.build_save_payload()["tools"] == [row]


# ---------------------------------------------------------------------------
# Review regressions (ENG-3699)
# ---------------------------------------------------------------------------


def test_to_dict_keeps_the_type_discriminator_and_round_trips(aix):
    """`BuiltinTool` is a dataclass, so a naive to_dict() emits its raw fields.

    That row has no ``type``, which ``from_dict`` cannot rebuild and the worker
    drops — a silent loss for anyone snapshotting an agent via ``to_dict()``.
    """
    agent = aix.Agent(name="snapshot", tools=[BuiltinTool(toolkit="python", timeout_s=5)])

    snapshot = agent.to_dict()

    assert snapshot["tools"] == [{"type": "builtin", "toolkit": "python", "timeout_s": 5}]
    restored = type(agent).from_dict(snapshot)
    assert isinstance(restored.tools[0], BuiltinTool)
    assert restored.build_save_payload()["tools"][0]["type"] == "builtin"


def test_a_builtin_row_carrying_an_id_is_not_rebuilt_as_an_asset_tool(aix):
    """The asset branch would turn it into {"type": "tool", "assetId": ...}."""
    agent = aix.Agent(name="with id", tools=[{"type": "builtin", "toolkit": "file", "id": "68f0000000000000000000aa"}])

    assert isinstance(agent.tools[0], BuiltinTool)
    row = agent.build_save_payload()["tools"][0]
    assert row["type"] == "builtin" and row["toolkit"] == "file"
    assert "id" not in row and "assetId" not in row


def test_a_malformed_row_for_a_known_toolkit_is_rejected(aix):
    """Silence here ships the broken row to the backend."""
    with pytest.raises(ValueError, match="Unknown tool"):
        aix.Agent(name="bad", tools=[{"type": "builtin", "toolkit": "file", "include": ["run_python"]}])


def test_a_row_for_an_unknown_toolkit_is_kept_verbatim(aix):
    """A newer backend may know a toolkit this SDK does not; the row must survive."""
    agent = aix.Agent(name="future", tools=[{"type": "builtin", "toolkit": "rust", "timeout_s": 5}])

    assert agent.tools[0] == {"type": "builtin", "toolkit": "rust", "timeout_s": 5}
    assert agent.build_save_payload()["tools"][0]["toolkit"] == "rust"


def test_an_unhydrated_builtin_row_still_tracks_edits(aix):
    """An id-less row is its own identity; collapsing it hides in-place edits."""
    agent = aix.Agent(name="future", tools=[{"type": "builtin", "toolkit": "rust"}])
    agent._update_saved_state()

    agent.tools[0]["toolkit"] = "zig"

    assert agent.is_modified


def test_an_unbound_agent_without_builtins_keeps_the_callers_list(aix):
    """Hydration must not replace a list object it has nothing to convert in."""
    tools = [{"id": "68f0000000000000000000aa", "type": "model"}]

    from aixplain.v2.agent import Agent

    assert Agent(name="plain", tools=tools).tools is tools
