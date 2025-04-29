import pytest
from unittest.mock import patch, MagicMock
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy, InspectorAuto, AUTO_DEFAULT_MODEL_ID
from aixplain.factories.team_agent_factory.inspector_factory import InspectorFactory
from aixplain.enums.function import Function
from aixplain.enums.asset_status import AssetStatus

# Test data
INSPECTOR_CONFIG = {
    "name": "test_inspector",
    "model_id": "test_model_id",
    "model_config": {"prompt": "Check if the data is safe to use."},
    "policy": InspectorPolicy.ADAPTIVE,
}


def test_inspector_creation():
    """Test basic inspector creation with valid parameters"""
    inspector = Inspector(
        name=INSPECTOR_CONFIG["name"],
        model_id=INSPECTOR_CONFIG["model_id"],
        model_params=INSPECTOR_CONFIG["model_config"],
        policy=INSPECTOR_CONFIG["policy"],
    )

    assert inspector.name == INSPECTOR_CONFIG["name"]
    assert inspector.model_id == INSPECTOR_CONFIG["model_id"]
    assert inspector.model_params == INSPECTOR_CONFIG["model_config"]
    assert inspector.policy == INSPECTOR_CONFIG["policy"]
    assert inspector.auto is None


def test_inspector_auto_creation():
    """Test inspector creation with auto configuration"""
    inspector = Inspector(name="auto_inspector", auto=InspectorAuto.CORRECTNESS, policy=InspectorPolicy.WARN)

    assert inspector.name == "auto_inspector"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.WARN
    assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
    assert inspector.model_params is None


def test_inspector_name_validation():
    """Test inspector name validation"""
    with pytest.raises(ValueError, match="name cannot be empty"):
        Inspector(name="", model_id="test_model_id")


def test_inspector_factory_create_from_model():
    """Test creating inspector from model using factory"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": AssetStatus.ONBOARDED, "function": {"id": Function.GUARDRAILS.value}}

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        inspector = InspectorFactory.create_from_model(**INSPECTOR_CONFIG)

        assert inspector.name == INSPECTOR_CONFIG["name"]
        assert inspector.model_id == INSPECTOR_CONFIG["model_id"]
        assert inspector.model_params == INSPECTOR_CONFIG["model_config"]
        assert inspector.policy == INSPECTOR_CONFIG["policy"]


def test_inspector_factory_create_from_model_invalid_status():
    """Test creating inspector from model with invalid status"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "draft", "function": {"id": Function.GUARDRAILS.value}}

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        with pytest.raises(ValueError, match="is not onboarded"):
            InspectorFactory.create_from_model(**INSPECTOR_CONFIG)


def test_inspector_factory_create_from_model_invalid_function():
    """Test creating inspector from model with invalid function"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": AssetStatus.ONBOARDED, "function": {"id": "invalid_function"}}

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        with pytest.raises(ValueError, match="Only Guardrail models are supported"):
            InspectorFactory.create_from_model(**INSPECTOR_CONFIG)


def test_inspector_factory_create_auto():
    """Test creating auto-configured inspector using factory"""
    inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS, name="custom_name", policy=InspectorPolicy.ABORT)

    assert inspector.name == "custom_name"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.ABORT
    assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
    assert inspector.model_params is None


def test_inspector_factory_create_auto_default_name():
    """Test creating auto-configured inspector with default name"""
    inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS)

    assert inspector.name == "inspector_correctness"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.ADAPTIVE  # default policy
