"""Functional coverage for built-in agent toolkits (ENG-3699).

Skipped until ENG-3698 puts the ``{"type": "builtin", ...}`` row behind the dev
backend: until then the create call rejects the tool and the test would fail for
a reason that has nothing to do with the SDK. Un-skipping is the one-line change
below once the backend is deployed.
"""

import time

import pytest

from aixplain.v2 import BuiltinTool

pytestmark = pytest.mark.skip(reason="Requires builtin toolkit support on the backend (ENG-3698)")

#: Tool names the worker reports in a run step when the toolkit is used.
FILE_STEP_TOOLS = {"read_file", "list_directory", "glob", "grep", "write_file", "edit_file"}
PYTHON_STEP_TOOLS = {"run_python"}


def _step_tool_names(response) -> set:
    """Collect every tool name the run's intermediate steps mention.

    The engine has more than one spelling for the field that names the tool a
    step invoked, so all of them are read and the union returned; the assertions
    below only ask whether a given tool appears at all.
    """
    data = getattr(response, "data", None)
    names = set()
    for step in getattr(data, "steps", None) or []:
        if not isinstance(step, dict):
            continue
        for key in ("tool", "toolName", "name", "action"):
            value = step.get(key)
            if isinstance(value, str):
                names.add(value)
    return names


@pytest.mark.flaky(reruns=2, reason="LLM may not always choose to call a built-in toolkit")
def test_agent_runs_with_file_and_python_builtin_toolkits(client, resource_tracker):
    """Attach the file and python toolkits, run, and confirm one of them was used.

    Verifies end to end that:

    1. an agent carrying ``BuiltinTool`` rows is accepted by the backend;
    2. the rows survive the round-trip and come back typed, not as bare dicts;
    3. the worker actually exposes the toolkits to the agent at run time.
    """
    agent = client.Agent(
        name=f"builtin-toolkit-test-{int(time.time())}",
        description="Temporary agent for built-in toolkit functional testing",
        instructions=(
            "You have a sandboxed workspace with a filesystem and a Python interpreter. "
            "Use them rather than answering from memory."
        ),
        tools=[
            BuiltinTool(toolkit="file", include=["read_file", "list_directory", "glob", "grep"]),
            BuiltinTool(toolkit="python", timeout_s=30),
        ],
    )
    agent.save()
    resource_tracker.append(agent)

    # The toolkits must read back as objects, so `agent.tools` is symmetric with
    # what was passed in and a re-save would not mangle them.
    fetched = client.Agent.get(agent.id)
    assert [type(tool) for tool in fetched.tools] == [BuiltinTool, BuiltinTool]
    assert [tool.toolkit for tool in fetched.tools] == ["file", "python"]
    assert fetched.tools[1].timeout_s == 30
    assert fetched.build_save_payload()["tools"] == agent.build_save_payload()["tools"]

    response = agent.run(
        "List the files in your workspace, then use Python to compute 17 * 23. "
        "Do not answer the arithmetic from memory — run it."
    )

    assert response.status == "SUCCESS", f"Agent execution failed: {response.status}"

    used = _step_tool_names(response)
    assert used & (FILE_STEP_TOOLS | PYTHON_STEP_TOOLS), (
        f"Expected a built-in toolkit step (one of {sorted(FILE_STEP_TOOLS | PYTHON_STEP_TOOLS)}) "
        f"in the run's intermediate steps; saw {sorted(used)}."
    )


@pytest.mark.flaky(reruns=2, reason="LLM may not always choose to call the python toolkit")
def test_python_builtin_toolkit_settings_are_persisted(client, resource_tracker):
    """A setting sent at create time must still be there after a fetch."""
    agent = client.Agent(
        name=f"builtin-python-settings-{int(time.time())}",
        description="Temporary agent for built-in toolkit settings persistence",
        instructions="Use the Python interpreter to compute anything numeric.",
        tools=[BuiltinTool(toolkit="python", include=["run_python"], timeout_s=15, expose_files=False)],
    )
    agent.save()
    resource_tracker.append(agent)

    (tool,) = client.Agent.get(agent.id).tools

    assert isinstance(tool, BuiltinTool)
    assert tool.as_tool() == {
        "type": "builtin",
        "toolkit": "python",
        "include": ["run_python"],
        "timeout_s": 15,
        "expose_files": False,
    }
