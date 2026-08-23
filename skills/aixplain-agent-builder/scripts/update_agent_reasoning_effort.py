#!/usr/bin/env python3
"""Update an agent LLM's reasoning effort without widening tool scopes."""

from __future__ import annotations

import argparse
import json
from typing import Any

from aixplain import Aixplain


def role_id(role: Any) -> str:
    if isinstance(role, str):
        return role
    if isinstance(role, dict) and role.get("id"):
        return str(role["id"])
    value = getattr(role, "id", None)
    if value:
        return str(value)
    raise RuntimeError(f"Agent LLM has no model ID: {role!r}")


def parameter_map(role: Any) -> dict[str, Any]:
    parameters = role.get("parameters", {}) if isinstance(role, dict) else {}
    if isinstance(parameters, dict):
        return parameters
    if isinstance(parameters, list):
        return {
            item["name"]: item.get("value")
            for item in parameters
            if isinstance(item, dict) and item.get("name")
        }
    return {}


def scope_map(raw_agent: dict[str, Any]) -> dict[str, list[str]]:
    return {
        item["id"]: list(item.get("actions") or [])
        for item in (raw_agent.get("tools") or [])
        if isinstance(item, dict) and item.get("id")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_id")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--description")
    args = parser.parse_args()

    aix = Aixplain()
    raw_before = aix.Agent.context.client.get(f"v2/agents/{args.agent_id}")
    expected_scopes = scope_map(raw_before)
    agent = aix.Agent.get(args.agent_id)

    if args.verify_only:
        raw_parameters = parameter_map(raw_before.get("model") or {})
        sdk_parameters = parameter_map(agent.llm)
        raw_effort = raw_parameters.get(
            "reasoningEffort", raw_parameters.get("reasoning_effort")
        )
        sdk_effort = sdk_parameters.get(
            "reasoningEffort", sdk_parameters.get("reasoning_effort")
        )
        assert raw_effort == args.effort, raw_parameters
        assert sdk_effort == args.effort, sdk_parameters
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "verification": "READ_ONLY",
                    "save_performed": False,
                    "agent_id": args.agent_id,
                    "model_id": role_id(agent.llm),
                    "raw_backend_reasoning_effort": raw_effort,
                    "agent_get_reasoning_effort": sdk_effort,
                    "raw_tool_scopes": expected_scopes,
                },
                indent=2,
            )
        )
        return

    for tool in agent.tools or []:
        if getattr(tool, "id", None) in expected_scopes:
            tool.allowed_actions = expected_scopes[tool.id]

    if args.description is not None:
        original_model_id = role_id(agent.llm)
        agent.description = args.description
        agent.save()

        raw_after = aix.Agent.context.client.get(f"v2/agents/{args.agent_id}")
        reloaded = aix.Agent.get(args.agent_id)
        persisted_parameters = parameter_map(raw_after.get("model") or {})
        persisted_effort = persisted_parameters.get(
            "reasoningEffort", persisted_parameters.get("reasoning_effort")
        )
        assert raw_after.get("description") == args.description, raw_after.get("description")
        assert reloaded.description == args.description, reloaded.description
        assert role_id(reloaded.llm) == original_model_id, reloaded.llm
        assert persisted_effort == args.effort, persisted_parameters
        assert scope_map(raw_after) == expected_scopes, {
            "before": expected_scopes,
            "after": scope_map(raw_after),
        }
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "agent_id": args.agent_id,
                    "description": reloaded.description,
                    "description_persisted": True,
                    "model_id": original_model_id,
                    "reasoning_effort_after_save": persisted_effort,
                    "tool_scopes_preserved": True,
                },
                indent=2,
            )
        )
        return

    model = aix.Model.get(role_id(agent.llm))
    input_keys = list(model.inputs.keys()) if model.inputs is not None else []
    if "reasoning_effort" not in input_keys:
        raise RuntimeError(
            f"Model {model.id} ({model.name}) does not support reasoning_effort; "
            f"available inputs: {input_keys}"
        )

    model.inputs.reasoning_effort = args.effort
    agent.llm = model
    agent.save()

    raw_after = aix.Agent.context.client.get(f"v2/agents/{args.agent_id}")
    reloaded = aix.Agent.get(args.agent_id)
    persisted_parameters = parameter_map(raw_after.get("model") or {})
    reloaded_parameters = parameter_map(reloaded.llm)
    persisted_effort = persisted_parameters.get(
        "reasoningEffort", persisted_parameters.get("reasoning_effort")
    )
    reloaded_effort = reloaded_parameters.get(
        "reasoningEffort", reloaded_parameters.get("reasoning_effort")
    )

    assert persisted_effort == args.effort, persisted_parameters
    assert reloaded_effort == args.effort, reloaded_parameters
    assert scope_map(raw_after) == expected_scopes, {
        "before": expected_scopes,
        "after": scope_map(raw_after),
    }

    print(
        json.dumps(
            {
                "status": "PASS",
                "agent_id": args.agent_id,
                "model_id": model.id,
                "model_name": model.name,
                "reasoning_effort": persisted_effort,
                "reloaded_reasoning_effort": reloaded_effort,
                "tool_scopes_preserved": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
