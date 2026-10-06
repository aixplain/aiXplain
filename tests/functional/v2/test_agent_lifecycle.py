"""Functional tests for the v2 Agent lifecycle (ENG-3688).

Ports the scenarios that lived in ``tests/functional/agent/agent_functional_test.py``
before v1 was removed (PROD-2918). Generic CRUD and the web-tool tests already
have a v2 home in ``test_agent.py``; this file carries the draft/onboard
transition, subcomponent, tool-kind and round-trip scenarios that had no v2 twin.

v1 scenarios not ported here, and why:

- ``AgentFactory.create_sql_tool`` (SQLite and CSV) -- no v2 equivalent (see
  MIGRATION.md).
- ``AgentFactory.create_pipeline_tool`` -- no v2 equivalent (see MIGRATION.md).
- ``AgentFactory.create_python_interpreter_tool`` -- v2 runs Python through the
  Python Sandbox integration, which ``Tool(code=...)`` already exercises in
  ``test_custom_code_tool`` below; a marketplace search for an "interpreter"
  tool depends on backend state and would mostly skip.
- ``{{var}}`` placeholder substitution (v1 ``test_instructions``; v2 spelling
  ``run(variables=...)``) -- not ported in this change. The substitution is
  done by the backend, so the only end-to-end check is another LLM-output
  assertion; it is not part of the draft/onboard lifecycle this file covers.
- Agent with two utility tools (v1 ``test_agent_with_utility_tool``) -- v2
  replaces the utility-model builder with ``Tool(code=...)``, which is
  covered by ``test_custom_code_tool``; a second tool adds LLM-choice
  flakiness rather than SDK coverage. Not ported.
- MCP connector deploy (v1 ``test_agent_with_mcp_tool``) -- already skipped in
  v1 ("MCP connector has no available actions") and it depended on a
  hard-coded Zapier MCP URL. Not ported.
"""

import json
import re
import time
import uuid
from typing import List, Optional

import pytest
from pydantic import BaseModel

from aixplain.v2 import AssetStatus
from aixplain.v2.exceptions import ResourceError

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


def _track_saved(tracker, *resources) -> None:
    """Register every resource in *resources* that got an id, in the order given.

    Pass dependencies before the resources that reference them: teardown deletes
    newest-first. Anything that never got an id was never created, so tracking
    it would only report a false orphan.
    """
    for resource in resources:
        if getattr(resource, "id", None):
            tracker.append(resource)


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


# The "pong" check depends on the LLM following its instructions.
@pytest.mark.flaky(reruns=2)
def test_draft_agent_auto_saves_before_run(client, resource_tracker):
    """A modified draft is saved implicitly on ``run()`` and stays a draft."""
    agent = client.Agent(name=_unique("Auto Draft Agent"), instructions="Answer briefly.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)

    new_instructions = "Always answer with the single word: pong."
    agent.instructions = new_instructions
    response = agent.run("ping")

    assert response.status == "SUCCESS"
    assert "pong" in (response.data.output or "").lower()
    fetched = client.Agent.get(agent.id)
    assert fetched.instructions == new_instructions
    assert fetched.status == AssetStatus.DRAFT


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

    try:
        parent.save(save_subcomponents=True)
    finally:
        # The dependency first: teardown deletes newest-first.
        _track_saved(resource_tracker, sub, parent)

    assert sub.id is not None
    assert parent.id is not None
    assert sub.id in _agent_ids(client.Agent.get(parent.id).agents)


def test_save_without_subcomponents_rejects_unsaved_subagent(client, resource_tracker):
    """A plain save refuses an unsaved subagent; recursive save then succeeds."""
    sub = client.Agent(name=_unique("Unsaved Sub"), instructions="You are a subagent.")
    parent = client.Agent(name=_unique("Strict Parent"), instructions="You orchestrate.", agents=[sub])

    with pytest.raises(ValueError, match="must be saved before saving"):
        parent.save()
    assert sub.id is None
    assert parent.id is None

    try:
        parent.save(save_subcomponents=True)
    finally:
        _track_saved(resource_tracker, sub, parent)
    assert sub.id is not None
    assert parent.id is not None


# ---------------------------------------------------------------------------
# Tool kinds
# ---------------------------------------------------------------------------


# The LLM may answer without calling the tool.
@pytest.mark.flaky(reruns=2)
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


def test_add_and_remove_tool_round_trip(client, assets, resource_tracker):
    """Adding then removing a tool survives a fetch round-trip."""
    agent = client.Agent(name=_unique("Tool Round Trip"), instructions="Use tools when asked.")
    agent.save(as_draft=True)
    resource_tracker.append(agent)
    assert agent.tools == []

    agent.tools = [client.Tool.get(assets.TAVILY)]
    agent.save(as_draft=True)
    fetched = client.Agent.get(agent.id)
    assert len(fetched.tools) == 1
    assert fetched.status == AssetStatus.DRAFT

    agent.tools.pop()
    agent.save(as_draft=True)
    fetched = client.Agent.get(agent.id)
    assert fetched.tools == []
    assert fetched.status == AssetStatus.DRAFT


# The run depends on the LLM choosing to call the translation tool.
@pytest.mark.flaky(reruns=2)
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

    # The query is Portuguese, matching the pinned sourcelanguage.
    response = agent.run("Translate: 'Olá, como vai você?'")
    assert response.status == "SUCCESS"
    assert response.data.output


def test_llm_parameter_is_persisted_on_agent(client, assets, resource_tracker):
    """A ``Model`` llm's id and parameter edits survive a save -> fetch round-trip."""
    model = client.Model.get(assets.NON_DEFAULT_LLM)
    model.inputs["temperature"] = 0.1

    agent = client.Agent(name=_unique("LLM Param Agent"), instructions="Answer briefly.", llm=model)
    agent.save()
    resource_tracker.append(agent)

    # A fetch decodes the stored ``model`` as ``{id, name?, parameters?: {name: value}}``.
    fetched_llm = client.Agent.get(agent.id).llm
    assert isinstance(fetched_llm, dict), f"unexpected fetched llm shape: {fetched_llm!r}"
    assert fetched_llm["id"] == assets.NON_DEFAULT_LLM
    parameters = fetched_llm.get("parameters") or {}
    assert "temperature" in parameters, f"temperature was not persisted: {fetched_llm!r}"
    assert float(parameters["temperature"]) == pytest.approx(0.1)


@pytest.mark.skip(
    reason="Backend bug BUG-1098: rejects the Slack send-message payload: 'Unsupported Slack send message field(s). "
    "text: Use markdown_text for normal content, or fallback_text with blocks.' Re-test monthly."
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
    agent.save(as_draft=True)

    fetched = client.Agent.get(agent.id)
    assert fetched.name == new_name
    assert fetched.status == AssetStatus.DRAFT


def test_agent_round_trips_execution_and_inspector_fields(client, resource_tracker):
    """Execution fields survive a save -> fetch round-trip; inspector fields reach the wire."""
    agent = client.Agent(
        name=_unique("Fields Agent"),
        instructions=EXPECTED_OUTPUT_INSTRUCTIONS,
        max_inspectors=2,
        inspector_targets=["output"],
        output_format="json",
        expected_output=People,
    )
    # The inspector fields are asserted on what the SDK sends, not on the fetched
    # agent: the platform's v2 create/update path does not persist
    # ``inspectorTargets`` or ``maxInspectors`` (the fetched agent reads back ``[]``
    # and None), so a fetch would test the backend's schema rather than the SDK.
    # Backend ticket to be filed; move these below the fetch once it is fixed.
    payload = agent.build_save_payload()
    assert payload["inspectorTargets"] == ["output"]
    assert payload["maxInspectors"] == 2

    agent.save()
    resource_tracker.append(agent)

    fetched = client.Agent.get(agent.id)
    assert fetched.output_format == "json"
    # The SDK persists a Pydantic class as ``json.dumps(model_json_schema())``.
    stored = fetched.expected_output
    if isinstance(stored, str):
        stored = json.loads(stored)
    assert stored == People.model_json_schema()


# The JSON shape depends on the LLM honouring the schema.
@pytest.mark.flaky(reruns=2)
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


# Saving with an unknown llm id is covered once, by test_team_agent.py::test_fail_non_existent_llm,
# which asserts the backend's actual error text; a second copy here would assert different text.


def test_delete_agent_in_use_fails(client, resource_tracker):
    """A subagent referenced by a team agent cannot be deleted."""
    sub = client.Agent(name=_unique("In-Use Sub"), instructions="You are a subagent.")
    sub.save()
    resource_tracker.append(sub)

    team = client.Agent(name=_unique("In-Use Team"), instructions="You orchestrate.", agents=[sub])
    team.save()
    resource_tracker.append(team)

    # ``delete`` is wrapped by ``@with_hooks``, which re-raises the APIError as ResourceError.
    with pytest.raises(ResourceError) as excinfo:
        sub.delete()

    # The backend reports the refusal by code: "failed to delete resource: err.agent_is_in_use".
    assert "agent_is_in_use" in str(excinfo.value).lower()
