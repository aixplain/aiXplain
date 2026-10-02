"""Functional tests for the v2 Agent lifecycle (ENG-3688).

Ports the scenarios that lived in ``tests/functional/agent/agent_functional_test.py``
before v1 was removed (PROD-2918). Generic CRUD and the web-tool tests already
have a v2 home in ``test_agent.py``; this file carries the draft/onboard
transition, subcomponent, tool-kind and round-trip scenarios that had no v2 twin.

Scenarios with no v2 equivalent are annotated in place:

- ``AgentFactory.create_sql_tool`` -- no v2 equivalent (see MIGRATION.md).
- ``AgentFactory.create_pipeline_tool`` -- no v2 equivalent (see MIGRATION.md).
"""

import json
import re
import time
import uuid
from typing import List, Optional

import pytest
from pydantic import BaseModel

from aixplain.v2 import AssetStatus
from aixplain.v2.exceptions import APIError

#: Backend bug that keeps the Slack agent test skipped: the send-message payload
#: is rejected ("Unsupported Slack send message field(s). text: ..."). Link the
#: ticket here so the skip is lifted with it.
SLACK_BACKEND_BUG = "BUG-1098"

#: Instructions used by the expected-output tests. The table makes a JSON answer
#: the only useful shape, so the run exercises the schema end to end.
EXPECTED_OUTPUT_INSTRUCTIONS = (
    "Answer with a JSON object matching the schema. Use this table:\n"
    "| name | age | city |\n"
    "| Ana | 31 | Lisbon |\n"
    "| Bob | 25 | Berlin |\n"
)


def _unique(prefix: str) -> str:
    """Return a collision-resistant agent/tool name."""
    return f"{prefix} {int(time.time())}-{uuid.uuid4().hex[:6]}"


def _agent_ids(agents) -> List[Optional[str]]:
    """Return the ids referenced by an agent's ``agents`` list, whichever shape it is."""
    return [a if isinstance(a, str) else a.get("id") if isinstance(a, dict) else a.id for a in agents or []]


def _parse_json(text: str) -> dict:
    """Parse *text* as JSON, tolerating a fenced code block."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        assert match, f"no JSON object found in the output: {text!r}"
        return json.loads(match.group(1))


class Person(BaseModel):
    """One row of the expected-output table."""

    name: str
    age: int
    city: Optional[str] = None


class People(BaseModel):
    """The expected-output schema for a run."""

    result: List[Person]


# ---------------------------------------------------------------------------
# Draft / onboard lifecycle
# ---------------------------------------------------------------------------


def test_agent_saved_as_draft_stays_draft(client, resource_tracker):
    """``save(as_draft=True)`` persists the agent with DRAFT status."""
    agent = client.Agent(name=_unique("Draft Agent"), instructions="Answer briefly.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)

    assert agent.id is not None
    assert agent.status == AssetStatus.DRAFT
    assert client.Agent.get(agent.id).status == AssetStatus.DRAFT


def test_agent_saved_without_draft_is_onboarded(client, resource_tracker):
    """A plain ``save()`` onboards the agent."""
    agent = client.Agent(name=_unique("Onboarded Agent"), instructions="Answer briefly.")
    agent.save()
    resource_tracker.append(agent)

    assert agent.status == AssetStatus.ONBOARDED
    assert client.Agent.get(agent.id).status == AssetStatus.ONBOARDED


def test_draft_agent_auto_saves_before_run(client, resource_tracker):
    """A modified draft is saved implicitly on ``run()`` and stays a draft."""
    agent = client.Agent(name=_unique("Auto Draft Agent"), instructions="Answer briefly.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)

    agent.instructions = "Always answer with the single word: pong."
    response = agent.run("ping")

    assert response.status == "SUCCESS"
    assert agent.status == AssetStatus.DRAFT


def test_onboarded_agent_rejects_mutation_without_save(client, resource_tracker):
    """An onboarded agent must be saved before a run sees its edits."""
    agent = client.Agent(name=_unique("Frozen Agent"), instructions="Answer briefly.")
    agent.save()
    resource_tracker.append(agent)

    agent.instructions = "Always answer with the single word: pong."
    with pytest.raises(ValueError, match="onboarded and cannot be modified"):
        agent.run("ping")

    agent.save()
    response = agent.run("ping")
    assert response.status == "SUCCESS"


def test_end2end_draft_then_onboard_run(client, assets, resource_tracker):
    """Create as draft, run, onboard, re-fetch and run again."""
    agent = client.Agent(
        name=_unique("End2End Agent"),
        description="Runs before and after onboarding.",
        instructions="Answer briefly.",
        llm=assets.DEFAULT_LLM,
    )
    agent.save(as_draft=True)
    resource_tracker.append(agent)
    assert agent.status == AssetStatus.DRAFT
    assert agent.run("Say hello in one word.").status == "SUCCESS"

    agent.save()
    assert agent.status == AssetStatus.ONBOARDED
    fetched = client.Agent.get(agent.id)
    assert fetched.status == AssetStatus.ONBOARDED
    response = fetched.run("Say goodbye in one word.")
    assert response.status == "SUCCESS"
    assert response.data.output


# ---------------------------------------------------------------------------
# Subcomponents
# ---------------------------------------------------------------------------


def test_save_subcomponents_persists_unsaved_subagent(client, resource_tracker):
    """``save(save_subcomponents=True)`` saves an unsaved subagent before the parent."""
    sub = client.Agent(name=_unique("Sub Agent"), instructions="You are a subagent.")
    parent = client.Agent(name=_unique("Parent Agent"), instructions="You orchestrate.", agents=[sub])
    # Register the dependency first: teardown deletes newest-first.
    resource_tracker.append(sub)
    resource_tracker.append(parent)

    parent.save(save_subcomponents=True)

    assert sub.id is not None
    assert parent.id is not None
    assert sub.id in _agent_ids(client.Agent.get(parent.id).agents)


def test_save_without_subcomponents_rejects_unsaved_subagent(client, resource_tracker):
    """A plain save refuses an unsaved subagent; recursive save then succeeds."""
    sub = client.Agent(name=_unique("Unsaved Sub"), instructions="You are a subagent.")
    parent = client.Agent(name=_unique("Strict Parent"), instructions="You orchestrate.", agents=[sub])
    resource_tracker.append(sub)
    resource_tracker.append(parent)

    with pytest.raises(ValueError, match="must be saved before saving"):
        parent.save()

    parent.save(save_subcomponents=True)
    assert sub.id is not None
    assert parent.id is not None


# ---------------------------------------------------------------------------
# Tool kinds
# ---------------------------------------------------------------------------


def test_custom_code_tool(client, resource_tracker):
    """``Tool(code=...)`` runs deterministic custom Python inside an agent."""
    tool = client.Tool(
        name=_unique("Concat Tool"),
        description="Concatenate two strings and return the result.",
        code="def concat(aaa: str, bbb: str) -> str:\n    return aaa + bbb",
    )
    tool.save()
    resource_tracker.append(tool)

    agent = client.Agent(
        name=_unique("Concat Agent"),
        instructions="Always use the tool to answer.",
        tools=[tool],
    )
    agent.save()
    resource_tracker.append(agent)

    response = agent.run("Concatenate 'Hello' and 'World' using the tool.")
    assert response.status == "SUCCESS"
    assert "HelloWorld" in response.data.output


def test_python_interpreter_tool(client, resource_tracker):
    """The marketplace Python Interpreter tool can be attached and used."""
    results = client.Tool.search(q="interpreter").results
    match = next((t for t in results if "interpreter" in (t.name or "").lower()), None)
    if match is None:
        pytest.skip("No Python Interpreter tool found in the marketplace")

    tool = client.Tool.get(match.id)
    agent = client.Agent(
        name=_unique("Interpreter Agent"),
        instructions="Use the Python Interpreter tool for every computation.",
        tools=[tool],
    )
    agent.save()
    resource_tracker.append(agent)

    response = agent.run("Use the Python Interpreter to compute 2 + 2 and print the result.")
    assert response.status == "SUCCESS"
    assert "4" in response.data.output


def test_add_and_remove_tool_round_trip(client, assets, resource_tracker):
    """Adding then removing a tool survives a fetch round-trip."""
    agent = client.Agent(name=_unique("Tool Round Trip"), instructions="Use tools when asked.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)
    assert agent.tools == []

    agent.tools = [client.Tool.get(assets.TAVILY)]
    agent.save()
    assert len(client.Agent.get(agent.id).tools) == 1

    agent.tools.pop()
    agent.save()
    assert client.Agent.get(agent.id).tools == []


def test_model_tool_parameter_survives_round_trip(client, assets, resource_tracker):
    """A per-tool parameter override is persisted and read back after a fetch."""
    model = client.Model.get(assets.TRANSLATION_MODEL)
    assert "sourcelanguage" in model.inputs, f"{assets.TRANSLATION_MODEL} has no sourcelanguage input"
    model.inputs["sourcelanguage"] = "pt"

    agent = client.Agent(
        name=_unique("Translation Agent"),
        instructions="Translate using the attached model tool.",
        tools=[model],
    )
    agent.save()
    resource_tracker.append(agent)

    fetched_tool = client.Agent.get(agent.id).tools[0]
    params = fetched_tool.get_parameters()
    assert any(p["name"] == "sourcelanguage" and p["value"] == "pt" for p in params)

    assert agent.run("Translate 'Hello' to Portuguese.").status == "SUCCESS"


def test_llm_parameter_is_preserved_on_agent(client, assets):
    """The exact ``Model`` instance (and its parameter edits) is kept as the agent's llm."""
    model = client.Model.get(assets.NON_DEFAULT_LLM)
    model.inputs["temperature"] = 0.1

    agent = client.Agent(name=_unique("LLM Param Agent"), instructions="Answer briefly.", llm=model)

    assert agent.llm is model
    assert agent.llm.inputs["temperature"].value == 0.1


@pytest.mark.skip(
    reason=(
        "Backend rejects the Slack send-message payload: 'Unsupported Slack send message field(s). "
        f"text: Use markdown_text for normal content, or fallback_text with blocks.' ({SLACK_BACKEND_BUG})"
    )
)
def test_agent_with_slack_action_tool(client, assets, slack_token, resource_tracker):
    """An agent runs a Slack action tool end to end."""
    integration = client.Integration.get(assets.SLACK_INTEGRATION)
    tool = client.Tool(
        name=_unique("Slack tool"),
        integration=integration,
        config={"token": slack_token},
        allowed_actions=["SLACK_SEND_MESSAGE"],
    )
    tool.save()
    resource_tracker.append(tool)

    agent = client.Agent(
        name=_unique("Slack Agent"),
        description="Posts messages to Slack.",
        instructions="Always use the Slack tool to answer.",
        tools=[tool],
    )
    agent.save()
    resource_tracker.append(agent)

    response = agent.run("Post a message to #integrations-test saying 'functional test'.")
    assert response.status == "SUCCESS"
    used = [tool_step.get("tool") for step in response.data.steps for tool_step in (step.get("tool_steps") or [])]
    assert "SLACK_SEND_MESSAGE" in used


# ---------------------------------------------------------------------------
# Update / get round-trips
# ---------------------------------------------------------------------------


def test_update_draft_agent_name_round_trip(client, resource_tracker):
    """Renaming a draft agent is persisted and visible after a fetch."""
    agent = client.Agent(name=_unique("Rename Me"), instructions="Answer briefly.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)

    new_name = _unique("Renamed Agent")
    agent.name = new_name
    agent.save()

    assert client.Agent.get(agent.id).name == new_name


def test_agent_round_trips_execution_and_inspector_fields(client, resource_tracker):
    """Execution and inspector fields survive a save -> fetch round-trip."""
    agent = client.Agent(
        name=_unique("Fields Agent"),
        instructions=EXPECTED_OUTPUT_INSTRUCTIONS,
        max_inspectors=2,
        inspector_targets=["output"],
        output_format="json",
        expected_output=People,
    )
    agent.save()
    resource_tracker.append(agent)

    fetched = client.Agent.get(agent.id)
    assert fetched.max_inspectors == 2
    assert fetched.inspector_targets == ["output"]
    assert fetched.output_format == "json"
    assert fetched.expected_output


def test_agent_expected_output_run_returns_json(client, resource_tracker):
    """A run with a JSON schema returns parseable JSON matching the schema."""
    agent = client.Agent(
        name=_unique("JSON Agent"),
        instructions=EXPECTED_OUTPUT_INSTRUCTIONS,
        output_format="json",
        expected_output=People,
    )
    agent.save()
    resource_tracker.append(agent)

    response = agent.run(
        "List every person in the table.",
        execution_params={"output_format": "json", "expected_output": People},
    )

    assert response.status == "SUCCESS"
    payload = _parse_json(response.data.output)
    assert {row["name"] for row in payload["result"]} == {"Ana", "Bob"}


def test_agent_persists_file_reference(client, tmp_path, resource_tracker):
    """A saved File attached to an agent survives a fetch round-trip."""
    path = tmp_path / "handbook.txt"
    path.write_text("Reference material for the agent.")
    document = client.File(path)
    document.save()
    resource_tracker.append(document)

    agent = client.Agent(name=_unique("Files Agent"), instructions="Use the reference.", files=[document])
    agent.save()
    resource_tracker.append(agent)

    assert [f.id for f in client.Agent.get(agent.id).files] == [document.id]


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_fail_non_existent_llm(client):
    """Saving an agent with an unknown llm id fails loudly."""
    agent = client.Agent(name=_unique("Bad LLM Agent"), instructions="Answer briefly.", llm="non_existent_llm")

    with pytest.raises(Exception) as excinfo:
        agent.save()

    assert "not found" in str(excinfo.value).lower()


def test_delete_agent_in_use_fails(client, resource_tracker):
    """A subagent referenced by a team agent cannot be deleted."""
    sub = client.Agent(name=_unique("In-Use Sub"), instructions="You are a subagent.")
    sub.save()
    resource_tracker.append(sub)

    team = client.Agent(name=_unique("In-Use Team"), instructions="You orchestrate.", agents=[sub])
    team.save()
    resource_tracker.append(team)

    with pytest.raises(APIError) as excinfo:
        sub.delete()

    message = str(excinfo.value).lower()
    assert "cannot be deleted" in message or "team" in message
