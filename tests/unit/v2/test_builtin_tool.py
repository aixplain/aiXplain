"""Tests for :class:`aixplain.v2.BuiltinTool` (ENG-3699).

The wire contract is owned by the agent worker, so the serialization tests below
assert the three contract rows field-by-field rather than spot-checking keys: a
renamed key here is a capability the worker silently drops.
"""

import dataclasses

import pytest

from aixplain.v2 import BuiltinTool
from aixplain.v2.builtin_tool import TOOLKIT_SETTINGS, TOOLKIT_TOOLS

#: The rows the worker accepts, verbatim from the ENG-3699 contract.
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


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("toolkit", ["file", "python", "bash"])
def test_bare_toolkit_emits_only_the_discriminator_and_the_toolkit(toolkit):
    """An unconfigured toolkit sends nothing else, so the worker's defaults apply."""
    assert BuiltinTool(toolkit=toolkit).as_tool() == {"type": "builtin", "toolkit": toolkit}


def test_fully_configured_file_toolkit_matches_the_contract_row():
    """The `file` row from the frozen wire contract, key for key."""
    tool = BuiltinTool(
        toolkit="file",
        include=["read_file", "list_directory", "glob", "grep", "write_file", "edit_file"],
        max_read_bytes=262144,
        max_results=500,
    )

    assert tool.as_tool() == FILE_ROW


def test_fully_configured_python_toolkit_matches_the_contract_row():
    """The `python` row from the frozen wire contract, key for key."""
    tool = BuiltinTool(toolkit="python", include=["run_python"], timeout_s=10, expose_files=False)

    assert tool.as_tool() == PYTHON_ROW


def test_fully_configured_bash_toolkit_matches_the_contract_row():
    """The `bash` row from the frozen wire contract, key for key."""
    tool = BuiltinTool(
        toolkit="bash",
        include=["run_command"],
        timeout_s=60,
        max_output_bytes=65536,
        deny_patterns=[r"^\s*rm\s+-rf\s+/"],
    )

    assert tool.as_tool() == BASH_ROW


def test_include_is_emitted_in_the_order_given():
    """The worker treats it as a set, but a reordered list makes diffs unreadable."""
    tool = BuiltinTool(toolkit="file", include=["grep", "read_file", "glob"])

    assert tool.as_tool()["include"] == ["grep", "read_file", "glob"]


def test_include_is_copied_so_later_mutation_cannot_reach_a_sent_row():
    """`as_tool()` snapshots; mutating the caller's list must not rewrite history."""
    names = ["read_file"]
    tool = BuiltinTool(toolkit="file", include=names)
    row = tool.as_tool()

    names.append("grep")

    assert row["include"] == ["read_file"]


def test_omitted_include_is_absent_rather_than_null():
    """`None` means "every tool in the toolkit", which the worker reads as omission."""
    assert "include" not in BuiltinTool(toolkit="python").as_tool()


def test_expose_files_false_is_sent_because_unset_is_not_false():
    """`Optional[bool]` exists precisely so an explicit False survives."""
    assert BuiltinTool(toolkit="python", expose_files=False).as_tool()["expose_files"] is False


def test_expose_files_unset_is_not_sent():
    """The complement of the test above: absence must stay absence."""
    assert "expose_files" not in BuiltinTool(toolkit="python", timeout_s=5).as_tool()


@pytest.mark.parametrize("row", CONTRACT_ROWS, ids=["file", "python", "bash"])
def test_no_asset_identity_keys_ever_appear(row):
    """A builtin toolkit is not an onboarded asset and must not pretend to be one."""
    serialized = BuiltinTool.from_api_dict(row).as_tool()

    assert not {"id", "assetId", "asset_id", "workspace_root"} & set(serialized)


def test_the_wire_keys_are_snake_case():
    """The worker's contract is snake_case; a camelCase drift silently drops settings."""
    row = BuiltinTool(toolkit="file", max_read_bytes=1024, max_results=10).as_tool()

    assert set(row) == {"type", "toolkit", "max_read_bytes", "max_results"}


def test_type_is_read_only_and_not_a_constructor_argument():
    """The discriminator routes the row to the worker; it is not user-settable."""
    assert BuiltinTool(toolkit="file").type == "builtin"
    assert "type" not in {f.name for f in dataclasses.fields(BuiltinTool)}
    with pytest.raises(TypeError):
        BuiltinTool(toolkit="file", type="model")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_unknown_toolkit_names_the_allowed_toolkits():
    """A typo in the toolkit is a construction-time error, not a silent no-op."""
    with pytest.raises(ValueError, match=r"Unknown toolkit 'phyton'.*\['bash', 'file', 'python'\]"):
        BuiltinTool(toolkit="phyton")


@pytest.mark.parametrize(
    ("toolkit", "bad_name"),
    [("file", "read_files"), ("python", "run_bash"), ("bash", "run_python")],
)
def test_unknown_include_name_names_the_allowed_tools(toolkit, bad_name):
    """A tool name from another toolkit (or a typo) is rejected with the real set."""
    with pytest.raises(ValueError) as excinfo:
        BuiltinTool(toolkit=toolkit, include=[bad_name])

    message = str(excinfo.value)
    assert bad_name in message
    assert str(sorted(TOOLKIT_TOOLS[toolkit])) in message


def test_empty_include_is_rejected_as_ambiguous():
    """`[]` could read as "no tools" or "all tools"; `None` is the documented "all"."""
    with pytest.raises(ValueError, match="include must name at least one tool"):
        BuiltinTool(toolkit="file", include=[])


@pytest.mark.parametrize(
    ("toolkit", "setting", "value"),
    [
        ("file", "timeout_s", 10),
        ("file", "expose_files", True),
        ("file", "deny_patterns", ["rm"]),
        ("python", "max_read_bytes", 1024),
        ("python", "deny_patterns", ["rm"]),
        ("python", "max_output_bytes", 1024),
        ("bash", "expose_files", True),
        ("bash", "max_results", 5),
    ],
)
def test_setting_from_the_wrong_toolkit_names_the_allowed_settings(toolkit, setting, value):
    """Silently ignoring a misplaced setting is the failure mode this prevents."""
    with pytest.raises(ValueError) as excinfo:
        BuiltinTool(toolkit=toolkit, **{setting: value})

    message = str(excinfo.value)
    assert setting in message
    assert str(sorted(TOOLKIT_SETTINGS[toolkit])) in message


def test_every_misplaced_setting_is_reported_at_once():
    """Fixing one setting only to hit the next error is a poor first experience."""
    with pytest.raises(ValueError, match=r"\['expose_files', 'timeout_s'\]"):
        BuiltinTool(toolkit="file", timeout_s=1, expose_files=True)


def test_timeout_s_is_shared_by_python_and_bash():
    """`timeout_s` lives in two toolkits; neither may reject it as misplaced."""
    assert BuiltinTool(toolkit="python", timeout_s=5).as_tool()["timeout_s"] == 5
    assert BuiltinTool(toolkit="bash", timeout_s=5).as_tool()["timeout_s"] == 5


# ---------------------------------------------------------------------------
# The value-object invariants Agent integration depends on
# ---------------------------------------------------------------------------


def test_builtin_tool_exposes_neither_id_nor_save():
    """`Agent._validate_dependencies` and `_save_subcomponents` gate on these.

    Both walk ``agent.tools`` and act on any entry with an ``id`` attribute or a
    ``save`` method — a builtin toolkit has neither and must keep it that way, or
    every agent carrying one would fail to save as an "unsaved component".
    """
    tool = BuiltinTool(toolkit="file")

    assert not hasattr(tool, "id")
    assert not hasattr(tool, "save")


def test_builtin_tools_compare_by_configuration():
    """Change detection reads equality; two identical attachments are the same."""
    assert BuiltinTool(toolkit="python", timeout_s=30) == BuiltinTool(toolkit="python", timeout_s=30)
    assert BuiltinTool(toolkit="python", timeout_s=30) != BuiltinTool(toolkit="python", timeout_s=60)


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", CONTRACT_ROWS, ids=["file", "python", "bash"])
def test_a_persisted_row_round_trips_unchanged(row):
    """`get()` then `save()` must not rewrite a row the user never touched."""
    assert BuiltinTool.from_api_dict(row).as_tool() == row


@pytest.mark.parametrize("row", CONTRACT_ROWS, ids=["file", "python", "bash"])
def test_from_api_dict_populates_the_typed_fields(row):
    """The point of hydrating is attribute access, not just a faithful re-emit."""
    tool = BuiltinTool.from_api_dict(row)

    assert tool.toolkit == row["toolkit"]
    assert tool.include == row["include"]
    for setting in TOOLKIT_SETTINGS[row["toolkit"]]:
        assert getattr(tool, setting) == row[setting]


def test_an_unknown_server_key_survives_the_round_trip():
    """A backend newer than the SDK must not lose settings by being fetched."""
    row = {"type": "builtin", "toolkit": "python", "timeout_s": 10, "sandbox_profile": "strict"}

    assert BuiltinTool.from_api_dict(row).as_tool() == row


def test_a_server_only_key_is_dropped_in_both_directions():
    """`workspace_root` is the worker's to choose; echoing it back would pin it."""
    row = {"type": "builtin", "toolkit": "file", "workspace_root": "/mnt/agent-42"}

    tool = BuiltinTool.from_api_dict(row)

    assert tool.as_tool() == {"type": "builtin", "toolkit": "file"}


def test_a_setting_belonging_to_another_toolkit_is_carried_not_rejected():
    """Inbound rows are lenient: hydration must never fail on a live agent."""
    row = {"type": "builtin", "toolkit": "file", "timeout_s": 10}

    tool = BuiltinTool.from_api_dict(row)

    assert tool.timeout_s is None
    assert tool.as_tool() == row


def test_a_row_without_a_toolkit_is_rejected():
    """`from_api_dict` stays strict; ``Agent`` is the layer that degrades to a dict."""
    with pytest.raises(ValueError, match="must carry a 'toolkit'"):
        BuiltinTool.from_api_dict({"type": "builtin"})


def test_a_row_with_an_unknown_toolkit_is_rejected():
    """Same contract: unmappable in, exception out, caller decides what to do."""
    with pytest.raises(ValueError, match="Unknown toolkit"):
        BuiltinTool.from_api_dict({"type": "builtin", "toolkit": "rust"})


# ---------------------------------------------------------------------------
# The registries themselves
# ---------------------------------------------------------------------------


def test_the_toolkit_registries_describe_the_same_toolkits():
    """A toolkit with tools but no settings entry would crash `as_tool()`."""
    assert set(TOOLKIT_TOOLS) == set(TOOLKIT_SETTINGS)


def test_every_declared_setting_is_a_real_field():
    """`TOOLKIT_SETTINGS` drives `getattr`; a stale name would raise at runtime."""
    fields = {f.name for f in dataclasses.fields(BuiltinTool)}
    declared = {name for names in TOOLKIT_SETTINGS.values() for name in names}

    assert declared <= fields


def test_a_non_string_toolkit_is_a_value_error_not_a_type_error():
    """An unhashable toolkit must not escape the membership test as a TypeError."""
    with pytest.raises(ValueError, match="Unknown toolkit"):
        BuiltinTool(toolkit=["file"])

    with pytest.raises(ValueError, match="Unknown toolkit"):
        BuiltinTool.from_api_dict({"type": "builtin", "toolkit": ["file"]})


def test_include_is_snapshotted_so_a_later_mutation_cannot_bypass_validation():
    """Validation runs once; an aliased list would let an unknown name in afterwards."""
    names = ["read_file"]
    tool = BuiltinTool(toolkit="file", include=names)

    names.append("not_a_real_tool")

    assert tool.include == ["read_file"]


def test_deny_patterns_is_snapshotted_too():
    """The one other list-valued setting; same aliasing hazard."""
    patterns = [r"^\s*rm\b"]
    tool = BuiltinTool(toolkit="bash", deny_patterns=patterns)

    patterns.append("everything")

    assert tool.deny_patterns == [r"^\s*rm\b"]


def test_from_api_dict_does_not_alias_the_response_row():
    """Editing a fetched toolkit must not reach back into the response dict."""
    row = {"type": "builtin", "toolkit": "file", "include": ["read_file"]}

    BuiltinTool.from_api_dict(row).include.append("grep")

    assert row["include"] == ["read_file"]


def test_an_emitted_row_never_shares_a_list_with_the_tool():
    """`as_tool()` is a snapshot for unknown server keys too, not just modelled ones."""
    tool = BuiltinTool.from_api_dict({"type": "builtin", "toolkit": "python", "allow_hosts": ["a"]})

    tool.as_tool()["allow_hosts"].append("b")

    assert tool.as_tool()["allow_hosts"] == ["a"]
