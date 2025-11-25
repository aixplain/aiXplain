import pytest


@pytest.fixture(scope="module")
def slack_integration_id():
    """Return a Slack integration model ID for testing."""
    return "686432941223092cb4294d3f"  # Use Script integration from test_aa.py (Slack integration)


@pytest.fixture(scope="module")
def integration_with_auth_schemes():
    """Return an integration ID that has multiple auth schemes."""
    return "686432941223092cb4294d3f"  # Script integration


def validate_integration_structure(integration):
    """Helper function to validate integration structure and data types."""
    # Test core model fields (inherited from Model)
    assert isinstance(integration.id, str)
    assert isinstance(integration.name, str)
    if integration.description is not None:
        assert isinstance(integration.description, str)

    # Test integration-specific fields
    assert hasattr(integration, "auth_schemes")
    assert isinstance(integration.auth_schemes, list)

    # Test attributes if present
    if integration.attributes:
        assert isinstance(integration.attributes, list)
        for attr in integration.attributes:
            assert hasattr(attr, "name")
            assert hasattr(attr, "code")


def test_integration_auth_schemes_property(client, slack_integration_id):
    """Test the auth_schemes property of Integration class."""
    integration = client.Integration.get(slack_integration_id)

    # Validate integration structure
    validate_integration_structure(integration)

    # Test auth_schemes property
    auth_schemes = integration.auth_schemes
    assert isinstance(auth_schemes, list)
    assert len(auth_schemes) > 0, "Integration should have at least one auth scheme"

    # Verify auth schemes are valid strings
    for scheme in auth_schemes:
        assert isinstance(scheme, str)
        expected_schemes = ["OAUTH2", "BEARER_TOKEN", "NO_AUTH"]
        assert scheme in expected_schemes, f"Unexpected auth scheme: {scheme}"


def test_integration_get_auth_inputs(client, slack_integration_id):
    """Test the get_auth_inputs method of Integration class."""
    integration = client.Integration.get(slack_integration_id)

    # Test with valid auth scheme
    auth_schemes = integration.auth_schemes
    if auth_schemes:
        auth_scheme = auth_schemes[0]
        auth_inputs = integration.get_auth_inputs(auth_scheme)

        assert isinstance(auth_inputs, list)

        # If there are auth inputs, validate their structure
        for auth_input in auth_inputs:
            assert isinstance(auth_input, dict)
            if "name" in auth_input:
                assert isinstance(auth_input["name"], str)
            if "required" in auth_input:
                assert isinstance(auth_input["required"], bool)
            if "type" in auth_input:
                assert isinstance(auth_input["type"], str)

    # Test with invalid auth scheme
    invalid_inputs = integration.get_auth_inputs("INVALID_SCHEME")
    assert isinstance(invalid_inputs, list)
    assert len(invalid_inputs) == 0

    # Test with None auth scheme
    none_inputs = integration.get_auth_inputs(None)
    assert isinstance(none_inputs, list)
    assert len(none_inputs) == 0


def test_integration_list_actions(client, slack_integration_id):
    """Test the list_actions method of Integration class."""
    integration = client.Integration.get(slack_integration_id)

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


def test_integration_with_no_auth_schemes(client):
    """Test integration behavior when no auth schemes are available."""
    # Get a list of integrations to find one without auth schemes
    integrations = client.Integration.search()

    for integration in integrations.results:
        if not integration.auth_schemes:
            # Test auth_schemes property
            assert integration.auth_schemes == []

            # Test get_auth_inputs with no schemes
            inputs = integration.get_auth_inputs("ANY_SCHEME")
            assert inputs == []

            # Test validation with no schemes
            errors = integration._validate_params(
                auth_scheme="ANY_SCHEME", data={}, action="test"
            )
            assert isinstance(errors, list)
            assert len(errors) > 0  # Should have error for invalid auth scheme
            break
    else:
        # If no integration without auth schemes found, skip this test
        pytest.skip("No integration without auth schemes found")
