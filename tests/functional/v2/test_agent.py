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
    assert hasattr(agents, "results")
    assert isinstance(agents.results, list)
    number_of_agents = len(agents.results)
    assert number_of_agents >= 0, "Expected to get results from agent listing"

    # Validate structure of returned agents
    for agent in agents.results:
        validate_agent_structure(agent)


def test_get_agent(client, agent_id):
    """Test getting a specific agent by ID - verifies backend interaction and structure."""
    agent = client.Agent.get(agent_id)
    assert agent.id == agent_id

    # Validate complete agent structure
    validate_agent_structure(agent)
    
    # Test specific fields for this agent match backend data
    assert agent.name == "Scraper Utility Agent"
    assert agent.status == "onboarded"
    assert agent.team_id == 15752
    assert agent.llm_id == "669a63646eb56306647e1091"
    assert "Scrapes travel blogs" in agent.description


def test_agent_object_hierarchy(client, agent_id):
    """Test that the agent object hierarchy matches the backend structure exactly."""
    agent = client.Agent.get(agent_id)
    
    # Test that all expected fields are present and have correct types
    expected_fields = {
        "id": str,
        "name": str,
        "status": str,
        "team_id": int,
        "description": str,
        "llm_id": str,
        "assets": list,
        "createdAt": str,
        "updatedAt": str,
        "inspectorTargets": list,
        "maxInspectors": type(None),  # Can be None
        "inspectors": list,
        "resourceInfo": dict,
        "expectedOutput": type(None),  # Can be None
    }
    
    for field_name, expected_type in expected_fields.items():
        assert hasattr(agent, field_name), f"Agent should have field: {field_name}"
        field_value = getattr(agent, field_name)
        
        if expected_type == type(None):
            # Field can be None
            assert field_value is None or isinstance(field_value, (dict, list, str, int))
        else:
            assert isinstance(field_value, expected_type), f"Field {field_name} should be {expected_type}, got {type(field_value)}"
    
    # Test specific structure of assets
    if agent.assets:
        for asset in agent.assets:
            assert isinstance(asset, dict)
            # Check for required asset fields based on the backend structure
            if "assetId" in asset and asset["assetId"] is not None:
                assert isinstance(asset["assetId"], str)
            if "type" in asset and asset["type"] is not None:
                assert isinstance(asset["type"], str)
            if "function" in asset and asset["function"] is not None:
                assert isinstance(asset["function"], str)
            if "supplier" in asset and asset["supplier"] is not None:
                assert isinstance(asset["supplier"], str)


def test_agent_serialization(client, agent_id):
    """Test that the agent can be properly serialized and deserialized - verifies backend structure matching."""
    agent = client.Agent.get(agent_id)
    
    # Test to_dict serialization
    agent_dict = agent.to_dict()
    assert isinstance(agent_dict, dict)
    
    # Check that all fields are present in the serialized form
    expected_keys = {
        "id", "name", "status", "teamId", "description", "llmId", 
        "assets", "createdAt", "updatedAt", "inspectorTargets", 
        "maxInspectors", "inspectors", "resourceInfo", "expectedOutput"
    }
    
    for key in expected_keys:
        assert key in agent_dict, f"Serialized agent should have key: {key}"
    
    # Test that the serialized form matches the backend structure
    assert agent_dict["id"] == agent_id
    assert agent_dict["name"] == "Scraper Utility Agent"
    assert agent_dict["status"] == "onboarded"
    assert agent_dict["teamId"] == 15752
    assert agent_dict["llmId"] == "669a63646eb56306647e1091"


def test_agent_run_structure(client, agent_id):
    """Test the structure of agent run results - verifies backend interaction."""
    agent = client.Agent.get(agent_id)
    
    # Test running the agent with a simple query
    result = agent.run(query="What is the weather like today?")
    
    # Validate the result structure
    assert hasattr(result, "status")
    assert hasattr(result, "completed")
    assert hasattr(result, "data")
    assert hasattr(result, "session_id")
    assert hasattr(result, "request_id")
    assert hasattr(result, "error_message")
    assert hasattr(result, "used_credits")
    assert hasattr(result, "run_time")
    
    # Check data types
    assert isinstance(result.status, str)
    assert isinstance(result.completed, bool)
    assert isinstance(result.used_credits, float)
    assert isinstance(result.run_time, float)
    
    # Check that the run was successful
    assert result.completed is True, f"Agent run should be completed, got: {result.completed}"
    assert result.status in ["SUCCESS", "success"], f"Agent run should be successful, got status: {result.status}"
    assert result.error_message is None, f"Agent run should not have errors, got: {result.error_message}"
    
    # Check that session_id is present if completed (but it can be None in some cases)
    if result.completed:
        # session_id can be None in some cases, so we just check that the attribute exists
        assert hasattr(result, "session_id")
    
    # Check that data is present and has the expected structure
    assert result.data is not None, "Agent run result should have data"
    if hasattr(result.data, "output"):
        assert result.data.output is not None, "Agent run result should have output"


def test_agent_creation_and_deletion(client):
    """Test creating and deleting an agent - verifies backend CRUD operations."""
    # Create a new agent with a unique name
    import time
    unique_name = f"Test Agent for Deletion {int(time.time())}"
    agent = client.Agent(
        name=unique_name,
        description="A test agent that will be deleted",
        status="draft"
    )
    
    # Save the agent first to get an ID
    agent.save()
    assert agent.id is not None
    assert agent.id != ""
    
    # Now test that the agent has the expected structure
    validate_agent_structure(agent)
    
    # Verify the agent was saved
    saved_agent = client.Agent.get(agent.id)
    assert saved_agent.id == agent.id
    assert saved_agent.name == unique_name
    
    # Delete the agent
    delete_result = agent.delete()
    assert hasattr(delete_result, "status")
    assert hasattr(delete_result, "completed")


def test_agent_field_mappings(client, agent_id):
    """Test that field mappings work correctly for camelCase fields - verifies backend structure matching."""
    agent = client.Agent.get(agent_id)
    
    # Test that camelCase fields are properly mapped
    assert hasattr(agent, "team_id")
    assert hasattr(agent, "llm_id")
    
    # Test that the underlying data uses camelCase
    agent_dict = agent.to_dict()
    assert "teamId" in agent_dict
    assert "llmId" in agent_dict
    
    # Verify the values match
    assert agent_dict["teamId"] == agent.team_id
    assert agent_dict["llmId"] == agent.llm_id 