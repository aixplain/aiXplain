#!/usr/bin/env python3
"""Build and test one agent for each stable SDK v2 execution strategy."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from aixplain import Aixplain
from aixplain.v2.agent import Task


GPT_5_4_ID = "69b7e5f1b2fe44704ab0e7d0"
CODE_EXECUTION_ID = "698cda188bbb345db14ac13b"
EXPECTED_RESULT = "2870"


def configured_model(aix: Aixplain, effort: str):
    model = aix.Model.get(GPT_5_4_ID)
    if "reasoning_effort" not in model.inputs.keys():
        raise RuntimeError(f"Model {model.id} does not support reasoning_effort")
    model.inputs.reasoning_effort = effort
    return model


def step_unit_names(steps: list | None) -> list[str]:
    names: list[str] = []
    for step in steps or []:
        if not isinstance(step, dict):
            continue
        unit = step.get("unit") or {}
        if isinstance(unit, dict) and unit.get("name"):
            names.append(str(unit["name"]))
    return names


def apply_budget(agent) -> None:
    agent.budget.max_cost = 0.15
    agent.budget.max_duration_seconds = 120
    agent.budget.max_iterations = 15


def run_and_report(aix: Aixplain, agent, strategy: str) -> dict[str, Any]:
    raw = aix.Agent.context.client.get(f"v2/agents/{agent.id}")
    raw_tasks = raw.get("tasks") or []
    raw_planner = raw.get("planner")

    if strategy == "adaptive":
        assert not raw_tasks and not raw_planner, {"tasks": raw_tasks, "planner": raw_planner}
    elif strategy == "static_tasks":
        assert len(raw_tasks) == 3 and not raw_planner, {
            "tasks": raw_tasks,
            "planner": raw_planner,
        }
    elif strategy == "planner":
        assert not raw_tasks and isinstance(raw_planner, dict) and raw_planner.get("id"), {
            "tasks": raw_tasks,
            "planner": raw_planner,
        }

    prompt = (
        "Use Code Execution to calculate the sum of the squares of every integer from 1 through 20. "
        "Verify the result with a second method and explain it concisely."
    )
    result = agent.run(query=prompt)
    output = str(result.data.output or "")
    governance = result.data.governance or {}
    stats = result.data.execution_stats or {}
    units = step_unit_names(result.data.steps)

    assert EXPECTED_RESULT in output.replace(",", ""), output
    assert governance.get("status", "ALLOWED") == "ALLOWED", governance
    code_execution_used = "Code Execution" in units

    return {
        "strategy": strategy,
        "agent_id": agent.id,
        "app_url": f"https://app.aixplain.com/agents/{agent.id}",
        "persisted_tasks": len(raw_tasks),
        "persisted_planner": raw_planner,
        "observed_units": units,
        "code_execution_used": code_execution_used,
        "governance": governance,
        "credits": stats.get("credits"),
        "runtime": stats.get("runtime"),
        "output": output,
        "pass_fail": "PASS",
    }


def latest_agent(aix: Aixplain, prefix: str):
    for page_number in range(5):
        page = aix.Agent.search(page_number=page_number, page_size=100)
        matches = [
            item
            for item in page.results
            if str(getattr(item, "name", "")).startswith(prefix)
        ]
        if matches:
            return aix.Agent.get(matches[0].id)
        if not page.results:
            break
    raise RuntimeError(f"No existing agent found with prefix {prefix!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-latest", action="store_true")
    args = parser.parse_args()

    aix = Aixplain()
    if args.resume_latest:
        adaptive = latest_agent(aix, "Adaptive Execution Test")
        static = latest_agent(aix, "Static Task Execution Test")
        planned = latest_agent(aix, "Planner Execution Test")
    else:
        suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-UTC")
        code_execution = aix.Tool.get(CODE_EXECUTION_ID)
        code_execution.allowed_actions = ["run"]

        common_instructions = (
            "Always use Code Execution for the calculation and verification. Inspect the tool result, "
            "state the exact result, and explain both verification methods."
        )

        adaptive = aix.Agent(
            name=f"Adaptive Execution Test {suffix}",
            description="Chooses calculation and verification steps adaptively from observations.",
            instructions=common_instructions,
            llm=configured_model(aix, "medium"),
            tools=[code_execution],
            output_format="markdown",
        )
        apply_budget(adaptive)
        adaptive.save()

        calculate = Task(
            name="calculate",
            instructions="Use Code Execution to calculate the requested series exactly.",
            expected_output="Exact numeric result and calculation trace",
        )
        verify = Task(
            name="verify",
            instructions="Use Code Execution to verify the result with an independent formula.",
            expected_output="Independent verification and match status",
            dependencies=[calculate],
        )
        explain = Task(
            name="explain",
            instructions="Present the verified result and both methods concisely.",
            expected_output="Concise verified markdown answer",
            dependencies=[verify],
        )
        static = aix.Agent(
            name=f"Static Task Execution Test {suffix}",
            description="Runs a fixed calculate, verify, and explain task graph.",
            instructions=common_instructions,
            llm=configured_model(aix, "medium"),
            tools=[code_execution],
            tasks=[calculate, verify, explain],
            output_format="markdown",
        )
        apply_budget(static)
        static.save()

        planned = aix.Agent(
            name=f"Planner Execution Test {suffix}",
            description="Uses a planning model to generate and execute a task graph.",
            instructions=common_instructions,
            llm=configured_model(aix, "medium"),
            planner=configured_model(aix, "high"),
            tools=[code_execution],
            output_format="markdown",
        )
        apply_budget(planned)
        planned.save()

    reports = [
        run_and_report(aix, adaptive, "adaptive"),
        run_and_report(aix, static, "static_tasks"),
        run_and_report(aix, planned, "planner"),
    ]
    print(
        json.dumps(
            {
                "status": "PASS",
                "expected_result": EXPECTED_RESULT,
                "agents": reports,
                "total_credits": sum(float(item["credits"] or 0) for item in reports),
                "total_runtime": sum(float(item["runtime"] or 0) for item in reports),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
