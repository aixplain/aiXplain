#!/usr/bin/env python3
"""Attach an authorized Slack tool to an agent and verify persistence."""

from __future__ import annotations

import argparse
import json
from typing import Any

from aixplain import Aixplain


SLACK_ACTIONS = [
    "SLACK_FIND_CHANNELS",
    "SLACK_FETCH_CONVERSATION_HISTORY",
    "SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION",
    "SLACK_CHAT_POST_MESSAGE",
]


def scope_map(raw_agent: dict[str, Any]) -> dict[str, list[str]]:
    return {
        item["id"]: list(item.get("actions") or [])
        for item in (raw_agent.get("tools") or [])
        if isinstance(item, dict) and item.get("id")
    }


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


def role_map(raw_agent: dict[str, Any]) -> dict[str, Any]:
    roles = {
        "llm": raw_agent.get("model"),
        "planner": raw_agent.get("planner"),
        "supervisor": raw_agent.get("supervisor"),
        "response_generator": raw_agent.get("responder"),
    }
    return {
        name: (
            {
                "id": value.get("id"),
                "parameters": parameter_map(value),
            }
            if isinstance(value, dict) and value.get("id")
            else None
        )
        for name, value in roles.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_id")
    parser.add_argument("slack_tool_id")
    parser.add_argument("--expected-effort", default="medium")
    args = parser.parse_args()

    aix = Aixplain()
    raw_before = aix.Agent.context.client.get(f"v2/agents/{args.agent_id}")
    expected_scopes = scope_map(raw_before)
    expected_roles = role_map(raw_before)
    agent = aix.Agent.get(args.agent_id)

    for tool in agent.tools or []:
        tool_id = getattr(tool, "id", None)
        if tool_id in expected_scopes:
            tool.allowed_actions = expected_scopes[tool_id]

    slack = aix.Tool.get(args.slack_tool_id)
    slack.allowed_actions = list(SLACK_ACTIONS)
    tools = list(agent.tools or [])
    if not any(getattr(tool, "id", None) == slack.id for tool in tools):
        tools.append(slack)
    agent.tools = tools
    agent.save()

    expected_scopes[slack.id] = list(SLACK_ACTIONS)
    raw_after = aix.Agent.context.client.get(f"v2/agents/{args.agent_id}")
    reloaded = aix.Agent.get(args.agent_id)
    actual_scopes = scope_map(raw_after)
    actual_roles = role_map(raw_after)
    model_parameters = parameter_map(raw_after.get("model") or {})
    reasoning_effort = model_parameters.get(
        "reasoningEffort", model_parameters.get("reasoning_effort")
    )

    assert actual_scopes == expected_scopes, {
        "expected": expected_scopes,
        "actual": actual_scopes,
    }
    assert actual_roles == expected_roles, {
        "expected": expected_roles,
        "actual": actual_roles,
    }
    assert reasoning_effort == args.expected_effort, model_parameters
    assert any(getattr(tool, "id", None) == slack.id for tool in reloaded.tools or [])

    print(
        json.dumps(
            {
                "status": "PASS",
                "agent_id": args.agent_id,
                "slack_tool_id": slack.id,
                "slack_tool_name": slack.name,
                "slack_actions": actual_scopes[slack.id],
                "tool_count": len(actual_scopes),
                "reasoning_effort": reasoning_effort,
                "roles": actual_roles,
                "all_role_payloads_preserved": True,
                "existing_tool_scopes_preserved": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
