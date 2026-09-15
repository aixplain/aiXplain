"""Functional coverage for built-in agent toolkits (ENG-3699).

`builtinTools` is deployed on dev only, while CI's functional legs run against the
test and prod backends, so the module stays skipped there. Un-skip it locally
against dev to exercise it.
"""

import time

import pytest

from aixplain.v2.agent import _step_unit_names

pytestmark = pytest.mark.skip(
    reason="builtinTools is live on dev only; CI functional legs target test/prod (ENG-3698 rollout)"
)

#: Tool names the worker reports as a step's unit when a toolkit is used.
BUILTIN_STEP_TOOLS = {"read_file", "list_directory", "glob", "grep", "write_file", "edit_file", "run_python"}

BASH_GATED_WARNING = "Built-in toolkit 'bash' is not enabled on this worker"

READ_AFTER_WRITE_TIMEOUT_S = 8.0


def _get_when_builtin_tools_match(client, agent_id, expected):
    # Dev's read path can trail a save by ~1 s; a field the backend lost outright (ENG-3711) never converges.
    deadline = time.monotonic() + READ_AFTER_WRITE_TIMEOUT_S
    while True:
        expired = time.monotonic() >= deadline
        try:
            fetched = client.Agent.get(agent_id)
        except Exception:
            # A create can 404 for the same lag; only let it surface once the budget is spent.
            if expired:
                raise
            time.sleep(0.5)
            continue
        if sorted(fetched.builtin_tools or []) == sorted(expected) or expired:
            return fetched
        time.sleep(0.5)


@pytest.mark.flaky(reruns=2, reason="LLM may not always choose to use a built-in toolkit")
def test_agent_runs_with_file_and_python_builtin_toolkits(client, resource_tracker):
    """Enable the file and python toolkits, run, and confirm one of them was used."""
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

    fetched = _get_when_builtin_tools_match(client, agent.id, ["file", "python"])
    assert sorted(fetched.builtin_tools or []) == ["file", "python"]

    response = agent.run(
        "Write the text 'hello' to a file named hello.txt, then use Python to compute 17 * 23. "
        "Do not answer the arithmetic from memory — run it."
    )

    assert response.status == "SUCCESS", f"Agent execution failed: {response.status}"

    used = _step_unit_names(response.data.steps)
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

    fetched = _get_when_builtin_tools_match(client, agent.id, ["python"])
    assert fetched.builtin_tools == ["python"]

    fetched.builtin_tools.append("file")
    fetched.save()

    assert sorted(_get_when_builtin_tools_match(client, agent.id, ["file", "python"]).builtin_tools or []) == [
        "file",
        "python",
    ]

    fetched.builtin_tools = []
    fetched.save()

    assert _get_when_builtin_tools_match(client, agent.id, []).builtin_tools in (None, [])


def test_a_gated_toolkit_is_dropped_with_a_warning_on_the_run_result(client, resource_tracker):
    """`bash` is disabled on every worker: the run succeeds and says why bash is missing."""
    agent = client.Agent(
        name=f"builtin-toolkit-gated-{int(time.time())}",
        description="Temporary agent for built-in toolkit gating",
        instructions="Answer briefly.",
        builtin_tools=["python", "bash"],
    )
    agent.save()
    resource_tracker.append(agent)

    # Running a lagged definition could omit bash entirely and fail for the wrong reason.
    fetched = _get_when_builtin_tools_match(client, agent.id, ["python", "bash"])
    assert sorted(fetched.builtin_tools or []) == ["bash", "python"]

    response = agent.run("Reply with the single word: ok")

    assert response.status == "SUCCESS", f"Agent execution failed: {response.status}"
    # ``response.warnings`` covers both placements; ``data.warnings`` alone misses a top-level key.
    assert any(BASH_GATED_WARNING in warning for warning in response.warnings), response.warnings
