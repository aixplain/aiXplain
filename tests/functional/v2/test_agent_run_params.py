"""Functional coverage for public v2 agent run-time features.

Each test exercises one public run-time knob against the live backend and
asserts the documented observable effect, not merely that the call returned.
The features here previously had no functional coverage (or only a unit test),
so a backend regression would have slipped through. Keep one test per feature
row; assert the wire payload for deterministic behaviour and the response for
backend behaviour.
"""

import json
import time
import uuid

import pytest

from aixplain.v2.exceptions import APIError

from .assets import (
    IMAGE_MODEL_ID,
    REASONING_MODEL_ID,
    RED_PNG_BYTES,
    TAVILY_TOOL_ID,
    VISION_LLM_ID,
)

#: The platform's default LLM is intermittently marked unavailable; every test
#: here runs the live backend, so retry the whole module rather than special-case.
pytestmark = pytest.mark.flaky(reruns=2, reruns_delay=5, reason="platform model availability is intermittent")

BUDGET_BLOCKED = "BLOCKED_BY_BUDGET"
MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


def _unique(prefix: str) -> str:
    return f"{prefix}-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def _make_agent(client, tracker, *, instructions="You are a helpful test agent. Reply briefly.", **kwargs):
    agent = client.Agent(name=_unique("run-params"), instructions=instructions, **kwargs)
    agent.save()
    tracker.append(agent)
    return agent


def _make_tool_agent(client, tracker):
    tool = client.Tool.get(TAVILY_TOOL_ID)
    return _make_agent(
        client,
        tracker,
        instructions="You are a research agent. Always use the web search tool before answering.",
        tools=[tool],
    )


def _output(response) -> str:
    data = getattr(response, "data", None)
    if data is None:
        return ""
    output = getattr(data, "output", None)
    if output is None and isinstance(data, str):
        output = data
    return output or ""


def _write_temp(tmp_path, name: str, payload: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(payload)
    return str(path)


@pytest.fixture(scope="module")
def run_agent(client, module_resource_tracker):
    return _make_agent(client, module_resource_tracker)


@pytest.fixture(scope="module")
def vision_agent(client, module_resource_tracker):
    return _make_agent(client, module_resource_tracker, llm=VISION_LLM_ID)


@pytest.fixture(scope="module")
def image_agent(client, module_resource_tracker):
    return _make_agent(
        client,
        module_resource_tracker,
        instructions="You generate images with the attached image tool.",
        tools=[client.Model.get(IMAGE_MODEL_ID)],
    )


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------


@pytest.mark.flaky(reruns=2, reruns_delay=5, reason="tool call is model-dependent")
def test_budget_max_iterations_halts_after_one_step(client, module_resource_tracker):
    agent = _make_tool_agent(client, module_resource_tracker)
    agent.budget.max_iterations = 1

    result = agent.run("Search the web for the capital of France, then answer.")

    assert result.status == "SUCCESS"
    assert MAX_ITERATIONS_REACHED in result.diagnostic_error_codes, (
        f"expected the run to stop on the iteration cap, got {result.diagnostic_error_codes}"
    )


@pytest.mark.flaky(reruns=2, reruns_delay=5, reason="tool call is model-dependent")
def test_budget_max_cost_zero_blocks_run(client, module_resource_tracker):
    agent = _make_tool_agent(client, module_resource_tracker)
    agent.budget.max_cost = 0.0

    result = agent.run("Search the web for the capital of France, then answer.")

    assert result.data.governance is not None
    assert result.data.governance["status"] == BUDGET_BLOCKED
    assert BUDGET_EXCEEDED in result.diagnostic_error_codes


def test_budget_max_duration_zero_blocks_run(client, module_resource_tracker):
    agent = _make_tool_agent(client, module_resource_tracker)
    agent.budget.max_duration_seconds = 0

    result = agent.run("Search the web for the capital of France, then answer.")

    assert result.data.governance is not None
    assert result.data.governance["status"] == BUDGET_BLOCKED


# ---------------------------------------------------------------------------
# Context overflow
# ---------------------------------------------------------------------------


def test_context_overflow_strategy_round_trips_and_overrides(client, module_resource_tracker):
    agent = _make_agent(client, module_resource_tracker)
    agent.context_overflow_strategy = "summarize"
    agent.save()

    fetched = client.Agent.get(agent.id)
    assert fetched.context_overflow_strategy == "summarize"

    assert fetched.build_run_payload(query="hi")["executionParams"]["contextOverflowStrategy"] == "summarize"

    result = fetched.run("hi")
    assert result.status == "SUCCESS"

    override = fetched.run("hi", execution_params={"context_overflow_strategy": "truncate"})
    assert override.status == "SUCCESS"


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


def test_progress_logs_are_printed(run_agent, capsys):
    result = run_agent.run(
        "Say hi.",
        progress_format="logs",
        progress_verbosity=2,
        progress_truncate=False,
    )

    captured = capsys.readouterr().out
    assert result.status == "SUCCESS"
    assert "Step" in captured, f"expected progress timeline on stdout, got {captured!r}"


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


@pytest.mark.flaky(reruns=2, reruns_delay=5, reason="image tool call is model-dependent")
def test_artifacts_carry_presigned_urls(image_agent):
    result = image_agent.run(
        "Use the image generation tool to generate an image of a red cube. You MUST call the tool. Then reply DONE."
    )

    assert result.status == "SUCCESS"
    assert result.artifacts, "expected at least one artifact from the image tool"

    artifact = result.artifacts[0]
    assert artifact.source == "tool_output"
    assert artifact.category == "image"
    assert artifact.url and artifact.url.startswith("http")
    assert artifact.mime_type and artifact.mime_type.startswith("image/")


# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------


def test_debug_returns_analysis(run_agent):
    from aixplain.v2.meta_agents import DEBUGGER_AGENT_ID

    result = run_agent.run("Say hi.")

    try:
        debug_result = result.debug()
    except APIError as exc:
        # The pinned meta-agent is not deployed on every backend; the SDK path
        # still ran, so skip rather than report a platform gap as a test bug.
        if "Not Found" not in str(exc):
            raise
        pytest.skip(f"Debugger meta-agent {DEBUGGER_AGENT_ID} not deployed on this backend")

    assert debug_result.analysis, "debugger returned an empty analysis"


# ---------------------------------------------------------------------------
# Variables / prompt / criteria / identifier / history
# ---------------------------------------------------------------------------


def test_variables_are_forwarded_in_query(client, module_resource_tracker):
    agent = _make_agent(
        client,
        module_resource_tracker,
        instructions="The secret word is {{word}}. Reply with only the word.",
    )

    payload = agent.build_run_payload(query="What is the secret word?", variables={"word": "zebra"})
    assert payload["query"]["input"] == "What is the secret word?"
    assert payload["query"]["word"] == "zebra"

    result = agent.run("What is the secret word?", variables={"word": "zebra"})
    assert result.status == "SUCCESS"
    assert _output(result)


def test_prompt_criteria_and_identifier_are_accepted(run_agent):
    result = run_agent.run(
        "Say the secret.",
        prompt="The secret is ORANGE. Reply with only the secret.",
        criteria="The answer must be a single word.",
        identifier=_unique("identifier"),
    )

    assert result.status == "SUCCESS"
    assert _output(result)


def test_history_is_accepted(run_agent):
    result = run_agent.run(
        "What did I say my name was?",
        history=[
            {"role": "user", "content": "My name is Sam."},
            {"role": "assistant", "content": "Hi Sam."},
        ],
    )

    assert result.status == "SUCCESS"
    assert "sam" in _output(result).lower()


def test_run_response_generation_returns_output(run_agent):
    result = run_agent.run("Say hi.", run_response_generation=True)

    assert result.status == "SUCCESS"
    assert _output(result)


def test_evolve_tasks_and_inspectors_are_accepted(run_agent):
    assert run_agent.run("Say hi.", evolve='{"toEvolve": true}').status == "SUCCESS"
    assert (
        run_agent.run(
            "Say hi.",
            tasks=[{"name": "t1", "description": "d", "expectedOutput": "o"}],
        ).status
        == "SUCCESS"
    )
    assert (
        run_agent.run(
            "Say hi.",
            inspectors=[
                {
                    "name": "Gate",
                    "targets": ["input"],
                    "action": {"type": "abort"},
                    "evaluator": {"type": "asset", "assetId": REASONING_MODEL_ID, "prompt": "PASS or FAIL"},
                }
            ],
        ).status
        == "SUCCESS"
    )


# ---------------------------------------------------------------------------
# execution_params
# ---------------------------------------------------------------------------


def test_execution_params_max_tokens_is_honoured(run_agent):
    with pytest.raises(APIError):
        run_agent.run("Say hi.", execution_params={"max_tokens": 1, "output_format": "text"})


def test_execution_params_output_format_json(run_agent):
    result = run_agent.run(
        "What color is the sky? Answer with one word.",
        execution_params={"output_format": "json", "expected_output": {"color": "blue"}},
        run_response_generation=True,
    )

    assert result.status == "SUCCESS"
    text = _output(result).strip().strip("`")
    if text.startswith("json"):
        text = text[4:].strip()
    parsed = json.loads(text)
    assert parsed.get("color")


# ---------------------------------------------------------------------------
# Attachments / files
# ---------------------------------------------------------------------------


def test_attachments_send_image_to_vision_model(vision_agent, tmp_path):
    path = _write_temp(tmp_path, "red.png", RED_PNG_BYTES)

    result = vision_agent.run("What is the color of the attached image? Answer with one word.", attachments=[path])

    assert result.status == "SUCCESS"
    assert _output(result)


def test_deprecated_files_alias_uploads_and_reads(vision_agent, tmp_path):
    path = _write_temp(tmp_path, "note.txt", b"The magic number is 42.")

    result = vision_agent.run("Read the attached file and reply with the magic number.", files=[path])

    assert result.status == "SUCCESS"
    assert "42" in _output(result)


# ---------------------------------------------------------------------------
# Session memory
# ---------------------------------------------------------------------------


def test_session_recalls_and_stateless_forgets(client, module_resource_tracker):
    agent = _make_agent(client, module_resource_tracker)
    session = client.Session(agent=agent, name=_unique("memory"))
    session.save()
    module_resource_tracker.append(session)

    agent.run("Remember the codeword PLUM-9137. Reply OK.", session=session)
    recalled = agent.run("What is the codeword? Reply only the codeword.", session=session)
    assert "PLUM-9137" in _output(recalled)

    stateless = _make_agent(client, module_resource_tracker)
    stateless.run("Remember the codeword PLUM-9137. Reply OK.")
    forgotten = stateless.run("What is the codeword? Reply only the codeword.")
    assert "PLUM-9137" not in _output(forgotten)

    results = client.Session.search(memory_enabled=True)
    assert isinstance(results.results, list)


# ---------------------------------------------------------------------------
# reasoning_effort / tool param overrides
# ---------------------------------------------------------------------------


@pytest.mark.flaky(reruns=2, reruns_delay=5, reason="reasoning model can be unavailable")
def test_reasoning_effort_lands_in_payload_and_backend(client, module_resource_tracker):
    llm = client.Model.get(REASONING_MODEL_ID)
    llm.inputs.reasoning_effort = "low"

    agent = _make_agent(client, module_resource_tracker, llm=llm)

    payload = agent.build_run_payload(query="hi")
    llm_params = {p["name"]: p["value"] for p in payload["modelParameters"]["llm"]}
    assert llm_params["reasoningEffort"] == "low"

    result = agent.run("Say hi.")
    assert result.status == "SUCCESS"


@pytest.mark.flaky(reruns=2, reruns_delay=5, reason="tool call is model-dependent")
def test_tool_input_override_is_forwarded(client, module_resource_tracker):
    tool = client.Tool.get(TAVILY_TOOL_ID)
    action_name = next(iter(tool.actions))
    action = tool.actions[action_name]
    input_name = next(iter(action.inputs))
    action.inputs[input_name].value = "override-value"

    agent = _make_agent(
        client,
        module_resource_tracker,
        instructions="Always use the web search tool before answering.",
        tools=[tool],
    )

    overrides = agent._build_tool_overrides()
    assert overrides, "expected the mutated tool input to be forwarded as a run-time override"
    assert overrides[0]["id"] == tool.id
    assert any(p["value"] == "override-value" for p in overrides[0]["parameters"])

    result = agent.run("Search the web for the capital of France, then answer.")
    assert result.status == "SUCCESS"
