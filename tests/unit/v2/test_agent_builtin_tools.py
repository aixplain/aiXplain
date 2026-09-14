"""Tests for the ``builtin_tools`` capability field on the v2 Agent (ENG-3699).

Built-in toolkits are a toggle on the agent, not asset rows in ``tools``. The
tests below are therefore mostly about what the SDK does *not* do: it does not
validate, dedupe, case-fold or reorder the list, and the field is invisible to
every code path that walks ``tools``.
"""

from unittest.mock import Mock

import pytest

from aixplain import Aixplain
from aixplain.v2 import BuiltinToolkit
from aixplain.v2.agent import Agent


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_enabled_toolkits_are_emitted_as_builtin_tools(aix):
    """The wire key is camelCase `builtinTools`, matching `assets` / `llmId`."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file", "python"])

    assert agent.to_dict()["builtinTools"] == ["file", "python"]


def test_an_agent_that_never_touched_the_field_omits_it_entirely(aix):
    """Absent, not null: every existing agent's payload must be unchanged."""
    agent = aix.Agent(name="plain-agent", instructions="hi")

    assert "builtinTools" not in agent.to_dict()
    assert "builtinTools" not in agent.build_save_payload()


def test_an_explicit_empty_list_is_emitted(aix):
    """`[]` is how a caller turns off the toolkits an agent already has.

    The backend treats absent, `null` and `[]` alike, so this only matters on the
    way *out*: omitting `[]` would leave the previously-saved toolkits in place.
    """
    agent = aix.Agent(name="workspace-agent", builtin_tools=[])

    assert agent.to_dict()["builtinTools"] == []


def test_the_field_reaches_the_save_payload(aix):
    """`build_save_payload` starts from `to_dict()`, so this needs no plumbing."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file", "python"])

    assert agent.build_save_payload()["builtinTools"] == ["file", "python"]


def test_builtin_tools_do_not_appear_in_the_tools_list(aix):
    """The mistake this design reverts: a toggle is not an asset row."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])

    assert agent.build_save_payload()["tools"] == []


def test_the_field_is_absent_from_a_run_payload(aix):
    """It is agent-definition state, not a per-run parameter."""
    agent = aix.Agent(id="agent-id", name="workspace-agent", builtin_tools=["file"])

    assert "builtinTools" not in agent.build_run_payload(query="hello")


# ---------------------------------------------------------------------------
# The SDK never validates
# ---------------------------------------------------------------------------


def test_unknown_toolkit_names_pass_through_untouched(aix):
    """The worker drops an unknown toolkit with a warning; the SDK must not raise.

    Order, case and duplicates are all preserved: the backend dedupes on save and
    the worker normalizes, so normalizing here too would mean `agent.builtin_tools`
    no longer reads back what the caller wrote.
    """
    requested = ["banana", "FILE", "file", "file"]

    agent = aix.Agent(name="workspace-agent", builtin_tools=requested)

    assert agent.to_dict()["builtinTools"] == ["banana", "FILE", "file", "file"]


def test_a_toolkit_appended_after_construction_is_not_validated_either(aix):
    """There is no setter hook, so this is a statement about there being no hook."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])

    agent.builtin_tools.append("not-a-toolkit")

    assert agent.to_dict()["builtinTools"] == ["file", "not-a-toolkit"]


# ---------------------------------------------------------------------------
# The optional enum
# ---------------------------------------------------------------------------


def test_enum_members_serialize_as_plain_strings(aix):
    """`BuiltinToolkit` is autocompletion sugar, never a requirement."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=[BuiltinToolkit.FILE, BuiltinToolkit.PYTHON])

    assert agent.builtin_tools == ["file", "python"]
    assert agent.to_dict()["builtinTools"] == ["file", "python"]


def test_enum_members_and_strings_mix_freely(aix):
    """A caller migrating to the enum must not have to convert the whole list."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=[BuiltinToolkit.FILE, "python"])

    assert agent.to_dict()["builtinTools"] == ["file", "python"]


def test_an_enum_member_appended_after_construction_still_serializes(aix):
    """`BuiltinToolkit` subclasses `str`, so the post-init coercion is cosmetic."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])

    agent.builtin_tools.append(BuiltinToolkit.BASH)

    assert agent.to_dict()["builtinTools"] == ["file", "bash"]


def test_the_enum_covers_exactly_the_documented_toolkits():
    """A fourth toolkit is a new member here, not a schema change."""
    assert {member.value for member in BuiltinToolkit} == {"file", "python", "bash"}


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_from_dict_hydrates_the_field():
    """`get()` decodes through dataclasses-json; no hydration hook is involved."""
    agent = Agent.from_dict({"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file", "python"]})

    assert agent.builtin_tools == ["file", "python"]


@pytest.mark.parametrize("response", [{}, {"builtinTools": None}], ids=["absent", "null"])
def test_a_response_without_the_key_leaves_the_field_unset(response):
    """Pre-ENG-3698 the backend returns neither; both must mean "nothing to say"."""
    agent = Agent.from_dict({"id": "agent-id", "name": "workspace-agent", **response})

    assert agent.builtin_tools is None
    assert "builtinTools" not in agent.to_dict()


def test_get_then_mutate_then_save_puts_the_new_list_on_the_wire(aix):
    """The documented workflow: fetch, append a toolkit, save."""
    aix.client.get = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file"]})
    aix.client.request = Mock(
        return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file", "bash"]}
    )
    agent = aix.Agent.get("agent-id")
    assert agent.builtin_tools == ["file"]

    agent.builtin_tools.append("bash")
    agent.save()

    assert aix.client.request.call_args.kwargs["json"]["builtinTools"] == ["file", "bash"]
    assert agent.builtin_tools == ["file", "bash"]


def test_saving_a_fetched_agent_that_was_not_edited_re_sends_the_same_list(aix):
    """A fetch-then-save round-trip must not quietly drop the toolkits."""
    aix.client.get = Mock(
        return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file", "python"]}
    )
    aix.client.request = Mock(
        return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file", "python"]}
    )
    agent = aix.Agent.get("agent-id")

    agent.save()

    assert aix.client.request.call_args.kwargs["json"]["builtinTools"] == ["file", "python"]


def test_appending_a_toolkit_marks_a_saved_agent_modified(aix):
    """`is_modified` reads `to_dict()`, so the field is covered with no extra code."""
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file"]})
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])
    agent.save()
    assert not agent.is_modified

    agent.builtin_tools.append("bash")

    assert agent.is_modified


# ---------------------------------------------------------------------------
# The field is invisible to the tool-saving machinery
# ---------------------------------------------------------------------------


def test_an_agent_whose_only_capability_is_a_toolkit_validates(aix):
    """`_validate_dependencies` walks `tools`; a capability list is not one."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file", "python"])

    agent._validate_dependencies()

    assert agent.builtin_tools == ["file", "python"]


def test_an_agent_whose_only_capability_is_a_toolkit_saves_subcomponents(aix):
    """The regression class this design removes: nothing here resembles a tool.

    Under the reverted asset-row design, an object in `tools` with an `id`
    attribute tripped `_validate_dependencies`, and one with a `save` method was
    called by `_save_subcomponents`. A list of strings has no analogue for either.
    """
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent", "builtinTools": ["file"]})
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])

    agent.save(save_subcomponents=True)

    payload = aix.client.request.call_args.kwargs["json"]
    assert payload["builtinTools"] == ["file"]
    assert payload["tools"] == []


def test_toolkits_and_asset_tools_coexist(aix):
    """The two lists are orthogonal; enabling a toolkit must not disturb `tools`."""
    agent = aix.Agent(
        name="mixed-agent",
        tools=[{"id": "tool-id", "type": "model", "asset_id": "tool-id"}],
        builtin_tools=["python"],
    )

    payload = agent.build_save_payload()

    assert payload["builtinTools"] == ["python"]
    assert payload["tools"][0]["assetId"] == "tool-id"


def test_a_bare_string_is_wrapped_rather_than_exploded_into_characters(aix):
    """`builtin_tools="file"` is the obvious slip on a list-valued field.

    Iterating the string would enable `f`, `i`, `l` and `e` as four separate
    toolkits — all unknown, so the worker would drop them with warnings and the
    agent would silently end up with no toolkit at all.
    """
    agent = aix.Agent(name="workspace-agent", builtin_tools="file")

    assert agent.to_dict()["builtinTools"] == ["file"]


def test_a_lone_enum_member_is_wrapped_too(aix):
    """`BuiltinToolkit` subclasses `str`, so it takes the same scalar path."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=BuiltinToolkit.PYTHON)

    assert agent.to_dict()["builtinTools"] == ["python"]


def test_a_non_list_sequence_is_normalized_to_a_list(aix):
    """A tuple is a reasonable thing to pass; `to_dict()` must still emit JSON."""
    agent = aix.Agent(name="workspace-agent", builtin_tools=("file", "python"))

    assert agent.to_dict()["builtinTools"] == ["file", "python"]


def test_the_callers_list_is_not_aliased(aix):
    """Rebuilding the list in post-init must also decouple it from the caller's."""
    requested = ["file"]
    agent = aix.Agent(name="workspace-agent", builtin_tools=requested)

    requested.append("bash")

    assert agent.builtin_tools == ["file"]


def test_a_backend_that_does_not_echo_the_key_does_not_clear_the_field(aix):
    """Until ENG-3698 lands, the create response carries no `builtinTools`.

    The in-memory agent must keep what it sent, or a save-then-save sequence
    would drop the toolkits on the second call.
    """
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "workspace-agent"})
    agent = aix.Agent(name="workspace-agent", builtin_tools=["file"])

    agent.save()

    assert agent.builtin_tools == ["file"]
    assert aix.client.request.call_args.kwargs["json"]["builtinTools"] == ["file"]


def test_the_field_is_not_marked_auto_deserialize_only():
    """A `decoder` here would silently null the field out on every save.

    `resource.py`'s `_create` merge loop skips fields that are excluded from
    serialization *unless* they also define a `decoder` — that pairing is the
    codebase's "manually serialized, auto-deserialized" marker (`_role_field`).
    `builtin_tools` relies on the skip: today's backend does not echo
    `builtinTools`, so copying the response's value back would replace the
    caller's list with `None`. Adding a decoder to tidy up response parsing
    would reintroduce exactly that, and only the save path would show it.
    """
    from aixplain.v2.resource import _is_auto_deserialize_only, _is_excluded_from_serialization

    field_def = Agent.__dataclass_fields__["builtin_tools"]

    assert _is_excluded_from_serialization(field_def)
    assert not _is_auto_deserialize_only(field_def)
