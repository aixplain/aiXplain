import pytest
from aixplain.enums import AssetStatus, ResponseStatus


@pytest.fixture(scope="module")
def agent_id():
    """Return an agent ID for testing."""
    return "67911bdb4616206d6769a787"  # Scraper Utility Agent


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

    if agent.llm_id:
        assert isinstance(agent.llm_id, str)

    # Test assets structure if present
    if agent.assets:
        assert isinstance(agent.assets, list)
        for asset in agent.assets:
            assert isinstance(asset, dict)
            # Check for required asset fields - assetId can be None
            if "assetId" in asset and asset["assetId"] is not None:
                assert isinstance(asset["assetId"], str)
            if "type" in asset and asset["type"] is not None:
                assert isinstance(asset["type"], str)
            if "function" in asset and asset["function"] is not None:
                assert isinstance(asset["function"], str)
            if "supplier" in asset and asset["supplier"] is not None:
                assert isinstance(asset["supplier"], str)

    # Test timestamps if present
    if agent.createdAt:
        assert isinstance(agent.createdAt, str)

    if agent.updatedAt:
        assert isinstance(agent.updatedAt, str)

    # Test inspector-related fields if present
    if agent.inspectorTargets:
        assert isinstance(agent.inspectorTargets, list)

    if agent.maxInspectors is not None:
        assert isinstance(agent.maxInspectors, int)

    if agent.inspectors:
        assert isinstance(agent.inspectors, list)

    # Test resourceInfo if present
    if agent.resourceInfo:
        assert isinstance(agent.resourceInfo, dict)

    # Test expectedOutput if present
    if agent.expectedOutput is not None:
        # expectedOutput can be any type, so we just check it's not None
        pass


def test_list_agents(client):
    """Test listing agents with pagination - verifies backend interaction."""
    agents = client.Agent.list()
    assert hasattr(agents, "results"), "Agent list response missing 'results' field"
    assert isinstance(agents.results, list), "Agent list results is not a list"
    
    number_of_agents = len(agents.results)
    assert number_of_agents >= 0, "Expected to get results from agent listing"
    
    # Validate that we actually got some agents (functional test should have data)
    assert number_of_agents > 0, "No agents returned from listing - this may indicate a backend issue"
    
    # Validate structure of returned agents
    for i, agent in enumerate(agents.results):
        try:
            validate_agent_structure(agent)
        except AssertionError as e:
            pytest.fail(f"Agent {i} failed structure validation: {e}")
    
    # Validate pagination metadata if available
    if hasattr(agents, 'total'):
        assert agents.total >= number_of_agents, "Total count should be >= number of results"
    if hasattr(agents, 'page_number'):
        assert agents.page_number >= 0, "Page number should be non-negative"


def test_get_agent(client, agent_id):
    """Test getting a specific agent by ID - verifies backend interaction and structure."""
    agent = client.Agent.get(agent_id)
    assert agent.id == agent_id, f"Retrieved agent ID {agent.id} doesn't match requested ID {agent_id}"

    # Validate complete agent structure
    try:
        validate_agent_structure(agent)
    except AssertionError as e:
        pytest.fail(f"Agent structure validation failed: {e}")
    
    # Test specific fields for this agent match backend data
    assert agent.name == "Scraper Utility Agent", f"Expected agent name 'Scraper Utility Agent', got '{agent.name}'"
    assert agent.status == "onboarded", f"Expected agent status 'onboarded', got '{agent.status}'"
    assert agent.team_id == 15752, f"Expected team_id 15752, got {agent.team_id}"
    assert agent.llm_id == "669a63646eb56306647e1091", f"Expected LLM ID '669a63646eb56306647e1091', got '{agent.llm_id}'"
    
    # Validate description contains expected content
    assert agent.description is not None, "Agent description is None"
    assert "Scrapes travel blogs" in agent.description, f"Expected description to contain 'Scrapes travel blogs', got: '{agent.description}'"
    
    # Validate that the agent is actually functional (has required fields)
    assert agent.llm_id is not None, "Agent LLM ID is None - agent may not be functional"
    assert agent.status in ["onboarded", "draft"], f"Agent status '{agent.status}' indicates it may not be functional"


def test_agent_serialization(client, agent_id):
    """Test agent serialization and deserialization."""
    agent = client.Agent.get(agent_id)
    
    # Test to_dict serialization
    agent_dict = agent.to_dict()
    assert isinstance(agent_dict, dict)
    assert agent_dict["id"] == agent_id
    assert agent_dict["name"] == agent.name
    assert agent_dict["status"] == agent.status
    
    # Test from_dict deserialization
    new_agent = client.Agent.from_dict(agent_dict)
    assert new_agent.id == agent.id
    assert new_agent.name == agent.name
    assert new_agent.status == agent.status


def test_agent_run_structure(client, agent_id):
    """Test agent run functionality and response structure."""
    agent = client.Agent.get(agent_id)
    
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
    assert hasattr(response.data, 'output') or isinstance(response.data, str)
    assert isinstance(response.completed, bool)
    assert isinstance(response.status, str)
    
    # Validate that the response is completed - run() should return completed result
    assert response.completed is True, f"Agent execution should return completed result, got: {response.completed}"
    
    # Validate final response
    assert response.status in ["SUCCESS", "FAILED", "IN_PROGRESS"], f"Unexpected response status: {response.status}"
    
    # For successful responses, validate the data
    if response.status == "SUCCESS":
        if hasattr(response.data, 'output'):
            assert response.data.output is not None, "Response output is None for successful execution"
            assert len(response.data.output) > 0, "Response output is empty for successful execution"
        elif isinstance(response.data, str):
            assert len(response.data) > 0, "Response data is empty string for successful execution"
    
    # For failed responses, provide more context
    elif response.status == "FAILED":
        if hasattr(response, 'error_message') and response.error_message:
            pytest.fail(f"Agent execution failed: {response.error_message}")
        else:
            pytest.fail(f"Agent execution failed with status: {response.status}")


def test_agent_creation_and_deletion(client):
    """Test agent creation and deletion workflow."""
    # Create a test agent
    agent = client.Agent(
        name="Test Agent for Deletion",
        description="A temporary agent for testing creation and deletion",
        role="You are a test agent for testing purposes only"
    )

    # Test agent creation
    assert agent.name == "Test Agent for Deletion"
    assert agent.description == "A temporary agent for testing creation and deletion"
    assert agent.role == "You are a test agent for testing purposes only"

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
    assert retrieved_agent.role == agent.role
    
    # Store the ID before deletion since it might be cleared
    deleted_agent_id = agent.id
    assert deleted_agent_id is not None, "Agent ID should exist before deletion"
    
    # Clean up - delete the agent
    delete_result = agent.delete()
    
    # Verify deletion was successful
    assert delete_result is not None
    assert hasattr(delete_result, 'status')
    assert delete_result.status == "SUCCESS"
    
    # Verify the agent was actually deleted by trying to retrieve it
    from aixplain.v2.client import AixplainError
    with pytest.raises(AixplainError) as exc_info:
        client.Agent.get(deleted_agent_id)
    
    # Verify the error indicates the resource was deleted/not accessible
    error_message = str(exc_info.value).lower()
    expected_errors = ["not found", "404", "does not exist", "no such", "forbidden", "403"]
    assert any(phrase in error_message for phrase in expected_errors), \
        f"Expected deletion/access error, got: {exc_info.value}"
    
    print(f"✅ Agent deletion verified: {type(exc_info.value).__name__}: {exc_info.value}")


def test_agent_field_mappings(client, agent_id):
    """Test agent field mappings and data consistency."""
    agent = client.Agent.get(agent_id)
    
    # Test field mappings
    assert agent.id == agent_id
    assert agent.name == "Scraper Utility Agent"
    assert agent.status == "onboarded"
    assert agent.team_id == 15752
    assert agent.llm_id == "669a63646eb56306647e1091"
    
    # Test asset field mappings if assets exist
    if agent.assets:
        for asset in agent.assets:
            if "assetId" in asset and asset["assetId"]:
                assert asset["assetId"] is not None
            if "type" in asset and asset["type"]:
                assert asset["type"] in ["model", "regular", "connector"]


def test_slack_tool_integration_with_agent(client, slack_token):
    """Test Slack tool integration with agent creation and execution."""
    import time
    
    # Get Slack integration
    integration = client.Integration.get("686432941223092cb4294d3f")  # Slack integration ID
    
    # Create Slack tool
    slack_tool = client.Tool(
        name=f"test-slack-tool-{int(time.time())}",
        integration=integration,
        auth_params={"token": slack_token},
        auth_scheme=client.Integration.AuthenticationScheme.BEARER_TOKEN,
        allowed_actions=["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"]
    )
    
    # Validate tool creation
    assert slack_tool.name.startswith("test-slack-tool-")
    assert slack_tool.integration.id == "686432941223092cb4294d3f"
    assert slack_tool.auth_scheme == client.Integration.AuthenticationScheme.BEARER_TOKEN
    assert "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL" in slack_tool.allowed_actions
    
    # Test tool execution
    test_message = "Hello from aixplain functional test!"
    tool_response = slack_tool.run({
        "channel": "#integrations-test",
        "text": test_message
    })
    
    # Validate tool response
    assert tool_response is not None
    assert hasattr(tool_response, 'status')
    assert hasattr(tool_response, 'completed')
    assert hasattr(tool_response, 'data')
    
    # Validate tool execution success - run() should already return completed result
    assert tool_response.completed is True, f"Tool execution failed to complete. Status: {tool_response.status}"
    assert tool_response.status == "SUCCESS", f"Tool execution failed with status: {tool_response.status}"
    
    # Validate tool response data
    assert tool_response.data is not None, "Tool response data is None"
    if hasattr(tool_response.data, 'output'):
        assert tool_response.data.output is not None, "Tool response output is None"
    elif isinstance(tool_response.data, str):
        assert len(tool_response.data) > 0, "Tool response data is empty string"
    
    # Create agent with the Slack tool
    agent = client.Agent(
        name=f"test-slack-agent-{int(time.time())}",
        description="A test agent with Slack integration",
        role="You are a test agent that can post messages to Slack",
        tools=[slack_tool]
    )
    
    # Validate agent creation
    assert agent.name.startswith("test-slack-agent-")
    assert agent.description == "A test agent with Slack integration"
    assert agent.role == "You are a test agent that can post messages to Slack"
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
    assert hasattr(agent_response, 'request_id')
    assert hasattr(agent_response, 'data')
    assert hasattr(agent_response, 'completed')
    assert hasattr(agent_response, 'status')
    
    # Validate agent execution success - run() should already return completed result
    assert agent_response.completed is True, f"Agent execution failed to complete. Status: {agent_response.status}"
    assert agent_response.status == "SUCCESS", f"Agent execution failed with status: {agent_response.status}"
    
    # Validate agent response data
    assert agent_response.data is not None, "Agent response data is None"
    if hasattr(agent_response.data, 'output'):
        assert agent_response.data.output is not None, "Agent response output is None"
        assert len(agent_response.data.output) > 0, "Agent response output is empty"
    elif isinstance(agent_response.data, str):
        assert len(agent_response.data) > 0, "Agent response data is empty string"
    
    # Validate that the agent used the Slack tool
    # data can be AgentResponseData object, so we need to access the output field
    if hasattr(agent_response.data, 'output'):
        response_text = agent_response.data.output
    else:
        response_text = str(agent_response.data)
    
    assert "slack" in response_text.lower() or "message" in response_text.lower()
    
    # Clean up - delete the agent and tool
    agent.delete()
    # Note: Tool deletion may not be implemented yet, but agent deletion should work 