"""v2 functional twins for the legacy ``tests/functional/team_agent`` scenarios (ENG-3689).

The v1 team-agent suite was deleted with v1 (PROD-2918) and only five v2 tests
touched teams at all. This module re-covers the removed scenarios against the
current backend so ``aix.Agent(..., agents=[...])`` (a "team" in v2) stays
exercised end to end:

* task definitions on a subagent (including ``dependencies``);
* the ``llm`` / ``planner`` / ``supervisor`` / ``response_generator`` role
  overrides, asserted both persisted and present in the run payload;
* the ``run_response_generation`` run parameter;
* the nested save chain and statuses;
* mutating the subagent list of a saved team, then saving and running;
* one deployed agent shared by two teams;
* team instructions, llm parameter preservation, expected output, and draft
  updates;
* the ``evolve`` run parameter (the legacy ``evolve_async`` twin).

The naming convention follows ``test_agent_duplicate.py``: ``save()`` is the v2
deploy/onboard action, and ``save(save_subcomponents=True)`` persists the
subagents with the team.

Coverage map of the deleted ``tests/functional/team_agent/team_agent_functional_test.py``:

===============================  =========================================
legacy test                      v2 twin
===============================  =========================================
test_end2end                     ``test_end2end``
test_draft_team_agent_update     ``test_draft_team_agent_update``
test_nested_deployment_chain     ``test_nested_deployment_chain``
test_fail_non_existent_llm       ``test_fail_non_existent_llm``
test_add_remove_agents_from_team_agent
                                 ``test_add_remove_agents_from_team_agent``
test_team_agent_tasks            ``test_team_agent_tasks``
test_team_agent_with_instructions
                                 ``test_team_agent_with_instructions``
test_team_agent_llm_parameter_preservation
                                 ``test_team_agent_llm_parameter_preservation``
test_run_team_agent_with_expected_output
                                 ``test_run_team_agent_with_expected_output``
test_multiple_teams_with_shared_deployed_agent
                                 ``test_multiple_teams_with_shared_deployed_agent``
===============================  =========================================

Two legacy tests were already ``@pytest.mark.skip`` ("Tools not available") and
keep that reason here:

* ``test_team_agent_with_parameterized_agents`` -- needs the ``ConnectionTool``
  search model; the v2 tool surface is exercised by ``test_team_agent_tasks``
  instead.
* ``test_team_agent_with_slack_connector`` -- needs a live ``SLACK_TOKEN``.
"""

import time
import uuid

import pytest

from aixplain.v2 import AssetStatus

#: The platform default LLM, used for the team/subagents and for role overrides.
DEFAULT_LLM = "69b7e5f1b2fe44704ab0e7d0"
#: A second, distinct LLM so a role override cannot be confused with the default.
ALT_LLM = "698c87701239a117fd66b468"


def _name(prefix: str) -> str:
    """A per-run unique name: xdist workers and reruns must not collide."""
    return f"{prefix}-{int(time.time())}-{uuid.uuid4().hex[:6]}"


def _agent_ids(agents) -> list:
    """Ids of a team's ``agents``, which may hold id strings, dicts or ``Agent`` objects."""
    ids = []
    for agent in agents or []:
        if isinstance(agent, str):
            ids.append(agent)
        elif isinstance(agent, dict):
            ids.append(agent.get("id"))
        else:
            ids.append(getattr(agent, "id", None))
    return [agent_id for agent_id in ids if agent_id]


def _assert_success(response) -> str:
    """Assert a completed successful run and return its text output."""
    assert response is not None
    assert response.completed is True, f"run did not complete: {response.status}"
    assert response.status.upper() == "SUCCESS", f"run failed: {response.status}"
    data = getattr(response, "data", None)
    output = getattr(data, "output", None) or (data if isinstance(data, str) else "")
    assert output, "expected a non-empty run output"
    return output


def test_team_agent_with_instructions(client, resource_tracker):
    """A team's instructions round-trip through save/get unchanged."""
    instructions = "Coordinate the subagents and return one consolidated answer."
    sub = client.Agent(name=_name("TA sub"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA team"), instructions=instructions, agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert fetched.instructions == instructions
    assert _agent_ids(fetched.agents) == [sub.id]


def test_team_agent_tasks(client, resource_tracker):
    """Subagent task definitions and their dependency names persist on save."""
    first = "Gather the facts"
    sub = client.Agent(
        name=_name("TA task sub"),
        instructions="Work the tasks in order.",
        tasks=[
            client.Agent.Task(name=first, instructions="Gather the facts.", expected_output="facts"),
            client.Agent.Task(
                name="Write the summary",
                instructions="Summarize the facts.",
                expected_output="summary",
                dependencies=[first],
            ),
        ],
    )
    team = client.Agent(name=_name("TA task team"), instructions="Coordinate.", agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    fetched = client.Agent.get(sub.id)
    assert [task.name for task in fetched.tasks] == [first, "Write the summary"]
    assert fetched.tasks[0].expected_output == "facts"
    assert fetched.tasks[1].dependencies == [first]


def test_team_agent_llm_parameter_preservation(client, resource_tracker):
    """The primary llm override (id + parameter) survives save/get."""
    team = client.Agent(
        name=_name("TA llm team"),
        instructions="Coordinate.",
        llm={"id": ALT_LLM, "parameters": {"temperature": "0.3"}},
    )
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert fetched.llm == {"id": ALT_LLM, "parameters": {"temperature": "0.3"}}


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_role_llm_overrides_persisted_and_used(client, resource_tracker):
    """``planner`` / ``supervisor`` overrides persist and reach the run payload.

    The role *ids* come from the saved agent; the per-role *parameters* travel in
    the run payload as ``modelParameters`` (the shape the Temporal worker
    consumes). Both halves are asserted, and the team is run so the override is
    exercised, not just serialized.
    """
    sub = client.Agent(name=_name("TA roles sub"), instructions="Answer briefly.")
    team = client.Agent(
        name=_name("TA roles team"),
        instructions="Coordinate the subagents.",
        agents=[sub],
        planner={"id": ALT_LLM, "parameters": {"temperature": "0.1"}},
        supervisor={"id": ALT_LLM, "parameters": {"temperature": "0.2"}},
        response_generator={"id": ALT_LLM, "parameters": {"temperature": "0.4"}},
    )
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert fetched.planner == {"id": ALT_LLM, "parameters": {"temperature": "0.1"}}
    assert fetched.supervisor == {"id": ALT_LLM, "parameters": {"temperature": "0.2"}}
    assert fetched.response_generator == {"id": ALT_LLM, "parameters": {"temperature": "0.4"}}

    model_parameters = fetched.build_run_payload()["modelParameters"]
    assert model_parameters["planner"] == [{"name": "temperature", "value": "0.1"}]
    assert model_parameters["supervisor"] == [{"name": "temperature", "value": "0.2"}]
    assert model_parameters["responder"] == [{"name": "temperature", "value": "0.4"}]

    _assert_success(fetched.run("Reply with exactly the word OK."))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_run_response_generation(client, resource_tracker):
    """The ``run_response_generation`` run parameter is accepted end to end."""
    sub = client.Agent(name=_name("TA rrg sub"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA rrg team"), instructions="Coordinate.", agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    _assert_success(team.run("Reply with exactly the word OK.", run_response_generation=True))


def test_nested_deployment_chain(client, resource_tracker):
    """Saving a team recursively onboards the whole chain, leaf to top."""
    leaf = client.Agent(name=_name("TA leaf"), instructions="Leaf.")
    mid = client.Agent(name=_name("TA mid"), instructions="Mid.", agents=[leaf])
    top = client.Agent(name=_name("TA top"), instructions="Top.", agents=[mid])
    resource_tracker.append(leaf)
    resource_tracker.append(mid)
    top.save(save_subcomponents=True)
    resource_tracker.append(top)

    assert leaf.id and mid.id and top.id
    for agent in (leaf, mid, top):
        assert client.Agent.get(agent.id).status == AssetStatus.ONBOARDED


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_add_remove_agents_from_team_agent(client, resource_tracker):
    """A saved team's subagent list can be extended, saved, run, then shrunk."""
    first = client.Agent(name=_name("TA keep"), instructions="Answer A.")
    second = client.Agent(name=_name("TA drop"), instructions="Answer B.")
    team = client.Agent(name=_name("TA mutate team"), instructions="Coordinate.", agents=[first, second])
    resource_tracker.append(first)
    resource_tracker.append(second)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    added = client.Agent(name=_name("TA added"), instructions="Answer C.")
    added.save()
    # Placed before the team so newest-first teardown deletes the team first.
    resource_tracker.insert(0, added)
    # ``_original_agents`` is what build_save_payload serializes; keep the public
    # id list in step so a later to_dict()/is_modified check sees the change.
    team._original_agents.append(added)
    team.agents.append(added.id)
    team.save()
    assert set(_agent_ids(client.Agent.get(team.id).agents)) == {first.id, second.id, added.id}
    _assert_success(team.run("Reply with exactly the word OK."))

    team._original_agents = [agent for agent in team._original_agents if agent is not second]
    team.agents = [agent_id for agent_id in team.agents if agent_id != second.id]
    team.save()
    assert set(_agent_ids(client.Agent.get(team.id).agents)) == {first.id, added.id}


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_multiple_teams_with_shared_deployed_agent(client, resource_tracker):
    """One onboarded agent can back two teams, and both teams still run."""
    shared = client.Agent(name=_name("TA shared"), instructions="Answer briefly.")
    shared.save()
    resource_tracker.append(shared)

    team_1 = client.Agent(name=_name("TA shared 1"), instructions="Coordinate.", agents=[shared])
    team_2 = client.Agent(name=_name("TA shared 2"), instructions="Coordinate.", agents=[shared])
    team_1.save()
    resource_tracker.append(team_1)
    team_2.save()
    resource_tracker.append(team_2)

    assert client.Agent.get(shared.id).status == AssetStatus.ONBOARDED
    _assert_success(team_1.run("Reply with exactly the word OK."))
    _assert_success(team_2.run("Reply with exactly the word OK."))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_run_team_agent_with_expected_output(client, resource_tracker):
    """A run with an ``expected_output`` contract succeeds and answers."""
    sub = client.Agent(name=_name("TA expected sub"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA expected team"), instructions="Coordinate.", agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    _assert_success(team.run("Say OK.", expected_output="a single word"))


def test_draft_team_agent_update(client, resource_tracker):
    """A draft team can be saved, updated in place, and re-saved as a draft."""
    sub = client.Agent(name=_name("TA draft sub"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA draft team"), instructions="First instructions.", agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True, as_draft=True)
    resource_tracker.append(team)
    assert client.Agent.get(team.id).status == AssetStatus.DRAFT

    team.instructions = "Updated instructions."
    team.save(as_draft=True)
    assert client.Agent.get(team.id).instructions == "Updated instructions."


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_team_agent_evolve(client, resource_tracker):
    """The v2 twin of the legacy ``evolve_async``: a run carrying ``evolve`` succeeds.

    The v1 ``evolver_test.py`` was 100% skipped ("Evolver returning FAILED
    status" / "returning None"). v2 dropped the ``evolve_async`` wrapper in
    favour of the ``evolve`` run parameter, which the backend accepts.
    """
    import json

    sub = client.Agent(name=_name("TA evolve sub"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA evolve team"), instructions="Coordinate.", agents=[sub])
    resource_tracker.append(sub)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    _assert_success(team.run("Reply with exactly the word OK.", evolve=json.dumps({"toEvolve": True})))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_end2end(client, resource_tracker):
    """Create subagents, form a team, onboard it, and get a successful run."""
    first = client.Agent(name=_name("TA e2e 1"), instructions="Answer briefly.")
    second = client.Agent(name=_name("TA e2e 2"), instructions="Answer briefly.")
    team = client.Agent(name=_name("TA e2e team"), instructions="Coordinate.", agents=[first, second])
    resource_tracker.append(first)
    resource_tracker.append(second)
    team.save(save_subcomponents=True)
    resource_tracker.append(team)

    assert client.Agent.get(team.id).status == AssetStatus.ONBOARDED
    _assert_success(team.run("Reply with exactly the word OK."))


def test_fail_non_existent_llm(client):
    """An unknown ``llm`` id is rejected on save with a ``ResourceError``.

    v1 raised at ``TeamAgentFactory.create`` with a bespoke onboarding message;
    v2 defers the check to the backend ``save()`` call, so the twin asserts the
    v2 error instead of the v1 wording. Nothing is persisted, hence no tracker.
    """
    team = client.Agent(
        name=_name("TA bad llm"),
        instructions="Coordinate.",
        llm="non_existent_llm",
    )

    with pytest.raises(Exception, match="model.Invalid id"):
        team.save()
