"""Unit tests for propagating Model input overrides into Agent save payloads.

Covers the workflows exercised manually when tuning LLM parameters on a
:class:`~aixplain.v2.model.Model` and attaching that model to an
:class:`~aixplain.v2.agent.Agent` (primary ``llm`` or team ``llms``): values
set via ``inputs.reasoning_effort = ...`` or ``inputs["reasoning_effort"] = ...``
must appear under API ``parameters`` (camelCase keys) when building the save
payload.
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
    """Build a minimal Model; by default only ``reasoning_effort`` exists (no implicit defaults in payload)."""
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

        assert payload["model"] == {
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
        assert payload["model"]["parameters"] == {"reasoningEffort": "medium"}

    def test_team_llms_mixed_model_and_string_ids(self):
        """Team ``llms`` carries parameters only for embedded :class:`Model` refs."""
        supervisor = _reasoning_model("supervisor-id")
        supervisor.inputs.reasoning_effort = "low"
        mentalist_id = "mentalist-model-id"

        agent = _agent_for_save_payload(
            name="team",
            description="team",
            llms={
                "supervisor": supervisor,
                "mentalist": mentalist_id,
            },
        )
        payload = agent.build_save_payload()

        assert payload["llms"]["supervisor"] == {
            "id": "supervisor-id",
            "parameters": {"reasoningEffort": "low"},
        }
        assert payload["llms"]["mentalist"] == {"id": mentalist_id}

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

        assert payload["model"]["parameters"] == {
            "reasoningEffort": "high",
            "temperature": "0.5",
        }
