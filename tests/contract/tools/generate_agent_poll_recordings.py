"""Generate the agent poll recordings from the agents service's own code (ENG-3782).

``GET sdk/agents/{id}/result`` on platform-backend proxies the agents
service's ``GET /agents/checkRequest/{id}`` and returns its body inside
``AgentResultDto`` ({completed, status, data, artifacts?, progress?}), after
multiplying every credit field by 1.2 (agent overhead). Rather than typing that
body by hand, this script builds it with the agents service's real
``ResponseAdapter`` and ``to_legacy_response``, exactly as the route does, and
applies platform-backend's transformation on top.

Run it with an aixplain-agents checkout's interpreter (it imports
``aixplain_agents``), from this repo's root:

    /path/to/aixplain-agents/.venv/bin/python tests/contract/tools/generate_agent_poll_recordings.py \
        --agents-repo /path/to/aixplain-agents

Sources (re-check when either side changes):
    aixplain-agents  aixplain_agents/api/routes/agents.py check_request (completed branch)
    platform-backend src/agent/services/agent.run.service.ts result(); src/agent/utils/agent-credits.util.ts
                     withAgentOverheadResult; src/agent/dto/agent.dto.ts AgentResultDto
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "recordings" / "backend"
OVERHEAD = 1.2
CREDIT_KEYS = ("usedCredits", "used_credits", "credits")


def _gross_up(node):
    """platform-backend withAgentOverheadResult: x1.2 on the envelope, data, and their execution stats."""
    if not isinstance(node, dict):
        return node
    out = dict(node)
    for key in CREDIT_KEYS:
        if isinstance(out.get(key), (int, float)):
            out[key] = round(out[key] * OVERHEAD, 10)
    for stats in ("executionStats", "execution_stats"):
        if isinstance(out.get(stats), dict):
            out[stats] = _gross_up(out[stats])
    return out


def _poll_body(result):
    """aixplain-agents check_request, completed branch, then platform-backend's AgentResultDto."""
    from aixplain_agents.adapter.response_adapter import to_legacy_response

    result = dict(result)
    status = result.pop("status", "SUCCESS")
    agents_response = {"completed": True, "status": status, "data": to_legacy_response(result)}
    data = _gross_up(agents_response["data"])
    return _gross_up({"completed": True, "status": status, "data": data})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents-repo", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.agents_repo))

    from aixplain_agents.adapter.context import ExecutionContext
    from aixplain_agents.adapter.response_adapter import ResponseAdapter
    from aixplain_agents.core.result import AgentResult
    from aixplain_agents.core.usage import UsageInfo

    commit = subprocess.run(
        ["git", "-C", str(args.agents_repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    request = {
        "query": "What is the capital of France?",
        "session_id": "sess-contract-1",
        "request_id": "req-contract-agent-1",
        "agent": {"id": "agent-contract-1", "name": "Contract Agent"},
    }
    steps = [
        {
            "agent": {"id": "agent-contract-1", "name": "Contract Agent"},
            "unit": {"type": "llm", "name": "GPT-4o Mini"},
            "input": "What is the capital of France?",
            "output": "Paris.",
            "status": "SUCCESS",
            "used_credits": 0.01,
            "run_time": 1.2,
        }
    ]
    success = ResponseAdapter().adapt(
        AgentResult(
            output="Paris.",
            messages=[],
            usage=UsageInfo(prompt_tokens=10, completion_tokens=2),
            session_id="sess-contract-1",
            metadata={"progress_steps": steps},
        ),
        request,
        ExecutionContext(elapsed_seconds=1.5, total_credits=0.0125, request_id="req-contract-agent-1"),
    )
    # A run that succeeds with a non-fatal diagnostic: the answer was cut at
    # the model's token limit. SDK #983 read these codes from the top level.
    truncated = ResponseAdapter().adapt(
        AgentResult(
            output="Paris is the capital of France and its largest",
            messages=[],
            usage=UsageInfo(prompt_tokens=10, completion_tokens=16),
            session_id="sess-contract-1",
            metadata={"progress_steps": steps, "diagnostic_error_codes": ["MAX_TOKENS_REACHED"]},
        ),
        request,
        ExecutionContext(elapsed_seconds=1.5, total_credits=0.0125, request_id="req-contract-agent-1"),
    )
    failure = ResponseAdapter().adapt_error(
        RuntimeError("The model 'aixplain/6646261c6eb563165658bbb1' is currently unavailable or unreachable."),
        request,
        ExecutionContext(elapsed_seconds=0.4, request_id="req-contract-agent-1"),
    )
    provenance = {
        "source": "generated",
        "recorded_at": None,
        "backend": None,
        "derived_from": [
            f"aixplain-agents@{commit} ResponseAdapter + to_legacy_response, as api/routes/agents.py check_request returns it",
            "platform-backend@91ed4d7bf agent.run.service.ts result() -> withAgentOverheadResult (x1.2) -> AgentResultDto",
        ],
        "note": "Generated by tests/contract/tools/generate_agent_poll_recordings.py; re-run when either side changes.",
    }
    for name, result, what in (
        ("agent-poll-success", success, "successful run"),
        ("agent-poll-success-truncated", truncated, "successful run cut at the token limit (MAX_TOKENS_REACHED)"),
        ("agent-poll-failed", failure, "failed run"),
    ):
        recording = {
            "contract": f"Agent run poll (GET sdk/agents/{{request_id}}/result), {what}.",
            "endpoint": {"method": "GET", "host": "backend", "path": "/sdk/agents/{request_id}/result"},
            "request": {},
            "response": {"status": 200, "headers": {"Content-Type": "application/json"}, "json": _poll_body(result)},
            "provenance": provenance,
        }
        (OUT / f"{name}.json").write_text(json.dumps(recording, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", OUT / f"{name}.json")


if __name__ == "__main__":
    main()
