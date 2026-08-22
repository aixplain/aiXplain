#!/usr/bin/env python3
"""Practical end-to-end test for the aixplain agent-builder skill.

Creates one uniquely named test agent, runs one billable query, verifies that Code
Execution fired, checks governance and output, then reloads the saved agent.
The API key is read from AIXPLAIN_API_KEY and is never printed or persisted.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from aixplain import Aixplain

CODE_EXECUTION_ID = "698cda188bbb345db14ac13b"
EXPECTED_RESULT = "338350"


def step_unit_names(steps: list | None) -> list[str]:
    names: list[str] = []
    for step in steps or []:
        if not isinstance(step, dict):
            continue
        unit = step.get("unit") or {}
        if isinstance(unit, dict) and unit.get("name"):
            names.append(str(unit["name"]))
    return names


def main() -> None:
    api_key = os.environ["AIXPLAIN_API_KEY"]
    aix = Aixplain(api_key=api_key)

    code_execution = aix.Tool.get(CODE_EXECUTION_ID)
    available_actions = list(code_execution.actions)
    assert available_actions == ["run"], available_actions
    code_execution.allowed_actions = ["run"]

    suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-UTC")
    name = f"Agent Builder Practical Test {suffix}"

    agent = aix.Agent(
        name=name,
        description="Runs a {{calculation_type}} calculation and explains the verified result.",
        instructions=(
            "For every calculation, call the Code Execution tool; never calculate only in your head. "
            "Use Python, inspect the tool result, and return the exact numeric answer, formula, and "
            "a short explanation appropriate for {{audience}}."
        ),
        tools=[code_execution],
        output_format="markdown",
        max_tokens=1200,
    )
    agent.budget.max_cost = 0.10
    agent.budget.max_duration_seconds = 120
    agent.budget.max_iterations = 8
    agent.save()

    query = (
        "Use Python to calculate the sum of the squares of every integer from 1 through 100. "
        "Return the exact result and the closed-form formula."
    )
    result = agent.run(
        query=query,
        variables={"calculation_type": "sum-of-squares", "audience": "a technical product manager"},
    )

    units = step_unit_names(result.data.steps)
    governance = result.data.governance or {}
    output = str(result.data.output or "")
    stats = result.data.execution_stats or {}

    assert any("code" in unit.lower() and "execution" in unit.lower() for unit in units), units
    assert governance.get("status", "ALLOWED") == "ALLOWED", governance
    assert EXPECTED_RESULT in output.replace(",", ""), output

    reloaded = aix.Agent.get(agent.id)
    reloaded_config = reloaded.to_dict()
    assert reloaded.id == agent.id
    assert reloaded.name == name
    assert reloaded_config.get("output_format", reloaded_config.get("outputFormat")) in {
        "markdown",
        "MARKDOWN",
    }

    report = {
        "status": "PASS",
        "agent_id": agent.id,
        "app_url": f"https://app.aixplain.com/agents/{agent.id}",
        "query": query,
        "observed_units": units,
        "governance": governance,
        "credits": stats.get("credits"),
        "runtime": stats.get("runtime"),
        "output": output,
        "round_trip": {
            "id_preserved": reloaded.id == agent.id,
            "name_preserved": reloaded.name == name,
            "output_format": reloaded_config.get("output_format", reloaded_config.get("outputFormat")),
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
