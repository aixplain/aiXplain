"""Unit tests for propagating Model input overrides into Agent save payloads.

Covers :class:`~aixplain.v2.model.Model` bound to :class:`~aixplain.v2.agent.Agent`:
primary ``llm`` manifests and ``supervisor`` / ``planner`` (team wiring) emitted
as ``{id, parameters}`` dicts for ``supervisorId`` / ``plannerId``.
"""

from typing import Any, List, Optional

from unittest.mock import Mock

from aixplain.v2.agent import Agent
from aixplain.v2.model import Model, Parameter


def _agent_for_save_payload(**kwargs: Any) -> Agent:
    """Build an :class:`Agent` that can run ``build_save_payload()`` without a real client.

    ``context`` is excluded from the dataclass initializer but ``to_dict()`` expects
    the attribute to exist (see other v2 agent unit tests).
    """
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


class TestAgentLlmInputParametersInSavePayload:
    """Model input mutations must flow into ``build_save_payload()`` API shape."""

    def test_dot_notation_on_model_inputs_in_primary_llm_manifest(self):
        """``llm.inputs.reasoning_effort = ...`` maps to camelCase ``parameters``."""
        llm = _reasoning_model()
        llm.inputs.reasoning_effort = "low"

        agent = _agent_for_save_payload(name="n", description="d", llm=llm)
        payload = agent.build_save_payload()

        assert payload["llmId"] == {
            "id": llm.id,
            "parameters": {"reasoningEffort": "low"},
        }

    def test_bracket_notation_via_agent_llm_reference(self):
        """``agent.llm.inputs['reasoning_effort'] = ...`` updates the shared model."""
        llm = _reasoning_model()
        agent = _agent_for_save_payload(name="n", description="d", llm=llm)
        agent.llm.inputs["reasoning_effort"] = "medium"

        assert llm.inputs["reasoning_effort"].value == "medium"
        payload = agent.build_save_payload()
        assert payload["llmId"]["parameters"] == {"reasoningEffort": "medium"}

    def test_planner_supervisor_string_dict_and_model_refs(self):
        """``planner`` / ``supervisor`` become ``plannerId`` / ``supervisorId`` strings."""
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

        assert payload["supervisorId"] == {
            "id": "supervisor-id",
            "parameters": {"reasoningEffort": "low"},
        }
        assert payload["plannerId"] == {"id": mentalist_plain}
        assert "llms" not in payload

    def test_planner_dict_emitted_as_manifest(self):
        """A dict ``planner`` is emitted as ``{id, parameters}``."""
        agent = _agent_for_save_payload(
            name="a",
            description="d",
            planner={"id": "p1", "parameters": {"temperature": "0.2"}},
        )
        payload = agent.build_save_payload()
        assert payload["plannerId"] == {
            "id": "p1",
            "parameters": {"temperature": "0.2"},
        }

    def test_response_generator_string_dict_and_model_refs(self):
        """``response_generator`` becomes ``responseGeneratorId`` as ``{id, parameters?}``."""
        rg_model = _reasoning_model("response-gen-id")
        rg_model.inputs.reasoning_effort = "high"
        agent_from_model = _agent_for_save_payload(
            name="rg-model", description="d", response_generator=rg_model
        )
        payload = agent_from_model.build_save_payload()
        assert payload["responseGeneratorId"] == {
            "id": "response-gen-id",
            "parameters": {"reasoningEffort": "high"},
        }

        agent_from_string = _agent_for_save_payload(
            name="rg-str", description="d", response_generator="response-gen-id"
        )
        assert agent_from_string.build_save_payload()["responseGeneratorId"] == {
            "id": "response-gen-id"
        }

        agent_from_dict = _agent_for_save_payload(
            name="rg-dict",
            description="d",
            response_generator={"id": "rg2", "parameters": {"temperature": "0.5"}},
        )
        assert agent_from_dict.build_save_payload()["responseGeneratorId"] == {
            "id": "rg2",
            "parameters": {"temperature": "0.5"},
        }

    def test_response_generator_omitted_when_unset(self):
        """``responseGeneratorId`` is absent from the payload when ``response_generator`` is None."""
        agent = _agent_for_save_payload(name="n", description="d")
        payload = agent.build_save_payload()
        assert "responseGeneratorId" not in payload

    def test_multiple_non_none_parameters_are_merged(self):
        """Several set inputs appear together under ``parameters``."""
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

        assert payload["llmId"]["parameters"] == {
            "reasoningEffort": "high",
            "temperature": "0.5",
        }
