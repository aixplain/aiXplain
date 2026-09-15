"""Tests for run ``warnings`` decoding and step unit-name extraction (ENG-3699)."""

import warnings

from aixplain.v2.agent import AgentResponseData, AgentRunResult, _step_unit_names

GATED_BASH = "Built-in toolkit 'bash' is not enabled on this worker — skipped"

# Step shapes observed on dev: tool steps and LLM steps both name the unit at ``unit.name``.
TOOL_STEP = {
    "unit": {"id": None, "name": "write_file", "path": None, "type": "tool"},
    "step_id": "call_abc",
    "input": "{}",
    "output": "ok",
}
LLM_STEP = {"unit": {"id": "69b7e5f1b2fe44704ab0e7d0", "name": "GPT-5.4"}, "step_id": "llm-abc"}


# ---------------------------------------------------------------------------
# warnings
# ---------------------------------------------------------------------------


def test_warnings_are_decoded_from_the_payload():
    assert AgentResponseData.from_dict({"output": "ok", "warnings": [GATED_BASH]}).warnings == [GATED_BASH]


def test_absent_warnings_decode_to_an_empty_list():
    assert AgentResponseData.from_dict({"output": "ok"}).warnings == []


def test_null_warnings_decode_to_an_empty_list_without_a_runtime_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        data = AgentResponseData.from_dict({"warnings": None})

    assert data.warnings == []
    assert [str(w.message) for w in caught] == []


def test_a_non_list_is_not_iterated_into_characters():
    assert AgentResponseData.from_dict({"warnings": "oops"}).warnings == []


def test_non_string_entries_are_dropped():
    assert AgentResponseData.from_dict({"warnings": ["a", 1, None, {"x": 1}, "b"]}).warnings == ["a", "b"]


def test_direct_construction_is_normalized_too():
    assert AgentResponseData(warnings=None).warnings == []
    assert AgentResponseData().warnings == []


def test_warnings_reach_a_run_result_decoded_the_way_poll_decodes_it():
    result = AgentRunResult.from_dict(
        {"status": "SUCCESS", "completed": True, "data": {"output": "ok", "warnings": [GATED_BASH]}}
    )

    assert result.data.warnings == [GATED_BASH]


# ---------------------------------------------------------------------------
# _step_unit_names
# ---------------------------------------------------------------------------


def test_unit_names_are_read_from_the_dev_step_shape():
    names = _step_unit_names([LLM_STEP, TOOL_STEP])

    assert "write_file" in names
    assert "GPT-5.4" in names


def test_flat_keys_are_kept_as_a_fallback():
    assert _step_unit_names([{"tool": "run_python"}]) == {"run_python"}


def test_unit_name_wins_over_a_flat_name_on_the_same_step():
    assert _step_unit_names([{"unit": {"name": "read_file"}, "name": "stale"}]) == {"read_file"}


def test_a_unit_without_a_name_falls_back_to_flat_keys():
    assert _step_unit_names([{"unit": {"id": "x", "name": None}, "toolName": "glob"}]) == {"glob"}


def test_malformed_steps_yield_an_empty_set():
    assert _step_unit_names(None) == set()
    assert _step_unit_names("steps") == set()
    assert _step_unit_names([None, "x", 3]) == set()


# ---------------------------------------------------------------------------
# AgentRunResult.warnings
# ---------------------------------------------------------------------------


def test_run_result_warnings_read_the_nested_data_field():
    result = AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "data": {"warnings": [GATED_BASH]}})

    assert result.warnings == [GATED_BASH]


def test_run_result_warnings_fall_back_to_a_top_level_key_the_poll_allow_list_drops():
    raw = {"status": "SUCCESS", "completed": True, "data": {"output": "ok"}, "warnings": [GATED_BASH]}
    result = AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "data": raw["data"]})
    result._raw_data = raw

    assert result.warnings == [GATED_BASH]


def test_run_result_warnings_accept_a_hand_built_dict_data():
    assert AgentRunResult(status="SUCCESS", completed=True, data={"warnings": [GATED_BASH, 3]}).warnings == [GATED_BASH]


def test_run_result_without_warnings_is_an_empty_list():
    assert AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "data": {"output": "ok"}}).warnings == []
    assert AgentRunResult(status="SUCCESS", completed=True).warnings == []
