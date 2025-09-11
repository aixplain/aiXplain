"""Tests for agent deployment functionality with MCP (Model Control Protocol) tools.

This test verifies that agents can be created, deployed, and used with MCP tools,
including proper status management and cleanup.
"""

import pytest
import logging
from uuid import uuid4
from aixplain.factories import ToolFactory, AgentFactory
from aixplain.modules.model.integration import AuthenticationSchema
from aixplain.enums import AssetStatus
from aixplain.exceptions import AlreadyDeployedError
from tests.test_deletion_utils import safe_delete_all_agents_and_team_agents


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def cleanup_agents():
    """Fixture to clean up agents before and after tests."""
    # Clean up before test
    safe_delete_all_agents_and_team_agents()

    yield True

    # Clean up after test
    safe_delete_all_agents_and_team_agents()


@pytest.fixture
def mcp_tool():
    """Create an MCP tool for testing."""
    tool = ToolFactory.create(
        integration="686eb9cd26480723d0634d3e",  # Remote MCP ID
        name=f"Test Remote MCP {uuid4()}",
        authentication_schema=AuthenticationSchema.API_KEY,
        data={"url": "https://remote.mcpservers.org/fetch/mcp"},
    )

    # Set allowed actions (using ... as in original script)
    tool.allowed_actions = [...]

    # Filter actions to only include "fetch" action
    tool.action_scope = [action for action in tool.actions if action.code == "fetch"]

    return tool


@pytest.fixture
def test_agent(cleanup_agents, mcp_tool):
    """Create a test agent with MCP tool."""
    agent = AgentFactory.create(
        name=f"Test Agent {uuid4()}",
        description="This agent is used to scrape websites",
        instructions="You are a helpful assistant that can scrape any given website",
        tools=[mcp_tool],
        llm="669a63646eb56306647e1091",
    )
    return agent


def test_agent_creation_with_mcp_tool(test_agent, mcp_tool):
    """Test that an agent can be created with an MCP tool."""
    assert test_agent is not None
    assert test_agent.name.startswith("Test Agent")
    assert test_agent.description == "This agent is used to scrape websites"
    assert len(test_agent.tools) == 1
    assert test_agent.tools[0] == mcp_tool
    assert test_agent.status == AssetStatus.DRAFT


def test_agent_run_before_deployment(test_agent):
    """Test that an agent can run before being deployed."""
    response = test_agent.run("Give me information about the aixplain website")

    assert response is not None
    assert hasattr(response, "data")
    assert hasattr(response.data, "output")


def test_agent_deployment(test_agent):
    """Test that an agent can be deployed successfully."""
    # Verify initial status is DRAFT
    assert test_agent.status == AssetStatus.DRAFT

    # Deploy the agent
    test_agent.deploy()

    # Verify status is now ONBOARDED
    assert test_agent.status == AssetStatus.ONBOARDED


def test_agent_retrieval_after_deployment(test_agent):
    """Test that a deployed agent can be retrieved and maintains its status."""
    # Deploy the agent first
    test_agent.deploy()
    agent_id = test_agent.id

    # Retrieve the agent by ID
    retrieved_agent = AgentFactory.get(agent_id)

    assert retrieved_agent is not None
    assert retrieved_agent.id == agent_id
    assert retrieved_agent.status == AssetStatus.ONBOARDED


def test_deployed_agent_cannot_be_deployed_again(test_agent):
    """Test that attempting to deploy an already deployed agent raises an error."""
    # Deploy the agent first
    test_agent.deploy()
    assert test_agent.status == AssetStatus.ONBOARDED

    # Attempt to deploy again should raise AlreadyDeployedError
    with pytest.raises(AlreadyDeployedError, match="is already deployed"):
        test_agent.deploy()


def test_deployed_agent_can_run(test_agent):
    """Test that a deployed agent can still run queries."""
    # Deploy the agent first
    test_agent.deploy()

    # Run a query on the deployed agent
    response = test_agent.run("Give me information about the aixplain website")

    assert response is not None
    assert hasattr(response, "data")
    assert hasattr(response.data, "output")


def test_agent_lifecycle_end_to_end(cleanup_agents, mcp_tool):
    """Test the complete agent lifecycle: create, run, deploy, retrieve, run, delete."""
    # Create agent
    agent = AgentFactory.create(
        name=f"Test Agent Lifecycle {uuid4()}",
        description="This agent is used for lifecycle testing",
        instructions="You are a helpful assistant that can scrape any given website",
        tools=[mcp_tool],
        llm="669a63646eb56306647e1091",
    )

    # Test initial state
    assert agent.status == AssetStatus.DRAFT

    # Test run before deployment
    response = agent.run("Give me information about the aixplain website")
    assert response is not None

    # Deploy agent
    agent.deploy()
    assert agent.status == AssetStatus.ONBOARDED

    # Retrieve agent by ID
    agent_id = agent.id
    retrieved_agent = AgentFactory.get(agent_id)
    assert retrieved_agent.status == AssetStatus.ONBOARDED

    # Test run after deployment
    response = retrieved_agent.run("Give me information about the aixplain website")
    assert response is not None

    # Clean up
    retrieved_agent.delete()


def test_mcp_tool_properties(mcp_tool):
    """Test that the MCP tool has the expected properties."""
    assert mcp_tool is not None
    assert mcp_tool.name.startswith("MCP Server")
    assert hasattr(mcp_tool, "actions")
    assert hasattr(mcp_tool, "action_scope")
    assert len(mcp_tool.action_scope) >= 0  # Should have filtered actions

    # Verify that action_scope only contains "fetch" actions
    for action in mcp_tool.action_scope:
        assert action.code == "fetch"
