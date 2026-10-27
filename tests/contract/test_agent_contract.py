"""Agent definition, run and poll against platform-shaped responses (ENG-3782, layer 1).

The poll recordings are generated from the agents service's own code
(``tools/generate_agent_poll_recordings.py``): platform-backend returns the
agents service's ``checkRequest`` body verbatim inside ``AgentResultDto``, with
credits grossed up by 1.2. That body is camelCase only at its top level
(``to_legacy_response``); ``session_id`` and everything inside
``executionStats`` stay snake_case. SDK #983 was a nested field the SDK read
from the wrong place, tested against a body typed by hand.
"""

import pytest

from tests.support.platform_replay import BACKEND_URL, PlatformStub, load_recording

AGENT_ID = "agent-contract-1"


def _serve_run(platform: PlatformStub, poll: str) -> None:
    platform.serve("backend/agent-detail")
    platform.serve("backend/agent-run-submit")
    platform.serve("backend/agent-poll-in-progress", then=[poll])


def test_agent_definition_hydrates_its_tools_and_files(aix, platform: PlatformStub) -> None:
    platform.serve("backend/agent-detail")

    agent = aix.Agent.get(AGENT_ID)

    assert agent.name == "Contract Agent"
    assert agent.instructions == "You answer geography questions."
    assert [getattr(t, "id", None) or t.get("id") for t in agent.tools] == ["66f423426eb563fa213a3531"]
    # #1142: agent.files entries become File objects, like agent.tools.
    assert [f.id for f in agent.files] == ["file-contract-1"]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding: GET /v2/agents/:id returns the LLM as model: {id, name, parameters}; the SDK "
        "hydrates Agent.llm as that dict, and the public Agent.llm_id property accepts only a str or a "
        "Model, so it raises TypeError on every agent fetched from the platform."
    ),
)
def test_fetched_agent_reports_its_llm_id(aix, platform: PlatformStub) -> None:
    platform.serve("backend/agent-detail")

    assert aix.Agent.get(AGENT_ID).llm_id == "6646261c6eb563165658bbb1"


def test_successful_run_is_polled_to_its_answer(aix, platform: PlatformStub) -> None:
    _serve_run(platform, "backend/agent-poll-success")

    result = aix.Agent.get(AGENT_ID).run("What is the capital of France?", show_progress=False)

    assert result.status == "SUCCESS"
    assert result.completed is True
    assert result.data.output == "Paris."
    assert result.request_id == "req-contract-agent-1" or result.execution_id == "req-contract-agent-1"
    # platform-backend multiplies the agents service's credits by 1.2.
    assert result.used_credits == pytest.approx(0.0125 * 1.2)
    assert result.run_time == pytest.approx(1.5)
    polls = platform.sent("GET", "/sdk/agents/req-contract-agent-1/result")
    assert len(polls) == 2 and all(p.url.startswith(BACKEND_URL) for p in polls)
    assert len(platform.sent("POST", "/run")) == 1


def test_truncated_run_reports_its_diagnostic_code(aix, platform: PlatformStub) -> None:
    # #983: the agents service nests non-fatal codes under data (and its
    # executionStats), never at the top level of the poll body.
    _serve_run(platform, "backend/agent-poll-success-truncated")

    result = aix.Agent.get(AGENT_ID).run("What is the capital of France?", show_progress=False)

    assert result.status == "SUCCESS"
    assert result.diagnostic_error_codes == ["MAX_TOKENS_REACHED"]


def test_successful_run_exposes_its_session_and_steps(aix, platform: PlatformStub) -> None:
    _serve_run(platform, "backend/agent-poll-success")

    result = aix.Agent.get(AGENT_ID).run("What is the capital of France?", show_progress=False)

    assert result.data.session_id == "sess-contract-1"
    assert len(result.data.steps) == 1


def test_failed_run_carries_its_error_and_diagnostic_codes(aix, platform: PlatformStub) -> None:
    _serve_run(platform, "backend/agent-poll-failed")

    from aixplain.v2.exceptions import APIError

    expected = load_recording("backend/agent-poll-failed")["response"]["json"]["data"]

    with pytest.raises(APIError) as raised:
        aix.Agent.get(AGENT_ID).run("What is the capital of France?", show_progress=False)

    # The agents service's classified message reaches the caller, and the body
    # (with its diagnostic codes) stays inspectable on the error.
    assert expected["errorDetails"]["message"] in str(raised.value)
    assert raised.value.response_data["data"]["diagnosticErrorCodes"] == expected["diagnosticErrorCodes"]
    # A FAILED poll is a business outcome: raised, never resubmitted (SDK BUG-1090).
    assert len(platform.sent("POST", "/run")) == 1


@pytest.mark.parametrize(
    ("recording", "status", "message"),
    [
        ("backend/error-not-enough-balance", 471, "err.not_enough_balance"),
        # An object body with no statusCode key: the HTTP status must still come through.
        ("backend/error-agent-quota", 429, "err.agent_quota_exceeded"),
    ],
)
def test_refused_agent_run_raises_with_the_platform_code(
    aix, platform: PlatformStub, recording: str, status: int, message: str
) -> None:
    from aixplain.v2.exceptions import APIError

    platform.serve("backend/agent-detail").serve(recording)

    with pytest.raises(APIError) as raised:
        aix.Agent.get(AGENT_ID).run("hi", show_progress=False)

    assert raised.value.status_code == status and message in str(raised.value)
    assert len(platform.sent("POST", "/run")) == 1
