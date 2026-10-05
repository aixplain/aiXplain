"""v2 functional twins for the legacy ``tests/functional/team_agent`` scenarios (ENG-3689).

The v1 team-agent suite was deleted with v1 (PROD-2918) and only five v2 tests
touched teams at all. This module re-covers the removed scenarios against the
current backend so ``aix.Agent(..., agents=[...])`` (a "team" in v2) stays
exercised end to end:

* task definitions on a subagent (including ``dependencies``), and a team run
  that delegates to it;
* team instructions steering which subagent the team delegates to;
* the ``llm`` / ``planner`` / ``supervisor`` / ``response_generator`` role
  overrides and their parameters, persisted on a real team;
* the ``run_response_generation`` run parameter (acceptance only);
* the nested save chain, its statuses, and a run that reaches the subteam;
* mutating the subagent list of a saved team, then saving and running;
* one deployed agent shared by two teams, each delegating to it;
* a JSON ``expected_output`` contract, and draft updates.

Delegation is checked against ``response.data.steps``: the instructions,
tasks, nested, shared-agent, expected-output and end-to-end tests only pass if
the expected subagent shows up in the run's steps, so a team that answered on
its own fails them. No assertion matches exact LLM text.

The legacy ``evolve_async`` twin is intentionally not exercised: what a bare
``evolve`` run parameter triggers on the backend (and what it costs per CI run)
is unverified, so the module does not send it.

The naming convention follows ``test_agent_duplicate.py``: ``save()`` is the v2
deploy/onboard action. Each subagent is saved and registered with
``resource_tracker`` before the team that references it, so a failing team save
cannot leave an unsaved subagent in the tracker. Only the nested-chain test uses
``save(save_subcomponents=True)``, because the recursive save is what it covers.

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
                                 (plus the strict-xfail public-path twin
                                 ``test_add_agent_via_public_agents_list``)
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
"""

import json
import re
import time
import uuid
from typing import List

import pytest
from pydantic import BaseModel

from aixplain.v2 import AssetStatus
from aixplain.v2.exceptions import ResourceError

# Replaced by the shared assets fixture once ENG-3685 is in this branch.
#: A non-default LLM, so a role override cannot be confused with the platform default.
ALT_LLM = "698c87701239a117fd66b468"

#: Team instructions that make delegation mandatory, so a run's steps must name a subagent.
DELEGATE = "Always delegate the user's request to one of your agents and never answer it yourself."


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


def _assert_success(response):
    """Assert a completed successful run and return its output."""
    assert response is not None
    assert response.completed is True, f"run did not complete: {response.status}"
    assert response.status.upper() == "SUCCESS", f"run failed: {response.status}"
    data = getattr(response, "data", None)
    output = getattr(data, "output", None) or (data if isinstance(data, str) else "")
    assert output, "expected a non-empty run output"
    return output


def _steps(response) -> list:
    """The ``data.steps`` list of a run, whether ``data`` decoded to an object or a dict."""
    data = getattr(response, "data", None)
    if isinstance(data, dict):
        return data.get("steps") or []
    return getattr(data, "steps", None) or []


def _normalize(value) -> str:
    """Lower-case alphanumerics only, so a backend that re-spaces or re-cases a name still matches."""
    return re.sub(r"[^0-9a-z]", "", str(value).lower())


def _step_identifiers(response) -> List[str]:
    """Every agent/unit name and id the run's steps mention, normalized.

    A step names its acting agent under ``agent`` (a ``{id, name}`` dict or a
    plain string) and the asset it invoked under ``unit``. Both are collected
    because a supervisor's call into a subagent can surface either way.
    """
    identifiers = []
    for step in _steps(response):
        if not isinstance(step, dict):
            continue
        for key in ("agent", "agent_name", "unit"):
            ref = step.get(key)
            if isinstance(ref, dict):
                identifiers.extend(ref.get(field) for field in ("id", "name", "agent_name"))
            else:
                identifiers.append(ref)
    return [_normalize(identifier) for identifier in identifiers if identifier]


def _was_called(response, agent) -> bool:
    """Whether ``agent`` (by name or id) appears in the run's steps."""
    wanted = [_normalize(value) for value in (agent.name, agent.id) if value]
    return any(target in identifier for identifier in _step_identifiers(response) for target in wanted)


def _assert_called(response, *agents) -> None:
    """Assert each of ``agents`` took part in the run, per ``response.data.steps``."""
    for agent in agents:
        assert _was_called(response, agent), (
            f"expected {agent.name!r} ({agent.id}) in the run steps, saw {sorted(set(_step_identifiers(response)))}"
        )


def _assert_role(ref, model_id: str, parameters: dict) -> None:
    """A fetched role ref carries the expected model id and parameters (a ``name`` may ride along)."""
    assert isinstance(ref, dict), f"expected a role ref dict, got {ref!r}"
    assert ref.get("id") == model_id
    assert ref.get("parameters") == parameters


def _json_output(output):
    """Decode a JSON run output that may arrive parsed, as a string, or inside a fenced block."""
    if isinstance(output, (dict, list)):
        return output
    try:
        return json.loads(output)
    except (TypeError, ValueError):
        fenced = re.search(r"```(?:json)?\s*(.*?)```", str(output), re.DOTALL)
        assert fenced, f"run output is not JSON: {output!r}"
        return json.loads(fenced.group(1))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_team_agent_with_instructions(client, resource_tracker):
    """Team instructions persist and steer delegation to the named subagent only."""
    preferred = client.Agent(
        name=_name("TA-pick"), description="Answers general questions.", instructions="Answer briefly."
    )
    preferred.save()
    resource_tracker.append(preferred)
    other = client.Agent(
        name=_name("TA-skip"), description="Answers general questions.", instructions="Answer briefly."
    )
    other.save()
    resource_tracker.append(other)

    instructions = (
        f"Delegate every request to the agent named '{preferred.name}' and to no other agent. "
        f"Never call '{other.name}'."
    )
    team = client.Agent(name=_name("TA-team"), instructions=instructions, agents=[preferred, other])
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert fetched.instructions == instructions
    assert set(_agent_ids(fetched.agents)) == {preferred.id, other.id}

    response = fetched.run("What is the capital of France?")
    _assert_success(response)
    _assert_called(response, preferred)
    assert not _was_called(response, other), f"instructions excluded {other.name!r}, yet the team called it"


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_team_agent_tasks(client, resource_tracker):
    """Subagent task definitions persist, and a team run delegates to that subagent."""
    first = "Gather the facts"
    sub = client.Agent(
        name=_name("TA-task-sub"),
        description="Researches a topic and summarizes it.",
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
    sub.save()
    resource_tracker.append(sub)
    team = client.Agent(name=_name("TA-task-team"), instructions=DELEGATE, agents=[sub])
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(sub.id)
    assert [task.name for task in fetched.tasks] == [first, "Write the summary"]
    assert fetched.tasks[0].expected_output == "facts"
    assert fetched.tasks[1].dependencies == [first]

    response = team.run("Gather two facts about the Eiffel Tower, then summarize them in one sentence.")
    _assert_success(response)
    _assert_called(response, sub)


def test_team_agent_llm_parameter_preservation(client, resource_tracker):
    """Supervisor and planner (the v1 "mentalist") parameters on a real team survive save/get."""
    sub = client.Agent(name=_name("TA-llm-sub"), instructions="Answer briefly.")
    sub.save()
    resource_tracker.append(sub)

    model_id = client.Agent.DEFAULT_LLM
    team = client.Agent(
        name=_name("TA-llm-team"),
        instructions="Coordinate.",
        agents=[sub],
        supervisor={"id": model_id, "parameters": {"temperature": "0.1"}},
        planner={"id": model_id, "parameters": {"temperature": "0.3"}},
    )
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert _agent_ids(fetched.agents) == [sub.id]
    _assert_role(fetched.supervisor, model_id, {"temperature": "0.1"})
    _assert_role(fetched.planner, model_id, {"temperature": "0.3"})


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_role_llm_overrides_persisted_and_used(client, resource_tracker):
    """``planner`` / ``supervisor`` / ``response_generator`` overrides persist, and the team runs with them.

    The run-payload half (``modelParameters``) is pure SDK serialization and is
    covered by ``TestRoleOverridesReachRunPayload`` in
    ``tests/unit/v2/test_agent_llm_input_parameters.py``.
    """
    sub = client.Agent(name=_name("TA-roles-sub"), instructions="Answer briefly.")
    sub.save()
    resource_tracker.append(sub)
    # ALT_LLM (Claude Opus) is switched to the cheaper NON_DEFAULT_LLM when the shared
    # assets fixture lands; any non-default model proves the override.
    team = client.Agent(
        name=_name("TA-roles-team"),
        instructions="Coordinate the subagents.",
        agents=[sub],
        planner={"id": ALT_LLM, "parameters": {"temperature": "0.1"}},
        supervisor={"id": ALT_LLM, "parameters": {"temperature": "0.2"}},
        response_generator={"id": ALT_LLM, "parameters": {"temperature": "0.4"}},
    )
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    _assert_role(fetched.planner, ALT_LLM, {"temperature": "0.1"})
    _assert_role(fetched.supervisor, ALT_LLM, {"temperature": "0.2"})
    _assert_role(fetched.response_generator, ALT_LLM, {"temperature": "0.4"})

    _assert_success(fetched.run("Reply with exactly the word OK."))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_run_response_generation_accepted(client, resource_tracker):
    """A run with ``run_response_generation=True`` is accepted and succeeds.

    Only acceptance is verified: the SDK exposes nothing on the response that
    distinguishes a run with response generation from one without, so this test
    cannot prove the backend honoured the flag.
    """
    sub = client.Agent(name=_name("TA-rrg-sub"), instructions="Answer briefly.")
    sub.save()
    resource_tracker.append(sub)
    team = client.Agent(name=_name("TA-rrg-team"), instructions="Coordinate.", agents=[sub])
    team.save()
    resource_tracker.append(team)

    _assert_success(team.run("Reply with exactly the word OK.", run_response_generation=True))


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_nested_deployment_chain(client, resource_tracker):
    """Saving a team recursively onboards the whole chain, and a run reaches the subteam."""
    leaf = client.Agent(name=_name("TA-leaf"), description="Answers questions.", instructions="Answer briefly.")
    mid = client.Agent(name=_name("TA-mid"), description="Answers questions.", instructions=DELEGATE, agents=[leaf])
    top = client.Agent(name=_name("TA-top"), instructions=DELEGATE, agents=[mid])
    try:
        top.save(save_subcomponents=True)
    finally:
        # Register only what the recursive save actually created, leaf first, so
        # a failed save neither leaks a saved member nor reports an unsaved one
        # as orphaned; newest-first teardown then deletes top -> mid -> leaf.
        for agent in (leaf, mid, top):
            if agent.id:
                resource_tracker.append(agent)

    assert leaf.id and mid.id and top.id
    for agent in (leaf, mid, top):
        assert client.Agent.get(agent.id).status == AssetStatus.ONBOARDED

    response = top.run("What is the capital of France?")
    _assert_success(response)
    _assert_called(response, mid)


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_add_remove_agents_from_team_agent(client, resource_tracker):
    """A saved team's subagent list can be extended, saved, run, then shrunk.

    Edits go through the private ``_original_agents`` list because the public
    ``team.agents`` edit is dropped on save; see
    ``test_add_agent_via_public_agents_list``.
    """
    first = client.Agent(name=_name("TA-keep"), instructions="Answer A.")
    first.save()
    resource_tracker.append(first)
    second = client.Agent(name=_name("TA-drop"), instructions="Answer B.")
    second.save()
    resource_tracker.append(second)
    added = client.Agent(name=_name("TA-added"), instructions="Answer C.")
    added.save()
    resource_tracker.append(added)

    team = client.Agent(name=_name("TA-mutate-team"), instructions="Coordinate.", agents=[first, second])
    team.save()
    resource_tracker.append(team)

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


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "SDK bug: Agent.build_save_payload reads _original_agents, so public edits to agents "
        "are dropped on save — ticket to be filed"
    ),
)
def test_add_agent_via_public_agents_list(client, resource_tracker):
    """Appending to the public ``team.agents`` list, then saving, persists the new member."""
    first = client.Agent(name=_name("TA-pub-keep"), instructions="Answer A.")
    first.save()
    resource_tracker.append(first)
    added = client.Agent(name=_name("TA-pub-added"), instructions="Answer C.")
    added.save()
    resource_tracker.append(added)

    team = client.Agent(name=_name("TA-pub-team"), instructions="Coordinate.", agents=[first])
    team.save()
    resource_tracker.append(team)

    team.agents.append(added.id)
    team.save()
    assert set(_agent_ids(client.Agent.get(team.id).agents)) == {first.id, added.id}


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_multiple_teams_with_shared_deployed_agent(client, resource_tracker):
    """One onboarded agent can back two teams, and each team delegates to it."""
    shared = client.Agent(name=_name("TA-shared"), description="Answers questions.", instructions="Answer briefly.")
    shared.save()
    resource_tracker.append(shared)

    team_1 = client.Agent(name=_name("TA-shared-1"), instructions=DELEGATE, agents=[shared])
    team_1.save()
    resource_tracker.append(team_1)
    team_2 = client.Agent(name=_name("TA-shared-2"), instructions=DELEGATE, agents=[shared])
    team_2.save()
    resource_tracker.append(team_2)

    assert client.Agent.get(shared.id).status == AssetStatus.ONBOARDED
    for team in (team_1, team_2):
        response = team.run("What is the capital of France?")
        _assert_success(response)
        _assert_called(response, shared)


class _Person(BaseModel):
    name: str
    age: int


class _People(BaseModel):
    result: List[_Person]


#: The roster the expected-output subagent answers from.
_ROSTER = {"Ana": 19, "Bruno": 34, "Carla": 45, "Davi": 28}


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_run_team_agent_with_expected_output(client, resource_tracker):
    """A team saved with a JSON ``expected_output`` model answers in that structure.

    ``output_format`` / ``expected_output`` are agent attributes: they persist on
    save and every run sends them as ``executionParams.outputFormat`` /
    ``executionParams.expectedOutput``. They are not run kwargs.
    """
    roster = "\n".join(f"- {name}: {age} years old" for name, age in _ROSTER.items())
    sub = client.Agent(
        name=_name("TA-expected-sub"),
        description="Knows the ages of the people on the roster.",
        instructions=f"Answer questions using only this roster:\n{roster}",
    )
    sub.save()
    resource_tracker.append(sub)
    team = client.Agent(
        name=_name("TA-expected-team"),
        instructions=DELEGATE,
        agents=[sub],
        output_format="json",
        expected_output=_People,
    )
    team.save()
    resource_tracker.append(team)

    fetched = client.Agent.get(team.id)
    assert fetched.output_format == "json"
    assert fetched.expected_output, "the expected_output contract was not persisted"

    response = team.run("Who on the roster is older than 30? Give each person's name and age.")
    people = _People.model_validate(_json_output(_assert_success(response)))
    assert people.result, "expected at least one person in the structured output"
    assert {person.name for person in people.result} <= set(_ROSTER)
    _assert_called(response, sub)


def test_draft_team_agent_update(client, resource_tracker):
    """A draft team can be saved, updated in place, and re-saved as a draft."""
    sub = client.Agent(name=_name("TA-draft-sub"), instructions="Answer briefly.")
    sub.save()
    resource_tracker.append(sub)
    team = client.Agent(name=_name("TA-draft-team"), instructions="First instructions.", agents=[sub])
    team.save(as_draft=True)
    resource_tracker.append(team)
    assert client.Agent.get(team.id).status == AssetStatus.DRAFT

    team.instructions = "Updated instructions."
    team.save(as_draft=True)
    fetched = client.Agent.get(team.id)
    assert fetched.instructions == "Updated instructions."
    assert fetched.status == AssetStatus.DRAFT


@pytest.mark.flaky(reruns=2, reruns_delay=5)
def test_end2end(client, resource_tracker):
    """Create subagents, form a team, onboard it, and get a run that delegates."""
    first = client.Agent(name=_name("TA-e2e-1"), description="Answers questions.", instructions="Answer briefly.")
    first.save()
    resource_tracker.append(first)
    second = client.Agent(name=_name("TA-e2e-2"), description="Answers questions.", instructions="Answer briefly.")
    second.save()
    resource_tracker.append(second)
    team = client.Agent(name=_name("TA-e2e-team"), instructions=DELEGATE, agents=[first, second])
    team.save()
    resource_tracker.append(team)

    assert client.Agent.get(team.id).status == AssetStatus.ONBOARDED
    response = team.run("What is the capital of France?")
    _assert_success(response)
    assert _was_called(response, first) or _was_called(response, second), (
        f"expected a subagent in the run steps, saw {sorted(set(_step_identifiers(response)))}"
    )


def test_fail_non_existent_llm(client, resource_tracker):
    """An unknown ``llm`` id is rejected on save with a ``ResourceError``.

    v1 raised at ``TeamAgentFactory.create`` with a bespoke onboarding message;
    v2 defers the check to the backend ``save()`` call, so the twin asserts the
    v2 error instead of the v1 wording. The agent is registered if the backend
    ever accepts the id, so a regression cannot leak it.
    """
    team = client.Agent(
        name=_name("TA-bad-llm"),
        instructions="Coordinate.",
        llm="non_existent_llm",
    )
    try:
        with pytest.raises(ResourceError, match=re.escape("model.Invalid id")):
            team.save()
    finally:
        if team.id:
            resource_tracker.append(team)
