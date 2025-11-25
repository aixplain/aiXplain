import pytest
from aixplain import Aixplain
import os


@pytest.fixture
def api_keys():
    return {"key_a": "api_key_a_123", "key_b": "api_key_b_456"}


def test_multiple_aixplain_instances_api_key_context(api_keys):
    """Test that multiple Aixplain instances maintain separate API keys."""
    aix_a = Aixplain(api_keys["key_a"])
    aix_b = Aixplain(api_keys["key_b"])

    # Check that the context is set correctly
    assert aix_a.api_key == api_keys["key_a"]
    assert aix_b.api_key == api_keys["key_b"]
    assert aix_a.Model.context.api_key == api_keys["key_a"]
    assert aix_b.Model.context.api_key == api_keys["key_b"]


def test_api_key_utility_method_priority(api_keys):
    """Test that API key is correctly set in context."""
    aix_a = Aixplain(api_keys["key_a"])
    # Should use context API key
    assert aix_a.Model.context.api_key == api_keys["key_a"]


def test_multiple_instances_independence(api_keys):
    """Test that multiple instances are truly independent."""
    aix_a = Aixplain(api_keys["key_a"])
    aix_b = Aixplain(api_keys["key_b"])

    # Verify they have different API keys
    assert aix_a.api_key != aix_b.api_key
    assert aix_a.Model.context.api_key != aix_b.Model.context.api_key

    # Verify they have different contexts
    assert aix_a.Model.context is not aix_b.Model.context

    # Verify they have different clients
    assert aix_a.client is not aix_b.client


def test_resource_context_isolation(api_keys):
    """Test that each resource maintains its own context with correct key."""
    aix_a = Aixplain(api_keys["key_a"])
    aix_b = Aixplain(api_keys["key_b"])

    # Test all resource types have correct context
    resources_a = [
        aix_a.Model,
        aix_a.Agent,
        aix_a.Utility,
        aix_a.Tool,
        aix_a.Integration,
        aix_a.Resource,
        aix_a.Inspector,
    ]

    resources_b = [
        aix_b.Model,
        aix_b.Agent,
        aix_b.Utility,
        aix_b.Tool,
        aix_b.Integration,
        aix_b.Resource,
        aix_b.Inspector,
    ]

    # All resources in instance A should have key_a
    for resource in resources_a:
        assert resource.context.api_key == api_keys["key_a"]

    # All resources in instance B should have key_b
    for resource in resources_b:
        assert resource.context.api_key == api_keys["key_b"]


def test_client_initialization(api_keys):
    """Test that each instance has its own client with the correct API key."""
    aix_a = Aixplain(api_keys["key_a"])
    aix_b = Aixplain(api_keys["key_b"])

    # Each instance should have its own client
    assert aix_a.client is not aix_b.client

    # Each client should have the correct API key
    assert aix_a.client.team_api_key == api_keys["key_a"]
    assert aix_b.client.team_api_key == api_keys["key_b"]


def test_url_configuration(api_keys):
    """Test that each instance can have different URL configurations."""
    custom_backend = "https://custom-backend.com"
    custom_pipeline = "https://custom-pipeline.com"
    custom_model = "https://custom-model.com"

    aix_custom = Aixplain(
        api_keys["key_a"],
        backend_url=custom_backend,
        pipeline_url=custom_pipeline,
        model_url=custom_model,
    )

    assert aix_custom.backend_url == custom_backend
    assert aix_custom.pipeline_url == custom_pipeline
    assert aix_custom.model_url == custom_model


def test_api_key_validation():
    """Test that API key validation works correctly."""
    # Save original value
    original_key = os.environ.get("TEAM_API_KEY")

    try:
        # Remove the environment variable to test the assertion
        if "TEAM_API_KEY" in os.environ:
            del os.environ["TEAM_API_KEY"]

        # Should raise assertion error when no API key is provided
        with pytest.raises(AssertionError):
            Aixplain(api_key=None)

        # Should work with valid API key
        aix = Aixplain("valid_api_key_123")
        assert aix.api_key == "valid_api_key_123"

    finally:
        # Restore original value
        if original_key is not None:
            os.environ["TEAM_API_KEY"] = original_key


def test_context_api_key_retrieval(api_keys):
    """Test that the context API key can be retrieved correctly."""
    aix_a = Aixplain(api_keys["key_a"])

    # Test direct access
    assert aix_a.Model.context.api_key == api_keys["key_a"]


def test_multiple_instances_with_same_api_key():
    """Test that multiple instances with the same API key work correctly."""
    same_key = "same_api_key_123"

    aix_1 = Aixplain(same_key)
    aix_2 = Aixplain(same_key)

    # They should have the same API key but different instances
    assert aix_1.api_key == aix_2.api_key
    assert aix_1 is not aix_2
    assert aix_1.Model.context is not aix_2.Model.context
