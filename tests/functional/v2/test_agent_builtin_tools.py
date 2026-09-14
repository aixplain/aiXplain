"""Functional coverage for built-in agent toolkits (ENG-3699).

Skipped until ENG-3698 ships `builtinTools` on the backend: until then the key is
ignored on create and absent from the read, so the round-trip below would fail
for a reason that has nothing to do with the SDK. Un-skipping is the one-line
change immediately below.
"""

import time

import pytest

pytestmark = pytest.mark.skip(reason="Requires builtinTools support on the backend (ENG-3698)")

#: Tool names the worker reports in a run step when a toolkit is used.
BUILTIN_STEP_TOOLS = {"read_file", "list_directory", "glob", "grep", "write_file", "edit_file", "run_python"}


def _step_tool_names(response) -> set:
    """Collect every tool name the run's intermediate steps mention.

    The engine has more than one spelling for the field naming the tool a step
    invoked, so all of them are read and the union returned; the assertion below
    only asks whether a built-in tool appears at all.
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


@pytest.mark.flaky(reruns=2, reason="LLM may not always choose to use a built-in toolkit")
def test_agent_runs_with_file_and_python_builtin_toolkits(client, resource_tracker):
    """Enable the file and python toolkits, run, and confirm one of them was used.

    Verifies end to end that:

    1. an agent carrying `builtin_tools` is accepted by the backend;
    2. the list survives a `get()` round-trip;
    3. the worker actually exposes the toolkits to the agent at run time.
    """
    agent = client.Agent(
        name=f"builtin-toolkit-test-{int(time.time())}",
        description="Temporary agent for built-in toolkit functional testing",
        instructions=(
            "You have a sandboxed workspace with a filesystem and a Python interpreter. "
            "Use them rather than answering from memory."
        ),
        builtin_tools=["file", "python"],
    )
    agent.save()
    resource_tracker.append(agent)

    assert client.Agent.get(agent.id).builtin_tools == ["file", "python"]

    response = agent.run(
        "List the files in your workspace, then use Python to compute 17 * 23. "
        "Do not answer the arithmetic from memory — run it."
    )

    assert response.status == "SUCCESS", f"Agent execution failed: {response.status}"

    used = _step_tool_names(response)
    assert used & BUILTIN_STEP_TOOLS, (
        f"Expected a built-in toolkit step (one of {sorted(BUILTIN_STEP_TOOLS)}) in the run's "
        f"intermediate steps; saw {sorted(used)}."
    )


def test_builtin_toolkits_can_be_changed_on_a_saved_agent(client, resource_tracker):
    """Adding and clearing toolkits must both persist, `[]` included."""
    agent = client.Agent(
        name=f"builtin-toolkit-update-{int(time.time())}",
        description="Temporary agent for built-in toolkit persistence",
        instructions="Use the Python interpreter for anything numeric.",
        builtin_tools=["python"],
    )
    agent.save()
    resource_tracker.append(agent)

    fetched = client.Agent.get(agent.id)
    fetched.builtin_tools.append("file")
    fetched.save()

    assert sorted(client.Agent.get(agent.id).builtin_tools) == ["file", "python"]

    # An explicit empty list is how a caller turns every toolkit back off.
    fetched.builtin_tools = []
    fetched.save()

    assert client.Agent.get(agent.id).builtin_tools in (None, [])
