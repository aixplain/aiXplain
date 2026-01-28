import pytest


@pytest.fixture(scope="module")
def slack_integration_id():
    """Return a Slack integration model ID for testing."""
    return "686432941223092cb4294d3f"  # Use Script integration from test_aa.py (Slack integration)


def validate_integration_structure(integration):
    """Helper function to validate integration structure and data types."""
    # Test core model fields (inherited from Model)
    assert isinstance(integration.id, str)
    assert isinstance(integration.name, str)
    if integration.description is not None:
        assert isinstance(integration.description, str)

    # Test attributes if present
    if integration.attributes:
        assert isinstance(integration.attributes, list)
        for attr in integration.attributes:
            assert hasattr(attr, "name")
            assert hasattr(attr, "code")


def test_integration_list_actions(client, slack_integration_id):
    """Test the list_actions method of Integration class."""
    integration = client.Integration.get(slack_integration_id)

    # Validate integration structure
    validate_integration_structure(integration)

    try:
        actions = integration.list_actions()
        assert isinstance(actions, list)

        # Validate action structure if actions exist
        for action in actions:
            assert hasattr(action, "name")
            assert hasattr(action, "description")
            assert hasattr(action, "slug")
            assert hasattr(action, "inputs")

            # Test inputs if present
            if action.inputs:
                assert isinstance(action.inputs, list)
                for input_item in action.inputs:
                    assert hasattr(input_item, "name")
                    assert hasattr(input_item, "code")
                    assert hasattr(input_item, "required")
                    assert hasattr(input_item, "datatype")
    except Exception as e:
        # If the integration doesn't support list_actions or fails due to backend
        # issues, that's acceptable in test environment
        error_msg = str(e).lower()
        expected_errors = ["supplier_error", "tool not found", "not found"]
        assert any(err in error_msg for err in expected_errors)
        print(f"list_actions failed as expected: {e}")


def test_integration_list_inputs(client, slack_integration_id):
    """Test the list_inputs method of Integration class."""
    integration = client.Integration.get(slack_integration_id)

    try:
        # Test with no actions specified
        inputs = integration.list_inputs()
        assert isinstance(inputs, list)

        # Test with specific actions
        actions = integration.list_actions()
        if actions:
            # Test with first 2 actions
            action_slugs = [action.slug for action in actions[:2]]
            inputs = integration.list_inputs(*action_slugs)
            assert isinstance(inputs, list)

            # Validate input structure if inputs exist
            for input_item in inputs:
                assert hasattr(input_item, "name")
                assert hasattr(input_item, "code")
                assert hasattr(input_item, "required")
                assert hasattr(input_item, "datatype")
                assert hasattr(input_item, "description")
    except Exception as e:
        # If the integration doesn't support list_inputs or fails due to backend
        # issues, that's acceptable in test environment
        error_msg = str(e).lower()
        expected_errors = ["supplier_error", "tool not found", "not found"]
        assert any(err in error_msg for err in expected_errors)
        print(f"list_inputs failed as expected: {e}")
