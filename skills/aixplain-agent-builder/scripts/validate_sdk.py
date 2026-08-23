#!/usr/bin/env python3
"""Validate the aixplain agent-builder skill against SDK v2.

Local checks always run. Read-only marketplace checks run only when
AIXPLAIN_API_KEY is present. The key is never printed or persisted.
"""

from __future__ import annotations

import importlib.metadata
import inspect
import os

from aixplain import Aixplain
from aixplain.v2.inspector import Inspector

EXPECTED_VERSION = "0.2.47"
STABLE_TOOLS = {
    "Code Execution": "698cda188bbb345db14ac13b",
    "Marketplace Search": "6960f934f316da19e5f22494",
    "File Manager": "6a0216cffb2a801f1c41e32e",
}
STABLE_INTEGRATIONS = {
    "Python Sandbox": "688779d8bfb8e46c273982ca",
    "Gmail": "6864328d1223092cb4294d30",
    "Slack": "686432941223092cb4294d3f",
    "Google Drive": "6864329b1223092cb4294d4e",
    "Google Calendar": "686432901223092cb4294d36",
    "aiR Knowledge Base": "6904bcf672a6e36b68bb72fb",
    "PostgreSQL": "693ac6e8217c7b13b480970f",
    "SQLite": "689e06ed3ce71f58d73cc999",
}


def main() -> None:
    version = importlib.metadata.version("aixplain")
    assert version == EXPECTED_VERSION, (
        f"Expected aixplain {EXPECTED_VERSION}; installed {version}"
    )

    aixplain_signature = inspect.signature(Aixplain)
    inspector_signature = inspect.signature(Inspector)
    assert "api_key" in aixplain_signature.parameters
    assert "action" in inspector_signature.parameters
    assert "metric" in inspector_signature.parameters
    assert "targets" in inspector_signature.parameters

    inspector = Inspector(
        name="validation_gate",
        severity="high",
        targets=["output"],
        action="abort",
        metric={"asset_id": "validation-model-id", "prompt": "Validate output."},
    )
    payload = inspector.to_dict()
    assert payload["action"] == {"type": "abort"}
    assert payload["targets"] == ["output"]
    assert payload["evaluator"]["assetId"] == "validation-model-id"

    print(f"PASS SDK version: {version}")
    print(f"PASS Aixplain signature: {aixplain_signature}")
    print(f"PASS Inspector signature: {inspector_signature}")
    print("PASS Inspector payload serialization")

    api_key = os.environ.get("AIXPLAIN_API_KEY")
    if not api_key:
        print("SKIP authenticated checks: AIXPLAIN_API_KEY is not set")
        return

    aix = Aixplain(api_key=api_key)
    tools = aix.Tool.search(query="code execution").results
    integrations = aix.Integration.search(query="gmail").results

    assert tools, "Tool search returned no results"
    assert integrations, "Integration search returned no results"

    tool_actions = {}
    for name, asset_id in STABLE_TOOLS.items():
        tool = aix.Tool.get(asset_id)
        actions = list(tool.actions)
        assert actions, f"{name} exposed no actions"
        tool_actions[name] = actions

    for name, asset_id in STABLE_INTEGRATIONS.items():
        integration = aix.Integration.get(asset_id)
        assert integration.id == asset_id, f"{name} resolved to an unexpected ID"

    assert tool_actions["Code Execution"] == ["run"], tool_actions["Code Execution"]

    print(f"PASS tool search: {len(tools)} result(s)")
    print(f"PASS integration search: {len(integrations)} result(s)")
    print(f"PASS stable tools: {tool_actions}")
    print(f"PASS stable integrations: {len(STABLE_INTEGRATIONS)}")


if __name__ == "__main__":
    main()
