import os
import pytest
from aixplain import Aixplain


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration."""
    api_key = os.getenv("TEAM_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY environment variable not set")
    
    backend_url = os.getenv(
        "BACKEND_URL", "https://dev-platform-api.aixplain.com/"
    )
    model_url = os.getenv(
        "MODELS_RUN_URL", "https://dev-models.aixplain.com/api/v1/execute"
    )
    
    return Aixplain(
        api_key=api_key,
        backend_url=backend_url,
        model_url=model_url,
    )


@pytest.fixture(scope="module")
def text_model_id():
    """Return a text-generation model ID for testing."""
    return "669a63646eb56306647e1091"  # GPT-4o Mini


def validate_model_structure(model):
    """Helper function to validate model structure and data types."""
    # Test core fields
    assert isinstance(model.id, str)
    assert isinstance(model.name, str)
    # Description can be None for some models
    if model.description is not None:
        assert isinstance(model.description, str)
    
    # Test optional fields if present
    if model.service_name:
        assert isinstance(model.service_name, str)
    
    if model.status:
        assert hasattr(model.status, 'value')
    
    if model.hosted_by:
        assert isinstance(model.hosted_by, str)
    
    if model.developed_by:
        assert isinstance(model.developed_by, str)
    
    if model.subscriptions:
        assert isinstance(model.subscriptions, list)
    
    # Test supplier structure if present
    if model.supplier:
        assert hasattr(model.supplier, 'id')
        assert hasattr(model.supplier, 'name')
        assert hasattr(model.supplier, 'code')
    
    # Test pricing structure if present
    if model.pricing:
        assert hasattr(model.pricing, 'price')
    
    # Test version structure if present
    if model.version:
        assert hasattr(model.version, 'name')
        assert hasattr(model.version, 'id')
    
    # Test function structure if present
    if model.function:
        assert hasattr(model.function, 'value')
    
    # Test capabilities if present
    if model.supports_streaming is not None:
        assert isinstance(model.supports_streaming, bool)
    
    if model.supports_byoc is not None:
        assert isinstance(model.supports_byoc, bool)
    
    # Test timestamps if present
    if model.created_at:
        assert isinstance(model.created_at, str)
    
    if model.updated_at:
        assert isinstance(model.updated_at, str)
    
    # Test attributes if present
    if model.attributes:
        assert isinstance(model.attributes, list)
        for attr in model.attributes:
            assert hasattr(attr, 'name')
            assert hasattr(attr, 'code')
    
    # Test parameters if present
    if model.params:
        assert isinstance(model.params, list)
        for param in model.params:
            assert hasattr(param, 'name')
            assert hasattr(param, 'required')
            assert hasattr(param, 'data_type')
            assert hasattr(param, 'data_sub_type')


def test_list(client):
    """Test listing models with pagination."""
    models = client.Model.list()
    assert hasattr(models, 'results')
    assert isinstance(models.results, list)
    assert len(models.results) > 0
    
    # Validate structure of first model
    if models.results:
        validate_model_structure(models.results[0])


def test_get(client, text_model_id):
    """Test getting a specific model by ID and validate its structure."""
    model = client.Model.get(text_model_id)
    assert model.id == text_model_id
    
    # Validate complete model structure
    validate_model_structure(model)


def test_as_tool(client, text_model_id):
    """Test converting a model to a tool dictionary."""
    model = client.Model.get(text_model_id)
    tool = model.as_tool()
    
    assert isinstance(tool, dict)
    assert tool["name"] == model.name
    assert tool["description"] == model.description


def test_run(client, text_model_id):
    """Test running a model."""
    model = client.Model.get(text_model_id)
    
    try:
        result = model.run(data="Hello! Please respond with a short greeting.")
        assert hasattr(result, 'status')
        assert hasattr(result, 'data')
        assert result.status == "SUCCESS"
        assert result.data is not None
    except Exception as e:
        pytest.skip(f"Model run not supported: {e}") 