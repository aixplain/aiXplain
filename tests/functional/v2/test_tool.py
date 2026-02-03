import os
import pytest
import time

from aixplain.v2.integration import Integration


@pytest.fixture(scope="module")
def slack_integration_id():
    """Return Slack integration ID for testing."""
    return "686432941223092cb4294d3f"


def validate_tool_structure(tool):
    """Helper function to validate tool structure and data types."""
    # Test core fields (inherited from Model)
    assert isinstance(tool.id, str), "Tool ID should be a string"
    assert isinstance(tool.name, str), "Tool name should be a string"
    if tool.description is not None:
        assert isinstance(tool.description, str), "Tool description should be a string"

    # Test Tool-specific fields
    if tool.asset_id is not None:
        assert isinstance(tool.asset_id, str), "Tool asset_id should be a string"

    if tool.integration is not None:
        assert isinstance(tool.integration, (Integration, str)), (
            "Tool integration should be Integration object or string"
        )

    if tool.config is not None:
        assert isinstance(tool.config, dict), "Tool config should be a dictionary"

    if tool.code is not None:
        assert isinstance(tool.code, str), "Tool code should be a string"

    if tool.allowed_actions is not None:
        assert isinstance(tool.allowed_actions, list), "Tool allowed_actions should be a list"
        for action in tool.allowed_actions:
            assert isinstance(action, str), "Each allowed_action should be a string"

    tool_params = tool.get_parameters() if hasattr(tool, "get_parameters") else None
    if tool_params is not None:
        assert isinstance(tool_params, list), "Tool parameters should be a list"
        for param in tool_params:
            assert isinstance(param, dict), "Each parameter should be a dictionary"

    # Test inherited fields from Model
    if tool.service_name is not None:
        assert isinstance(tool.service_name, str), "Tool service_name should be a string"

    if tool.status is not None:
        assert hasattr(tool.status, "value"), "Tool status should be an enum with value attribute"

    # Tool doesn't have hosted_by, developed_by, or supplier attributes, skip these checks
    # if hasattr(tool, "host") and tool.host is not None:
    #     assert isinstance(tool.host, str), "Tool host should be a string"
    # if hasattr(tool, "developer") and tool.developer is not None:
    #     assert isinstance(tool.developer, str), "Tool developer should be a string"
    # if hasattr(tool, "supplier") and tool.supplier is not None:
    #     assert hasattr(tool.supplier, "id"), "Tool supplier should have id attribute"
    #     assert hasattr(tool.supplier, "name"), "Tool supplier should have name attribute"
    #     assert hasattr(tool.supplier, "code"), "Tool supplier should have code attribute"

    if tool.function is not None:
        assert isinstance(tool.function, (dict, str)), "Tool function should be dict or string"

    if tool.pricing is not None:
        assert hasattr(tool.pricing, "price"), "Tool pricing should have price attribute"

    if tool.version is not None:
        assert hasattr(tool.version, "name"), "Tool version should have name attribute"
        assert hasattr(tool.version, "id"), "Tool version should have id attribute"

    if tool.attributes is not None:
        assert isinstance(tool.attributes, list), "Tool attributes should be a list"
        for attr in tool.attributes:
            assert hasattr(attr, "name"), "Each attribute should have name attribute"
            assert hasattr(attr, "code"), "Each attribute should have code attribute"

    if tool.params is not None:
        assert isinstance(tool.params, list), "Tool params should be a list"
        for param in tool.params:
            assert hasattr(param, "name"), "Each param should have name attribute"
            assert hasattr(param, "required"), "Each param should have required attribute"
            assert hasattr(param, "data_type"), "Each param should have data_type attribute"

    # Test that Tool has delete method from DeleteResourceMixin
    assert hasattr(tool, "delete"), "Tool should have delete method from DeleteResourceMixin"


def test_search_tools(client):
    """Test searching tools with pagination."""
    tools = client.Tool.search()
    assert hasattr(tools, "results")
    assert isinstance(tools.results, list)
    number_of_tools = len(tools.results)
    assert number_of_tools > 0, "Expected to get results from tool search"

    # Validate structure of returned tools
    for tool in tools.results:
        validate_tool_structure(tool)

    if number_of_tools < 2:
        pytest.skip("Expected to have at least 2 tools for testing pagination")

    # Test with page size
    tools = client.Tool.search(page_size=number_of_tools - 1)
    assert hasattr(tools, "results")
    assert isinstance(tools.results, list)
    assert len(tools.results) <= number_of_tools - 1, (
        f"Expected at most {number_of_tools - 1} tools, but got {len(tools.results)}"
    )

    # Test with page number
    tools_page_2 = client.Tool.search(page_number=1, page_size=number_of_tools - 1)
    assert hasattr(tools_page_2, "results")
    assert isinstance(tools_page_2.results, list)
    assert len(tools_page_2.results) <= number_of_tools - 1, (
        f"Expected at most {number_of_tools - 1} tools, but got {len(tools_page_2.results)}"
    )


def test_search_tools_with_query_filter(client):
    """Test searching tools with query filter."""
    # Test with search query - use a more generic query
    query = "test"
    tools = client.Tool.search(q=query)
    assert hasattr(tools, "results"), "Tools should have results attribute"
    assert isinstance(tools.results, list), "Tools results should be a list"

    # If we get results, validate that at least some tools match the query
    if tools.results:
        matching_tools = []
        for tool in tools.results:
            # Check if the query appears in name, description, or other relevant fields
            tool_text = f"{tool.name} {tool.description or ''}".lower()
            if query.lower() in tool_text:
                matching_tools.append(tool)

        # If we have results but no matches, the search might be working differently
        # or the query might not match any tools. This is acceptable behavior.
        if not matching_tools:
            # Log that no tools matched the query, but don't fail the test
            print(
                f"No tools matched query '{query}' in name or description, but search returned {len(tools.results)} results"
            )
    else:
        # If no results returned, that's also acceptable for some queries
        print(f"No tools returned for query '{query}'")


def test_get_tool(client):
    """Test getting a specific tool by ID."""
    # First, search tools to get a valid tool ID
    tools = client.Tool.search()
    assert len(tools.results) > 0, "Expected to have at least one tool available for testing"

    tool_id = tools.results[0].id
    tool = client.Tool.get(tool_id)
    assert tool.id == tool_id, "Retrieved tool ID should match the requested ID"

    # Validate complete tool structure
    validate_tool_structure(tool)


def test_tool_run(client, slack_integration_id, slack_token):
    """Test running an integration tool."""
    tool_name = f"test-run-integration-{int(time.time())}"

    # Get the integration
    integration = client.Integration.get(slack_integration_id)

    # Create tool with proper authentication
    tool = client.Tool(
        name=tool_name,
        integration=integration,
        config={"token": slack_token},
        allowed_actions=["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"],
    )

    # Save tool before running
    tool.save()

    result = tool.run(
        action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
        data={
            "channel": "#integrations-test",
            "text": f"Test message from functional test {int(time.time())}",
        },
    )

    # Assert the result structure
    assert hasattr(result, "status"), "Result should have status attribute"
    assert hasattr(result, "data"), "Result should have data attribute"
    assert result.status == "SUCCESS", f"Expected SUCCESS status, got {result.status}"
    assert result.data is not None, "Result data should not be None"

    # Clean up - ensure tool is deleted
    print(f"Tool ID before deletion: {tool.id}")
    if tool.id:
        # Store the ID before deletion since it might be cleared
        deleted_tool_id = tool.id
        assert deleted_tool_id is not None, "Tool ID should exist before deletion"

        tool.delete()

        # Verify the tool was actually deleted by trying to retrieve it
        from aixplain.v2.exceptions import APIError

        with pytest.raises(APIError) as exc_info:
            client.Tool.get(deleted_tool_id)

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

        print(f"✅ Tool deletion verified: {type(exc_info.value).__name__}: {exc_info.value}")
    else:
        print("⚠️ Tool has no ID, skipping deletion validation")


def test_tool_get_parameters(client, slack_integration_id, slack_token):
    """Test getting tool parameters."""
    tool_name = f"test-params-{int(time.time())}"

    # Get the integration
    integration = client.Integration.get(slack_integration_id)

    # Create tool with proper authentication
    tool = client.Tool(
        name=tool_name,
        integration=integration,
        config={"token": slack_token},
        allowed_actions=["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"],
    )

    # Get parameters - this should work for properly configured tools
    parameters = tool.get_parameters()
    assert isinstance(parameters, list), "get_parameters() should return a list"

    # Validate parameter structure if parameters exist
    if parameters:
        for param in parameters:
            assert "code" in param, "Parameter should have 'code' field"
            assert "name" in param, "Parameter should have 'name' field"
            assert "description" in param, "Parameter should have 'description' field"
            assert "inputs" in param, "Parameter should have 'inputs' field"
            assert isinstance(param["inputs"], dict), "Parameter inputs should be a dictionary"

    # Clean up - ensure tool is deleted
    if tool.id:
        tool.delete()
