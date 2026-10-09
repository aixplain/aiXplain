"""Functional coverage for public v2 agent run-time features.

These features previously had no functional coverage (or only a unit test), so
a backend regression would have slipped through. Each test runs against the
live backend. Where the backend exposes the effect, the test asserts it: a
token that only the parameter can put in the output, a governance status, a
diagnostic code, an artifact, a step in ``result.data.steps``, or the printed
progress timeline. The wire payload is asserted wherever the behaviour is
deterministic on the SDK side.

Tests named ``*_accepted`` verify only that the backend accepts the parameter;
their docstrings say why nothing stronger is asserted.

Tests marked ``xfail(strict=True)`` check an effect the backend does not deliver
yet; each reason says what is missing. The wire payload for those features is
asserted by a separate test, or before the expected failure, so the SDK side
keeps passing or failing on its own merits, and a backend fix turns the xfail
into a strict XPASS failure that asks for the mark to be removed.

Not covered here:

- ``wait_time``, ``run_retries`` and ``run_retry_wait``: SDK-side poll and
  submission-retry controls with no observable effect on a healthy run. Unit
  tests in tests/unit/v2 cover them.
- ``execution_params.max_time``: a backend time cap. A run short enough to test
  cheaply never reaches it.
- ``evolve``: nothing in a run's response shows its effect, so a run could
  only show that the backend accepts it.
- ``progress_format="status"`` and ``progress_truncate``: only the ``logs``
  format at verbosity 3 is asserted.
- ``run_response_generation``: the agent runtime treats it as deprecated and
  ignores it. ``test_execution_params_output_format_json`` passes it, so it is
  accepted, but no effect is asserted.
- ``result.debug()``: tests/functional/v2/test_debugger.py covers it, so a
  missing Debugger meta-agent turns one leg red rather than two.
"""

import base64
import json
import re
import uuid
from typing import Any, List, Optional

import pytest

from aixplain.v2 import Inspector
from aixplain.v2.agent import AgentResponseData
from aixplain.v2.exceptions import APIError
from aixplain.v2.exceptions import TimeoutError as SDKTimeoutError

from tests.functional._helpers import unique_name

# No module-wide ``flaky`` mark: tests/functional/conftest.py already reruns any
# test whose run timed out. Only tests whose assertion depends on what the model
# chooses to say or do carry their own ``flaky`` mark, with the reason beside it.

BUDGET_BLOCKED = "BLOCKED_BY_BUDGET"
MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"

#: Tavily's single action and the optional input the tool-override test sets.
TAVILY_ACTION = "search"
TAVILY_RESULT_COUNT_INPUT = "num_results"

#: A 16x16 solid red PNG (8-bit RGB, no alpha channel, every pixel (255, 0, 0)),
#: used as a deterministic attachment payload. The previous fixture was a single
#: pixel at 50% alpha, which a vision model fairly calls "coral".
RED_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAFklEQVR42mP4z8BAEmIY1TCqYfhqAACQ+f8B8u7oVwAAAABJRU5ErkJggg=="
)

#: The agent engine reads only ``query.input``: the extra ``query`` keys that carry
#: ``variables`` and the top-level ``prompt`` are dropped, although the SDK sends
#: them in the v1-compatible shape the payload tests below assert.
ENGINE_IGNORES_RUN_TIME_INPUTS = (
    "Backend: the agent engine does not apply run-time variables / prompt (ticket to be filed)"
)

#: Instructions whose only content the model can repeat is the ``{{code}}`` variable.
VARIABLES_INSTRUCTIONS = "Reply with exactly this code and nothing else: {{code}}"


def _make_agent(client, tracker, *, instructions="You are a helpful test agent. Reply briefly.", **kwargs):
    agent = client.Agent(name=unique_name("run-params"), instructions=instructions, **kwargs)
    agent.save()
    tracker.append(agent)
    return agent


def _make_tool_agent(client, tracker, tavily_tool_id):
    tool = client.Tool.get(tavily_tool_id)
    return _make_agent(
        client,
        tracker,
        instructions="You are a research agent. Always use the web search tool before answering.",
        tools=[tool],
    )


def _output(response) -> str:
    """Return the run's output as text, whatever type the backend sent."""
    data = getattr(response, "data", None)
    if data is None:
        return ""
    output = data if isinstance(data, str) else getattr(data, "output", None)
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    if isinstance(output, (dict, list)):
        return json.dumps(output)
    return str(output)


def _response_data(result) -> AgentResponseData:
    data = result.data
    assert isinstance(data, AgentResponseData), (
        f"expected structured agent response data, got {type(data).__name__}: {data!r}"
    )
    return data


def _steps(result) -> List[dict]:
    data = result.data
    steps = None if isinstance(data, str) else getattr(data, "steps", None)
    return [step for step in steps or [] if isinstance(step, dict)]


def _is_tool_step(step: dict) -> bool:
    unit = step.get("unit")
    return isinstance(unit, dict) and str(unit.get("type") or "").lower() == "tool"


def _search_result_count(output: Any) -> Optional[int]:
    """Number of Tavily results in a tool step's output, or ``None`` if the shape is unknown."""
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except ValueError:
            return None
    if isinstance(output, dict):
        output = output.get("results")
    if isinstance(output, list):
        return len(output)
    return None


def _write_temp(tmp_path, name: str, payload: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(payload)
    return str(path)


@pytest.fixture(scope="module")
def run_agent(client, module_resource_tracker):
    return _make_agent(client, module_resource_tracker)


@pytest.fixture(scope="module")
def variables_agent(client, module_resource_tracker):
    return _make_agent(client, module_resource_tracker, instructions=VARIABLES_INSTRUCTIONS)


@pytest.fixture(scope="module")
def vision_agent(client, module_resource_tracker, assets):
    return _make_agent(client, module_resource_tracker, llm=assets.VISION_LLM)


@pytest.fixture(scope="module")
def image_agent(client, module_resource_tracker, assets):
    return _make_agent(
        client,
        module_resource_tracker,
        instructions="You generate images with the attached image tool.",
        tools=[client.Model.get(assets.SEEDREAM_MODEL)],
    )


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------


# The iteration cap only trips if the model calls the tool first.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_budget_max_iterations_halts_after_one_step(client, module_resource_tracker, assets):
    agent = _make_tool_agent(client, module_resource_tracker, assets.TAVILY)
    agent.budget.max_iterations = 1

    result = agent.run("Search the web for the capital of France, then answer.")

    assert result.status == "SUCCESS"
    assert MAX_ITERATIONS_REACHED in result.diagnostic_error_codes, (
        f"expected the run to stop on the iteration cap, got {result.diagnostic_error_codes}"
    )


def test_budget_max_cost_zero_blocks_run(client, module_resource_tracker, assets):
    agent = _make_tool_agent(client, module_resource_tracker, assets.TAVILY)
    agent.budget.max_cost = 0.0

    result = agent.run("Search the web for the capital of France, then answer.")

    governance = _response_data(result).governance
    assert governance["status"] == BUDGET_BLOCKED, f"expected a budget block, got governance={governance}"
    assert BUDGET_EXCEEDED in result.diagnostic_error_codes, (
        f"expected {BUDGET_EXCEEDED} in diagnostic codes, got {result.diagnostic_error_codes}"
    )


@pytest.mark.xfail(
    strict=True,
    raises=SDKTimeoutError,
    reason="Backend: a run with budget maxDurationSeconds=0 hangs IN_PROGRESS instead of returning BLOCKED "
    "(ticket to be filed)",
)
def test_budget_max_duration_zero_blocks_run(client, module_resource_tracker, assets):
    """A zero duration cap blocks the run.

    The payload is asserted before the run, so an SDK that stopped sending the cap
    fails here with an ``AssertionError`` rather than counting as the expected
    timeout. The run waits 60 seconds instead of the default 300: a blocked run
    answers at once, and the expected hang should not hold the leg for five minutes.
    """
    query = "Search the web for the capital of France, then answer."
    agent = _make_tool_agent(client, module_resource_tracker, assets.TAVILY)
    agent.budget.max_duration_seconds = 0
    assert agent.build_run_payload(query=query)["executionParams"]["budget"]["maxDurationSeconds"] == 0

    result = agent.run(query, timeout=60)

    governance = _response_data(result).governance
    assert governance["status"] == BUDGET_BLOCKED, f"expected a budget block, got governance={governance}"


# ---------------------------------------------------------------------------
# Context overflow
# ---------------------------------------------------------------------------


def test_context_overflow_strategy_round_trips_and_overrides(client, module_resource_tracker):
    """The saved strategy round-trips and a per-run override replaces it on the wire.

    No run is made: a short query can never overflow the context, so a run
    could not show which strategy the backend applied.
    """
    agent = _make_agent(client, module_resource_tracker)
    agent.context_overflow_strategy = "summarize"
    agent.save()

    fetched = client.Agent.get(agent.id)
    assert fetched.context_overflow_strategy == "summarize"

    assert fetched.build_run_payload(query="hi")["executionParams"]["contextOverflowStrategy"] == "summarize"

    override = fetched.build_run_payload(query="hi", execution_params={"context_overflow_strategy": "truncate"})
    assert override["executionParams"]["contextOverflowStrategy"] == "truncate"


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


def test_progress_logs_format_prints_step_timeline_at_full_verbosity(run_agent, capsys):
    """``progress_format="logs"`` prints the step timeline; verbosity 3 adds each step's I/O.

    Off a terminal (pytest's capture) the status format prints only the
    completion summary. A newline-terminated completed-step line therefore
    comes from the logs format, and a ``  → <label>`` detail line comes only
    from verbosity 3.
    """
    result = run_agent.run(
        "Say hi.",
        progress_format="logs",
        progress_verbosity=3,
        progress_truncate=False,
    )

    captured = capsys.readouterr().out
    assert result.status == "SUCCESS"
    assert re.search(r"[✓✗] Step\s+\d+ · [^\n]*\n", captured), (
        f"expected a newline-terminated completed step line (logs format), got {captured!r}"
    )
    assert re.search(r"^  → \S", captured, re.MULTILINE), (
        f"expected a step output detail line (verbosity 3), got {captured!r}"
    )
    assert re.search(r"✓ Completed \d+ steps", captured), f"expected the completion summary, got {captured!r}"


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


# The artifact exists only if the model calls the image tool.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
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
# Variables / prompt / criteria / identifier / history / tasks / inspectors
# ---------------------------------------------------------------------------


def test_variables_are_sent_as_query_keys(variables_agent):
    """``variables`` travel as extra keys of ``query`` beside ``input`` (the v1 contract).

    The placeholder lives in the instructions because that is where the backend
    substitutes: save rewrites ``{{code}}`` to ``{code}``.
    """
    token = f"tok{uuid.uuid4().hex[:10]}"

    payload = variables_agent.build_run_payload(query="Reply now.", variables={"code": token})

    assert payload["query"]["input"] == "Reply now."
    assert payload["query"]["code"] == token


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=ENGINE_IGNORES_RUN_TIME_INPUTS)
def test_variables_are_substituted_into_instructions(variables_agent):
    """A ``{{code}}`` placeholder in the instructions is filled from ``variables``.

    The token is random and neutral -- an earlier "secret word" wording made the
    model answer with the literal word ``word`` -- so only the substitution can put
    it in the output. Only that output check is expected to fail: a run that is
    refused raises ``APIError`` and a non-success status calls ``pytest.fail``,
    neither of which the xfail accepts. The payload is asserted by
    ``test_variables_are_sent_as_query_keys``.
    """
    token = f"tok{uuid.uuid4().hex[:10]}"

    result = variables_agent.run("Reply now.", variables={"code": token})
    if result.status != "SUCCESS":
        pytest.fail(f"the run itself failed with status {result.status}: {result.data!r}")

    assert token in _output(result).lower(), f"expected the substituted token {token!r}, got {result.data!r}"


def test_prompt_criteria_and_identifier_are_sent_top_level(run_agent):
    """``prompt``, ``criteria`` and ``identifier`` are top-level payload keys (the v1 contract)."""
    prompt = "Reply with exactly this code and nothing else: tok0123456789"
    identifier = unique_name("identifier")

    payload = run_agent.build_run_payload(
        query="Reply now.", prompt=prompt, criteria="The answer must be a single word.", identifier=identifier
    )

    assert payload["query"] == {"input": "Reply now."}
    assert payload["prompt"] == prompt
    assert payload["criteria"] == "The answer must be a single word."
    assert payload["identifier"] == identifier


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=ENGINE_IGNORES_RUN_TIME_INPUTS)
def test_prompt_override_reaches_model(run_agent):
    """``prompt`` reaches the model: the random token exists only in the prompt.

    The instruction is deliberately neutral: an earlier "the secret is ..." wording
    made the model refuse to share secrets. ``criteria`` and ``identifier`` ride
    along, so the backend still has to accept them: a refused run raises
    ``APIError``, which the xfail does not cover. Only the output check is expected
    to fail; the payload is asserted by
    ``test_prompt_criteria_and_identifier_are_sent_top_level``.
    """
    token = f"tok{uuid.uuid4().hex[:10]}"
    result = run_agent.run(
        "Reply now.",
        prompt=f"Reply with exactly this code and nothing else: {token}",
        criteria="The answer must be a single word.",
        identifier=unique_name("identifier"),
    )
    if result.status != "SUCCESS":
        pytest.fail(f"the run itself failed with status {result.status}: {result.data!r}")

    assert token in _output(result).lower(), f"expected the token {token!r} from the prompt, got {result.data!r}"


# The model has to recall the name from the supplied history.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_history_is_used(run_agent):
    result = run_agent.run(
        "What did I say my name was?",
        history=[
            {"role": "user", "content": "My name is Sam."},
            {"role": "assistant", "content": "Hi Sam."},
        ],
    )

    assert result.status == "SUCCESS"
    assert re.search(r"\bsam\b", _output(result), re.IGNORECASE), f"expected the name from history, got {result.data!r}"


def test_tasks_are_accepted(run_agent):
    """``tasks`` is sent as given and the backend accepts it.

    Only acceptance is verified: a single agent's response exposes no field
    showing which task, if any, it worked on.
    """
    tasks = [{"name": "t1", "description": "Say hi.", "expectedOutput": "A greeting."}]

    assert run_agent.build_run_payload(query="Say hi.", tasks=tasks)["tasks"] == tasks

    assert run_agent.run("Say hi.", tasks=tasks).status == "SUCCESS"


def test_run_time_inspector_accepted(run_agent, assets):
    """A run-time ``inspectors`` list is sent as given and the backend accepts it.

    Only acceptance is verified: in the first live CI run the response's steps held
    only the agent's own LLM step, nothing for the run-time inspector, so nothing the
    response exposes shows the inspector ran. The action is ``continue`` and the judge
    is told to always pass, so the inspector cannot abort the run whatever its verdict.
    """
    inspector = Inspector(
        name=unique_name("RunTimeInspector"),
        targets=["input"],
        action="continue",
        metric={"asset_id": assets.DEFAULT_LLM, "prompt": "Always answer PASS, whatever the content."},
    ).to_dict()

    assert run_agent.build_run_payload(query="Say hi.", inspectors=[inspector])["inspectors"] == [inspector]

    assert run_agent.run("Say hi.", inspectors=[inspector]).status == "SUCCESS"


# ---------------------------------------------------------------------------
# Run control: timeout
# ---------------------------------------------------------------------------


def test_timeout_zero_raises_before_first_poll(run_agent):
    """``timeout`` bounds the SDK's wait for an accepted run.

    Agent runs are asynchronous: the submission returns a poll URL, and
    ``sync_poll`` checks the remaining budget before its first poll, so
    ``timeout=0`` raises deterministically. The run itself carries on on the
    backend.
    """
    with pytest.raises(SDKTimeoutError, match=r"timed out after 0 seconds"):
        run_agent.run("Say hi.", timeout=0)


# ---------------------------------------------------------------------------
# execution_params
# ---------------------------------------------------------------------------


def test_execution_params_max_tokens_is_honoured(run_agent):
    """``max_tokens=1`` makes an otherwise healthy run fail.

    The backend's error text for this is generic (no token wording, see
    test_snake_case_e2e.py), so instead of matching the message the test checks
    that the failure is a business ``FAILED`` run outcome rather than a 401, a
    5xx or a polling error, and that the same run succeeds without the cap.
    """
    control = run_agent.run("Say hi.", execution_params={"output_format": "text"})
    assert control.status == "SUCCESS", f"control run without max_tokens failed: {control.status}"

    with pytest.raises(APIError) as excinfo:
        run_agent.run("Say hi.", execution_params={"max_tokens": 1, "output_format": "text"})

    error = excinfo.value
    assert error.retryable is False and error.response_data.get("status") == "FAILED", (
        f"expected a FAILED run outcome, got status_code={error.status_code} "
        f"retryable={error.retryable} response_data={error.response_data!r}"
    )
    assert str(error).startswith("Operation failed"), f"unexpected error: {error}"


# The model has to produce valid JSON with the expected key.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
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


# The vision model has to name the colour.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_attachments_send_image_to_vision_model(vision_agent, tmp_path):
    path = _write_temp(tmp_path, "red.png", RED_PNG_BYTES)

    result = vision_agent.run("What is the color of the attached image? Answer with one word.", attachments=[path])

    assert result.status == "SUCCESS"
    assert re.search(r"\bred", _output(result), re.IGNORECASE), f"expected the image colour, got {result.data!r}"


# The model has to read the code back from the file. A plain-text file needs no
# vision model, so this runs on the default LLM: tying it to VISION_LLM turned the
# leg red whenever that model was unavailable, although the alias itself worked.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_deprecated_files_alias_uploads_and_reads(run_agent, tmp_path):
    token = f"CODE-{uuid.uuid4().hex[:8].upper()}"
    path = _write_temp(tmp_path, "note.txt", f"The magic code is {token}.".encode())

    result = run_agent.run("Read the attached file and reply with only the magic code.", files=[path])

    assert result.status == "SUCCESS"
    assert token.lower() in _output(result).lower(), f"expected {token} from the file, got {result.data!r}"


# ---------------------------------------------------------------------------
# Session memory
# ---------------------------------------------------------------------------


# The model has to recall the codeword within the session.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_session_recalls_and_stateless_forgets(client, module_resource_tracker):
    """One agent recalls a codeword inside a session and not in a run without one.

    Using the same agent for both means the session is the only difference.
    The codeword is random, so the model cannot produce it without memory.
    """
    codeword = f"PLUM-{uuid.uuid4().hex[:6].upper()}"
    agent = _make_agent(client, module_resource_tracker)
    session = client.Session(agent=agent, name=unique_name("memory"))
    session.save()
    module_resource_tracker.append(session)

    agent.run(f"Remember the codeword {codeword}. Reply OK.", session=session)
    recalled = agent.run("What is the codeword? Reply only the codeword.", session=session)
    assert codeword in _output(recalled).upper(), f"session did not recall {codeword}: {recalled.data!r}"

    forgotten = agent.run("What is the codeword? Reply only the codeword.")
    assert codeword not in _output(forgotten).upper(), (
        f"a run without the session should not know {codeword}: {forgotten.data!r}"
    )


# ---------------------------------------------------------------------------
# reasoning_effort / tool param overrides
# ---------------------------------------------------------------------------


def test_reasoning_effort_payload_and_run_accepted(client, module_resource_tracker, assets):
    """``reasoning_effort`` lands in ``modelParameters`` and the backend accepts the run.

    Only acceptance is verified. No response field reports the effort level
    applied. The run-time path is not isolated either: ``save()`` also persists
    the value, and changing the LLM's inputs after saving marks an onboarded
    agent as modified, so ``run()`` refuses it.
    """
    # The suite's default LLM (GPT-5.4) exposes a ``reasoning_effort`` input.
    llm = client.Model.get(assets.DEFAULT_LLM)
    llm.inputs.reasoning_effort = "low"

    agent = _make_agent(client, module_resource_tracker, llm=llm)

    payload = agent.build_run_payload(query="hi")
    llm_params = {p["name"]: p["value"] for p in payload["modelParameters"]["llm"]}
    assert llm_params["reasoningEffort"] == "low"

    result = agent.run("Say hi.")
    assert result.status == "SUCCESS"


# The tool step exists only if the model calls the search tool.
@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_tool_input_override_applies_at_run_time_only(client, module_resource_tracker, assets):
    """A tool input changed after ``save()`` is sent with the run and not persisted.

    The SDK does not pin the shape of a tool step's output. When it carries a
    Tavily ``results`` list, the test also asserts that the override capped it
    at one result. Otherwise the wire payload and the non-persistence are what
    is asserted.
    """
    override = 1
    agent = _make_tool_agent(client, module_resource_tracker, assets.TAVILY)

    tool = agent.tools[0]
    search = tool.actions[TAVILY_ACTION]
    saved_value = search.inputs[TAVILY_RESULT_COUNT_INPUT].value
    assert str(saved_value) != str(override), (
        f"precondition: the override must differ from the saved {TAVILY_RESULT_COUNT_INPUT}={saved_value!r}"
    )
    search.inputs[TAVILY_RESULT_COUNT_INPUT] = override
    assert not agent.is_modified, "a tool input override must not mark the saved agent as modified"

    payload = agent.build_run_payload(query="hi")
    tool_entry = next((entry for entry in payload.get("tools", []) if entry["id"] == tool.id), None)
    assert tool_entry is not None, f"expected a run-time override for tool {tool.id}, got {payload.get('tools')}"
    assert {"name": TAVILY_RESULT_COUNT_INPUT, "value": override} in tool_entry["parameters"]

    result = agent.run("Search the web for the capital of France, then answer.")
    assert result.status == "SUCCESS"

    tool_steps = [step for step in _steps(result) if _is_tool_step(step)]
    assert tool_steps, f"expected the search tool to run, got steps {_steps(result)!r}"
    counts = [count for count in (_search_result_count(step.get("output")) for step in tool_steps) if count is not None]
    assert all(count <= override for count in counts), (
        f"expected at most {override} search result(s) per call with the override, got {counts}"
    )

    fetched = client.Agent.get(agent.id)
    persisted = fetched.tools[0].actions[TAVILY_ACTION].inputs[TAVILY_RESULT_COUNT_INPUT].value
    assert str(persisted) != str(override), (
        f"the run-time override was persisted: saved {TAVILY_RESULT_COUNT_INPUT}={persisted!r}"
    )
