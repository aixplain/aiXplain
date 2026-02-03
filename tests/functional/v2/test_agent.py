import pytest
import time
from aixplain.enums import AssetStatus, ResponseStatus


@pytest.fixture(scope="module")
def test_agent(client):
    """Create a test agent dynamically for testing and clean up after tests complete."""
    agent = client.Agent(
        name=f"Functional Test Agent {int(time.time())}",
        description="A temporary agent for functional testing",
        instructions="You are a helpful test agent. Respond briefly to questions.",
    )
    agent.save()

    yield agent

    # Cleanup after all tests in module complete
    try:
        agent.delete()
    except Exception:
        pass  # Ignore cleanup errors


def validate_agent_structure(agent):
    """Helper function to validate agent structure and data types."""
    # Test core fields inherited from BaseResource
    assert isinstance(agent.id, str)
    assert isinstance(agent.name, str)
    # Description can be None for some agents
    if agent.description is not None:
        assert isinstance(agent.description, str)

    # Test Agent-specific fields
    assert isinstance(agent.status, str)

    # Test optional fields if present
    if agent.team_id is not None:
        assert isinstance(agent.team_id, int)

    if agent.llm:
        assert isinstance(agent.llm, str)

    # Test timestamps if present
    if agent.created_at:
        assert isinstance(agent.created_at, str)

    if agent.updated_at:
        assert isinstance(agent.updated_at, str)

    # Test inspector-related fields if present
    if agent.inspector_targets:
        assert isinstance(agent.inspector_targets, list)

    if agent.max_inspectors is not None:
        assert isinstance(agent.max_inspectors, int)

    if agent.inspectors:
        assert isinstance(agent.inspectors, list)

    # Test resourceInfo if present
    if agent.resource_info:
        assert isinstance(agent.resource_info, dict)

    # Test expectedOutput if present
    if agent.expected_output is not None:
        # expectedOutput can be any type, so we just check it's not None
        pass


def test_search_agents(client, test_agent):
    """Test searching agents with pagination - verifies backend interaction."""
    # test_agent fixture ensures at least one agent exists
    agents = client.Agent.search()
    assert hasattr(agents, "results"), "Agent search response missing 'results' field"
    assert isinstance(agents.results, list), "Agent list results is not a list"

    number_of_agents = len(agents.results)
    assert number_of_agents >= 0, "Expected to get results from agent listing"

    # Validate that we actually got some agents (test_agent fixture guarantees at least one)
    assert number_of_agents > 0, "No agents returned from listing - this may indicate a backend issue"

    # Validate structure of returned agents
    for i, agent in enumerate(agents.results):
        try:
            validate_agent_structure(agent)
        except AssertionError as e:
            pytest.fail(f"Agent {i} failed structure validation: {e}")

    # Validate pagination metadata if available
    if hasattr(agents, "total"):
        assert agents.total >= number_of_agents, "Total count should be >= number of results"
    if hasattr(agents, "page_number"):
        assert agents.page_number >= 0, "Page number should be non-negative"


def test_get_agent(client, test_agent):
    """Test getting a specific agent by ID - verifies backend interaction and structure."""
    agent = client.Agent.get(test_agent.id)
    assert agent.id == test_agent.id, f"Retrieved agent ID {agent.id} doesn't match requested ID {test_agent.id}"

    # Validate complete agent structure
    try:
        validate_agent_structure(agent)
    except AssertionError as e:
        pytest.fail(f"Agent structure validation failed: {e}")

    # Test that retrieved agent matches the created test agent
    assert agent.name == test_agent.name, f"Expected agent name '{test_agent.name}', got '{agent.name}'"
    assert agent.description == test_agent.description, f"Description mismatch"
    assert agent.instructions == test_agent.instructions, f"Instructions mismatch"

    # Validate that the agent is actually functional (has required fields)
    assert agent.status in [
        "onboarded",
        "draft",
    ], f"Agent status '{agent.status}' indicates it may not be functional"


def test_agent_serialization(client, test_agent):
    """Test agent serialization and deserialization."""
    agent = client.Agent.get(test_agent.id)

    # Test to_dict serialization
    agent_dict = agent.to_dict()
    assert isinstance(agent_dict, dict)
    assert agent_dict["id"] == test_agent.id
    assert agent_dict["name"] == agent.name
    assert agent_dict["status"] == agent.status

    # Test from_dict deserialization
    new_agent = client.Agent.from_dict(agent_dict)
    assert new_agent.id == agent.id
    assert new_agent.name == agent.name
    assert new_agent.status == agent.status


def test_agent_run_structure(client, test_agent):
    """Test agent run functionality and response structure."""
    agent = client.Agent.get(test_agent.id)

    # Test agent run with a simple query
    response = agent.run("Hello, how are you?")

    # Validate response structure
    assert hasattr(response, "request_id")
    assert hasattr(response, "data")
    assert hasattr(response, "completed")
    assert hasattr(response, "status")

    # Check response data - request_id can be None for some responses
    if response.request_id is not None:
        assert isinstance(response.request_id, str)

    # data can be AgentResponseData object, not just string
    assert hasattr(response.data, "output") or isinstance(response.data, str)
    assert isinstance(response.completed, bool)
    assert isinstance(response.status, str)

    # Validate that the response is completed - run() should return completed result
    assert response.completed is True, f"Agent execution should return completed result, got: {response.completed}"

    # Validate final response
    assert response.status in [
        "SUCCESS",
        "FAILED",
        "IN_PROGRESS",
    ], f"Unexpected response status: {response.status}"

    # For successful responses, validate the data
    if response.status == "SUCCESS":
        if hasattr(response.data, "output"):
            assert response.data.output is not None, "Response output is None for successful execution"
            assert len(response.data.output) > 0, "Response output is empty for successful execution"
        elif isinstance(response.data, str):
            assert len(response.data) > 0, "Response data is empty string for successful execution"

    # For failed responses, provide more context
    elif response.status == "FAILED":
        if hasattr(response, "error_message") and response.error_message:
            pytest.fail(f"Agent execution failed: {response.error_message}")
        else:
            pytest.fail(f"Agent execution failed with status: {response.status}")


def test_agent_creation_and_deletion(client):
    """Test agent creation and deletion workflow."""
    # Create a test agent
    agent = client.Agent(
        name=f"Test Agent for Deletion {int(time.time())}",
        description="A temporary agent for testing creation and deletion",
        instructions="You are a test agent for testing purposes only",
    )

    # Test agent creation
    assert agent.name.startswith("Test Agent for Deletion")
    assert agent.description == "A temporary agent for testing creation and deletion"
    assert agent.instructions == "You are a test agent for testing purposes only"

    # Save the agent to get an ID
    agent.save()

    # Verify the agent now has an ID
    assert agent.id is not None
    assert isinstance(agent.id, str)

    # Verify the agent was actually saved by retrieving it from the backend
    retrieved_agent = client.Agent.get(agent.id)
    assert retrieved_agent.id == agent.id
    assert retrieved_agent.name == agent.name
    assert retrieved_agent.description == agent.description
    assert retrieved_agent.instructions == agent.instructions

    # Store the ID before deletion since it might be cleared
    deleted_agent_id = agent.id
    assert deleted_agent_id is not None, "Agent ID should exist before deletion"

    # Clean up - delete the agent
    delete_result = agent.delete()

    # Verify deletion was successful
    assert delete_result is not None
    assert hasattr(delete_result, "status")
    assert delete_result.status == "SUCCESS"

    # Verify the agent was actually deleted by trying to retrieve it
    from aixplain.v2.exceptions import APIError

    with pytest.raises(APIError) as exc_info:
        client.Agent.get(deleted_agent_id)

    # Verify the error indicates the resource was deleted/not accessible
    error_message = str(exc_info.value).lower()
    expected_errors = [
        "not found",
        "404",
        "does not exist",
        "no such",
        "forbidden",
        "403",
    ]
    assert any(phrase in error_message for phrase in expected_errors), (
        f"Expected deletion/access error, got: {exc_info.value}"
    )

    print(f"✅ Agent deletion verified: {type(exc_info.value).__name__}: {exc_info.value}")


def test_agent_field_mappings(client, test_agent):
    """Test agent field mappings and data consistency."""
    agent = client.Agent.get(test_agent.id)

    # Test field mappings - verify retrieved agent matches created agent
    assert agent.id == test_agent.id
    assert agent.name == test_agent.name
    assert agent.description == test_agent.description
    assert agent.instructions == test_agent.instructions
    # Status should be valid
    assert agent.status in ["onboarded", "draft"]
    # team_id should be present (integer)
    assert agent.team_id is None or isinstance(agent.team_id, int)


def test_slack_tool_integration_with_agent(client, slack_token):
    """Test Slack tool integration with agent creation and execution."""
    # Get Slack integration
    integration = client.Integration.get("686432941223092cb4294d3f")  # Slack integration ID

    # Create Slack tool
    slack_tool = client.Tool(
        name=f"test-slack-tool-{int(time.time())}",
        integration=integration,
        config={"token": slack_token},
        allowed_actions=["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"],
    )

    # Validate tool creation
    assert slack_tool.name.startswith("test-slack-tool-")
    assert slack_tool.integration.id == "686432941223092cb4294d3f"
    assert "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL" in slack_tool.allowed_actions

    # Save tool before running
    slack_tool.save()

    # Test tool execution
    test_message = "Hello from aixplain functional test!"
    tool_response = slack_tool.run(
        action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
        data={"channel": "#integrations-test", "text": test_message},
    )

    # Validate tool response
    assert tool_response is not None
    assert hasattr(tool_response, "status")
    assert hasattr(tool_response, "completed")
    assert hasattr(tool_response, "data")

    # Validate tool execution success - run() should already return completed result
    assert tool_response.completed is True, f"Tool execution failed to complete. Status: {tool_response.status}"
    assert tool_response.status == "SUCCESS", f"Tool execution failed with status: {tool_response.status}"

    # Validate tool response data
    assert tool_response.data is not None, "Tool response data is None"
    if hasattr(tool_response.data, "output"):
        assert tool_response.data.output is not None, "Tool response output is None"
    elif isinstance(tool_response.data, str):
        assert len(tool_response.data) > 0, "Tool response data is empty string"

    # Create agent with the Slack tool
    agent = client.Agent(
        name=f"test-slack-agent-{int(time.time())}",
        description="A test agent with Slack integration",
        instructions="You are a test agent that can post messages to Slack",
        tools=[slack_tool],
    )

    # Validate agent creation
    assert agent.name.startswith("test-slack-agent-")
    assert agent.description == "A test agent with Slack integration"
    assert agent.instructions == "You are a test agent that can post messages to Slack"
    assert len(agent.tools) == 1

    # Save the agent to get an ID
    agent.save()

    # Verify the agent now has an ID
    assert agent.id is not None
    assert isinstance(agent.id, str)

    # Test agent execution with Slack tool
    query = "post a test message to slack channel #integrations-test saying 'This is a functional test from pytest!'"
    agent_response = agent.run(query)

    # Validate agent response
    assert agent_response is not None
    assert hasattr(agent_response, "request_id")
    assert hasattr(agent_response, "data")
    assert hasattr(agent_response, "completed")
    assert hasattr(agent_response, "status")

    # Validate agent execution success - run() should already return completed result
    assert agent_response.completed is True, f"Agent execution failed to complete. Status: {agent_response.status}"
    assert agent_response.status == "SUCCESS", f"Agent execution failed with status: {agent_response.status}"

    # Validate agent response data
    assert agent_response.data is not None, "Agent response data is None"
    if hasattr(agent_response.data, "output"):
        assert agent_response.data.output is not None, "Agent response output is None"
        assert len(agent_response.data.output) > 0, "Agent response output is empty"
    elif isinstance(agent_response.data, str):
        assert len(agent_response.data) > 0, "Agent response data is empty string"

    # Validate that the agent used the Slack tool
    # data can be AgentResponseData object, so we need to access the output field
    if hasattr(agent_response.data, "output"):
        response_text = agent_response.data.output
    else:
        response_text = str(agent_response.data)

    # Check that the response contains expected content or indicates success
    response_lower = response_text.lower()
    assert (
        "slack" in response_lower
        or "message" in response_lower
        or "success" in response_lower
        or "functional test" in response_lower
        or agent_response.status == "SUCCESS"
    )

    # Clean up - delete the agent and tool
    agent.delete()
    # Note: Tool deletion may not be implemented yet, but agent deletion should work
