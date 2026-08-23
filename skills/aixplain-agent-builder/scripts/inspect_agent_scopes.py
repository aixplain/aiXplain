#!/usr/bin/env python3
"""Compare raw agent tool scopes with SDK-hydrated scopes."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from aixplain import Aixplain


def hydrated_scope(tool: Any) -> list[str]:
    value = getattr(tool, "allowed_actions", None)
    if value is not None:
        return list(value)
    if isinstance(tool, dict):
        return list(tool.get("actions") or tool.get("allowedActions") or [])
    return []


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: inspect_agent_scopes.py <agent-id>")

    aix = Aixplain(api_key=os.environ["AIXPLAIN_API_KEY"])
    agent_id = sys.argv[1]
    raw = aix.Agent.context.client.get(f"v2/agents/{agent_id}")
    loaded = aix.Agent.get(agent_id)

    raw_tools = raw.get("tools") or raw.get("assets") or []
    raw_summary = []
    for index, tool in enumerate(raw_tools):
        if not isinstance(tool, dict):
            raw_summary.append({"index": index, "value": str(tool)})
            continue
        parameters = tool.get("parameters") or []
        raw_summary.append(
            {
                "id": tool.get("id") or tool.get("assetId"),
                "name": tool.get("name"),
                "actions": tool.get("actions") or tool.get("allowedActions") or [],
                "parameter_actions": [
                    item.get("name") or item.get("code")
                    for item in parameters
                    if isinstance(item, dict)
                ],
            }
        )

    hydrated_summary = [
        {
            "id": getattr(tool, "id", None),
            "name": getattr(tool, "name", None),
            "allowed_actions": hydrated_scope(tool),
        }
        for tool in loaded.tools or []
    ]

    raw_scopes_by_id = {
        item.get("id") or item.get("assetId"): list(item.get("actions") or item.get("allowedActions") or [])
        for item in raw_tools
        if isinstance(item, dict) and (item.get("id") or item.get("assetId"))
    }
    for tool in loaded.tools or []:
        tool_id = getattr(tool, "id", None)
        if tool_id in raw_scopes_by_id:
            tool.allowed_actions = raw_scopes_by_id[tool_id]

    repaired_payload = loaded.build_save_payload()
    repaired_scopes_by_id = {
        item.get("id") or item.get("assetId"): list(item.get("actions") or item.get("allowedActions") or [])
        for item in (repaired_payload.get("tools") or [])
        if isinstance(item, dict) and (item.get("id") or item.get("assetId"))
    }
    assert repaired_scopes_by_id == raw_scopes_by_id, {
        "raw": raw_scopes_by_id,
        "repaired_payload": repaired_scopes_by_id,
    }

    print(
        json.dumps(
            {
                "agent_id": agent_id,
                "raw_tools": raw_summary,
                "hydrated_tools": hydrated_summary,
                "repaired_payload_scopes": repaired_scopes_by_id,
                "workaround_verified": True,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
