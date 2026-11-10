"""Tests for gated-toolkit run warnings and step unit-name extraction (ENG-3699)."""

from aixplain.v2.agent import AgentResponseData, AgentRunResult, AgentWarning, _step_unit_names

GATED_BASH = {"message": "Built-in toolkit 'bash' is not enabled on this worker"}

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


def test_a_gated_toolkit_warning_is_decoded_on_the_response_data():
    data = AgentResponseData.from_dict({"output": "ok", "warnings": [GATED_BASH]})

    assert data.warnings == [AgentWarning(**GATED_BASH)]


def test_a_gated_toolkit_warning_reaches_the_run_result():
    result = AgentRunResult.from_dict(
        {"status": "SUCCESS", "completed": True, "data": {"output": "ok", "warnings": [GATED_BASH]}}
    )

    assert [w.message for w in result.warnings] == [GATED_BASH["message"]]


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
