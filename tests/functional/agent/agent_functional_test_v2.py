import os
import pytest
from aixplain import Aixplain


@pytest.fixture(scope="function")
def aix():
    api_key = os.getenv("TEAM_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY environment variable not set")
    return Aixplain(api_key=api_key)


def test_v2_agent_run_with_utility(aix):
    """Ported legacy agent run test: create, deploy, run, assert output."""
    # Create a simple utility function
    def greet_random_name(greeting: str) -> str:
        """Greet a random name and return the result as a string."""
        import random
        list_of_names = ["John", "Jane", "Jim", "Jill", "Jack", "Jill", "Jim", "Jane", "John", "Jack"]
        return f"{greeting} {random.choice(list_of_names)}"

    # Create utility tool using convenient constructor
    utility_tool = aix.Tool(
        name="greet_random_name",
        description=(
            "Greet a random name and return the result as a string."
        ),
        code=greet_random_name
    )
    # Create agent with utility tool and a valid LLM
    agent = aix.Agent(
        name="test-agent-v2",
        description="A test agent for v2 run",
        instructions=(
            "You are a test assistant. Use the provided tool to greet a random name."
        ),
        tools=[utility_tool],
        llm_id="6646261c6eb563165658bbb1",
    )

    # Deploy the agent
    try:
        agent.deploy()
        assert agent.status == "onboarded"
    except Exception:
        print("Error deploying agent, deleting and trying again")
        agent.delete()
        agent.deploy()
        assert agent.status == "onboarded"

    # Run the agent with a prompt that requires the tool
    response = agent.run(
        query={
            "input": "Greet a random name."
        }
    )
    # Assert legacy-style output
    assert response is not None
    assert hasattr(response, "completed")
    assert hasattr(response, "status")
    assert hasattr(response, "data")
    assert response.completed is True
    assert response.status.lower() == "success"

    # Clean up
    agent.delete()
    utility_tool.resource.delete()
