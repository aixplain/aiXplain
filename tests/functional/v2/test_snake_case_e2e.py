"""End-to-end tests proving the camelCase → snake_case field renames work against the real backend.

Strategy:
- Persistable fields: set value with snake_case name → save → fetch → assert it matches.
- Runtime-only kwargs: call agent.run() with the snake_case kwarg → assert backend accepts it.
"""

import time

import pytest

from aixplain.v2.integration import Input, Action


class TestToolDictFieldsRoundTrip:
    """as_tool() produces snake_case keys; save must convert them so the backend stores the value."""

    def test_asset_id_round_trips_through_backend(self, client):
        """Set asset_id (renamed from assetId) via as_tool(), save agent, fetch back, compare."""
        model = client.Model.get("6895d6d1d50c89537c1cf237")  # GPT-5 Mini
        tool_dict = model.as_tool()

        # Value we're about to send (snake_case key)
        sent_asset_id = tool_dict["asset_id"]
        assert sent_asset_id == model.id

        # Save an agent carrying this tool
        agent = client.Agent(
            name=f"asset_id roundtrip {int(time.time())}",
            instructions="test",
            tools=[model],
        )
        agent.save()

        try:
            fetched = client.Agent.get(agent.id)
            saved_tool = fetched.tools[0]  # raw dict from API

            # Backend resolves asset_id into the tool's "id" field
            assert saved_tool["id"] == sent_asset_id, (
                f"asset_id we sent ({sent_asset_id}) != id backend returned ({saved_tool.get('id')})"
            )
        finally:
            try:
                agent.delete()
            except Exception:
                pass

    def test_allow_multi_and_supports_variables_round_trip(self, client):
        """get_parameters() returns allow_multi / supports_variables; verify values survive save."""
        model = client.Model.get("6895d6d1d50c89537c1cf237")
        params = model.get_parameters()
        if not params:
            pytest.skip("Model has no parameters")

        sample = params[0]
        sent_allow_multi = sample["allow_multi"]
        sent_supports_variables = sample["supports_variables"]

        # Save an agent with this model tool (params embedded in the payload)
        agent = client.Agent(
            name=f"params roundtrip {int(time.time())}",
            instructions="test",
            tools=[model],
        )
        agent.save()

        try:
            fetched = client.Agent.get(agent.id)
            saved_tool = fetched.tools[0]

            saved_params = saved_tool.get("parameters", [])
            assert saved_params, "Backend should return the tool parameters we sent"

            saved_sample = saved_params[0]
            assert saved_sample["allow_multi"] == sent_allow_multi, (
                f"allow_multi we sent ({sent_allow_multi}) "
                f"!= allow_multi backend returned ({saved_sample.get('allow_multi')})"
            )
            assert saved_sample["supports_variables"] == sent_supports_variables, (
                f"supports_variables we sent ({sent_supports_variables}) "
                f"!= supports_variables backend returned ({saved_sample.get('supports_variables')})"
            )
        finally:
            try:
                agent.delete()
            except Exception:
                pass


class TestInputActionFieldsRoundTrip:
    """Input / Action fields are read from the backend; verify snake_case ↔ camelCase mapping."""

    SCRIPT_INTEGRATION_ID = "686432941223092cb4294d3f"

    def test_input_fields_survive_serialization_round_trip(self, client):
        """Fetch real Input from API, read snake_case attrs, to_dict → from_dict, values match."""
        integration = client.Integration.get(self.SCRIPT_INTEGRATION_ID)
        if not integration.actions_available:
            pytest.skip("Integration has no actions available")

        actions = integration.list_actions()
        if not actions:
            pytest.skip("No actions returned")

        action_name = actions[0].name or actions[0].slug
        if not action_name:
            pytest.skip("First action has no name")

        input_actions = integration.list_inputs(action_name)
        if not input_actions or not input_actions[0].inputs:
            pytest.skip("No inputs available for this action")

        original = input_actions[0].inputs[0]

        # Read values via new snake_case names
        orig_default_value = original.default_value
        orig_allow_multi = original.allow_multi
        orig_supports_variables = original.supports_variables
        orig_available_options = original.available_options

        # Serialize (snake_case → camelCase JSON) then deserialize (camelCase JSON → snake_case)
        restored = Input.from_dict(original.to_dict())

        assert restored.default_value == orig_default_value
        assert restored.allow_multi == orig_allow_multi
        assert restored.supports_variables == orig_supports_variables
        assert restored.available_options == orig_available_options

    def test_action_display_name_survives_round_trip(self, client):
        """Fetch real Action from API, read display_name, to_dict → from_dict, value matches."""
        integration = client.Integration.get(self.SCRIPT_INTEGRATION_ID)
        if not integration.actions_available:
            pytest.skip("Integration has no actions available")

        actions = integration.list_actions()
        if not actions:
            pytest.skip("No actions returned")

        original = actions[0]
        orig_display_name = original.display_name

        restored = Action.from_dict(original.to_dict())
        assert restored.display_name == orig_display_name


# ---------------------------------------------------------------------------
# 3. AgentRunParams – runtime kwargs accepted by the backend
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_agent(client):
    """Ephemeral agent for run-param tests."""
    agent = client.Agent(
        name=f"snake_case run params {int(time.time())}",
        instructions="Reply with the single word 'pong' regardless of input.",
    )
    agent.save()
    yield agent
    try:
        agent.delete()
    except Exception:
        pass


class TestAgentRunParamsKwargs:
    """Renamed AgentRunParams kwargs are accepted by the backend.

    These are runtime-only (not persisted), so the test is:
    call agent.run() with the snake_case kwarg → backend accepts and responds.
    """

    def test_session_id(self, client, test_agent):
        """session_id (renamed from sessionId) is sent to the backend and reflected in the response."""
        agent = client.Agent.get(test_agent.id)
        sid = agent.generate_session_id()

        response = agent.run("ping", session_id=sid)

        assert response.status == "SUCCESS"
        assert response.data.session_id is not None
        assert sid in response.data.session_id

    def test_execution_params(self, client, test_agent):
        """execution_params (renamed from executionParams) reaches the backend.

        We prove the backend honours it by setting maxTokens=1, which forces a
        token-limit error — that error would not occur if the param were ignored.
        """
        from aixplain.v2.exceptions import APIError

        agent = client.Agent.get(test_agent.id)

        with pytest.raises(APIError, match="(?i)max.?token"):
            agent.run(
                "ping",
                execution_params={"maxTokens": 1, "maxIterations": 3, "outputFormat": "text"},
            )

    def test_run_response_generation(self, client, test_agent):
        """run_response_generation (renamed from runResponseGeneration) is accepted by the backend."""
        agent = client.Agent.get(test_agent.id)

        response = agent.run("ping", run_response_generation=False)

        assert response.status == "SUCCESS"

    def test_allow_history_and_session_id(self, client, test_agent):
        """allow_history_and_session_id (renamed from allowHistoryAndSessionId) is accepted."""
        agent = client.Agent.get(test_agent.id)
        sid = agent.generate_session_id()

        response = agent.run(
            "ping",
            session_id=sid,
            history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
            allow_history_and_session_id=True,
        )

        assert response.status == "SUCCESS"
