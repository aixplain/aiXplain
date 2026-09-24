"""Unit tests for propagating Model input overrides into Agent save payloads.

Save payloads use the V2 ``AgentModelInput`` nested shape: each role is
emitted under its own key (``model`` / ``supervisor`` / ``planner`` /
``responder``) with ``parameters`` as a ``[{name, value}]`` list (the
platform's ``NameValueInput`` shape — keeps the GraphQL schema agnostic to
specific parameter names).
"""

import json
from typing import Any, List, Optional

from unittest.mock import Mock

from aixplain.v2.agent import Agent
from aixplain.v2.model import Model, Parameter


def _agent_for_save_payload(**kwargs: Any) -> Agent:
    """Build an :class:`Agent` that can run ``build_save_payload()`` without a real client."""
    agent = Agent(**kwargs)
    agent.context = Mock()
    return agent


def _reasoning_model(model_id: str = "test-model-1", *, params: Optional[List[Parameter]] = None) -> Model:
    """Build a minimal Model; by default only ``reasoning_effort`` exists."""
    model = Model.__new__(Model)
    model.id = model_id
    model.name = "Test LLM"
    model.params = params or [
        Parameter(
            name="reasoning_effort",
            required=False,
            data_type="text",
            data_sub_type="text",
            default_values=[],
        ),
    ]
    model.__post_init__()
    model.context = Mock()
    return model


def _params_as_dict(parameters: List[dict]) -> dict:
    """Flatten ``[{name, value}]`` to ``{name: value}`` for ergonomic assertions."""
    return {item["name"]: item["value"] for item in parameters}


class TestAgentLlmInputParametersInSavePayload:
    """Model input mutations must flow into ``build_save_payload()`` API shape."""

    def test_dot_notation_on_model_inputs_in_primary_llm_manifest(self):
        """``llm.inputs.reasoning_effort = ...`` maps to camelCase ``parameters``."""
        llm = _reasoning_model()
        llm.inputs.reasoning_effort = "low"

        agent = _agent_for_save_payload(name="n", description="d", llm=llm)
        payload = agent.build_save_payload()

        assert payload["model"] == {
            "id": llm.id,
            "parameters": [{"name": "reasoningEffort", "value": "low"}],
        }

    def test_bracket_notation_via_agent_llm_reference(self):
        """``agent.llm.inputs['reasoning_effort'] = ...`` updates the shared model."""
        llm = _reasoning_model()
        agent = _agent_for_save_payload(name="n", description="d", llm=llm)
        agent.llm.inputs["reasoning_effort"] = "medium"

        assert llm.inputs["reasoning_effort"].value == "medium"
        payload = agent.build_save_payload()
        assert payload["model"]["parameters"] == [{"name": "reasoningEffort", "value": "medium"}]

    def test_planner_supervisor_string_dict_and_model_refs(self):
        """``planner`` / ``supervisor`` become ``planner`` / ``supervisor`` manifests."""
        supervisor = _reasoning_model("supervisor-id")
        supervisor.inputs.reasoning_effort = "low"
        mentalist_plain = "mentalist-model-id"

        agent = _agent_for_save_payload(
            name="team",
            description="team",
            supervisor=supervisor,
            planner=mentalist_plain,
        )
        payload = agent.build_save_payload()

        assert payload["supervisor"] == {
            "id": "supervisor-id",
            "parameters": [{"name": "reasoningEffort", "value": "low"}],
        }
        assert payload["planner"] == {"id": mentalist_plain}
        # Legacy top-level keys must not leak into the payload.
        for legacy_key in ("llmId", "supervisorId", "plannerId", "responseGeneratorId", "llms"):
            assert legacy_key not in payload

    def test_planner_dict_emitted_as_manifest(self):
        """A dict ``planner`` is emitted as ``{id, parameters: [{name,value}]}``."""
        agent = _agent_for_save_payload(
            name="a",
            description="d",
            planner={"id": "p1", "parameters": {"temperature": "0.2"}},
        )
        payload = agent.build_save_payload()
        assert payload["planner"] == {
            "id": "p1",
            "parameters": [{"name": "temperature", "value": "0.2"}],
        }

    def test_response_generator_maps_to_responder_key(self):
        """``response_generator`` is emitted under the wire key ``responder``."""
        rg_model = _reasoning_model("response-gen-id")
        rg_model.inputs.reasoning_effort = "high"

        # Model ref
        payload = _agent_for_save_payload(
            name="rg-model", description="d", response_generator=rg_model
        ).build_save_payload()
        assert payload["responder"] == {
            "id": "response-gen-id",
            "parameters": [{"name": "reasoningEffort", "value": "high"}],
        }
        assert "responseGeneratorId" not in payload

        # String ref
        payload = _agent_for_save_payload(
            name="rg-str", description="d", response_generator="response-gen-id"
        ).build_save_payload()
        assert payload["responder"] == {"id": "response-gen-id"}

        # Dict ref (parameter dict input)
        payload = _agent_for_save_payload(
            name="rg-dict",
            description="d",
            response_generator={"id": "rg2", "parameters": {"temperature": "0.5"}},
        ).build_save_payload()
        assert payload["responder"] == {
            "id": "rg2",
            "parameters": [{"name": "temperature", "value": "0.5"}],
        }

    def test_response_generator_omitted_when_unset(self):
        """``responder`` is absent from the payload when ``response_generator`` is None."""
        agent = _agent_for_save_payload(name="n", description="d")
        payload = agent.build_save_payload()
        assert "responder" not in payload
        assert "responseGeneratorId" not in payload

    def test_multiple_non_none_parameters_are_merged(self):
        """Several set inputs appear together under ``parameters`` (list shape)."""
        llm = _reasoning_model(
            params=[
                Parameter(
                    name="reasoning_effort",
                    required=False,
                    data_type="text",
                    data_sub_type="text",
                    default_values=[],
                ),
                Parameter(
                    name="temperature",
                    required=False,
                    data_type="text",
                    data_sub_type="text",
                    default_values=[{"value": "1"}],
                ),
            ],
        )
        llm.inputs.reasoning_effort = "high"
        llm.inputs["temperature"] = "0.5"

        agent = _agent_for_save_payload(name="n", description="d", llm=llm)
        payload = agent.build_save_payload()

        # Order isn't part of the contract; compare as a name→value map.
        assert _params_as_dict(payload["model"]["parameters"]) == {
            "reasoningEffort": "high",
            "temperature": "0.5",
        }

    def test_save_payload_drops_legacy_top_level_role_ids(self):
        """Make sure none of the legacy top-level keys appear on save."""
        agent = _agent_for_save_payload(
            name="n",
            description="d",
            llm="llm-id",
            supervisor="sup-id",
            planner="planner-id",
            response_generator="rg-id",
        )
        payload = agent.build_save_payload()
        for legacy_key in (
            "llmId",
            "supervisorId",
            "plannerId",
            "responseGeneratorId",
        ):
            assert legacy_key not in payload


class TestRoleRefsSurviveToDict:
    """``to_dict()`` must round-trip role refs, not silently drop them.

    ``to_dict()`` is the public dump API (and what experiment / provenance
    snapshots capture). The role fields are ``exclude=lambda x: True`` so the
    *save* path can emit the nested ``AgentModelInput`` shape by hand — but that
    marker also stripped them from every ``to_dict()``, so
    ``Agent.from_dict(agent.to_dict())`` silently reset ``llm`` to
    ``Agent.DEFAULT_LLM`` and the other three roles to ``None``.
    """

    def test_string_role_refs_round_trip_unchanged(self):
        """All four roles survive a dump/load as the same string ids."""
        agent = Agent(
            name="n",
            description="d",
            llm="llm-id",
            supervisor="sup-id",
            planner="planner-id",
            response_generator="rg-id",
        )

        restored = Agent.from_dict(agent.to_dict())

        assert restored.llm == "llm-id"
        assert restored.supervisor == "sup-id"
        assert restored.planner == "planner-id"
        assert restored.response_generator == "rg-id"

    def test_dumped_llm_is_not_silently_replaced_by_the_sdk_default(self):
        """The regression that motivated this: a chosen llm came back as the default."""
        agent = Agent(name="n", description="d", llm="a-deliberately-chosen-llm")

        dumped = agent.to_dict()

        assert dumped["model"] == "a-deliberately-chosen-llm"
        assert Agent.from_dict(dumped).llm != Agent.DEFAULT_LLM

    def test_model_role_ref_is_serialized_not_recursed_into(self):
        """A ``Model`` ref dumps as the id/parameters manifest (and stays JSON-safe)."""
        llm = _reasoning_model("model-ref-1")
        llm.inputs.reasoning_effort = "low"
        agent = Agent(name="n", description="d", llm=llm)

        dumped = agent.to_dict()

        assert dumped["model"]["id"] == "model-ref-1"
        assert _params_as_dict(dumped["model"]["parameters"]) == {"reasoningEffort": "low"}
        # Parameters survive the round trip, flattened for in-Python access.
        assert Agent.from_dict(dumped).llm == {
            "id": "model-ref-1",
            "parameters": {"reasoningEffort": "low"},
        }

    def test_unset_roles_are_omitted(self):
        """Roles left unset stay out of the dump; only ``llm`` has a default."""
        agent = Agent(name="n", description="d")

        dumped = agent.to_dict()

        assert dumped["model"] == Agent.DEFAULT_LLM
        for absent in ("supervisor", "planner", "responder"):
            assert absent not in dumped

    def test_role_change_marks_the_agent_modified(self):
        """``is_modified`` reads ``to_dict()``, so a swapped llm now registers.

        It previously did not: on a draft agent that made ``before_run`` skip the
        implicit save, so the run silently used the *old* model — the same class
        of silent model loss as the dump/load bug above.
        """
        agent = Agent.from_dict({"id": "a1", "name": "n", "description": "d", "model": {"id": "llm-1"}})
        agent._update_saved_state()
        assert agent.is_modified is False

        agent.llm = "llm-2"

        assert agent.is_modified is True

    def test_to_dict_is_json_serializable(self):
        """A dump is only useful if it survives ``json.dumps`` (``Model`` refs included)."""
        agent = Agent(name="n", description="d", llm=_reasoning_model("m-json"), supervisor="sup-id")

        reloaded = json.loads(json.dumps(agent.to_dict()))

        assert reloaded["model"]["id"] == "m-json"
        assert reloaded["supervisor"] == "sup-id"
