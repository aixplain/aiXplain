import pytest
from unittest.mock import patch, MagicMock
from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorPolicy,
    InspectorAuto,
    AUTO_DEFAULT_MODEL_ID,
    InspectorAction,
)
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

MOCK_MODEL_RESPONSE = {
    "id": "test_model_id",
    "name": "test_model",
    "description": "Test model description",
    "createdAt": "2024-03-20T10:00:00Z",
    "supplier": "test_supplier",
    "pricing": {"per_token": 0.001},
    "version": {"id": "v1"},
    "params": [],
    "attributes": [],
    "api_key": "test_api_key",
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


def test_inspector_creation_with_callable_policy():
    """Test inspector creation with valid callable policy"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        if "error" in model_response.lower():
            return InspectorAction.ABORT
        return InspectorAction.CONTINUE

    inspector = Inspector(
        name=INSPECTOR_CONFIG["name"],
        model_id=INSPECTOR_CONFIG["model_id"],
        model_params=INSPECTOR_CONFIG["model_config"],
        policy=process_response,
    )

    assert inspector.name == INSPECTOR_CONFIG["name"]
    assert inspector.model_id == INSPECTOR_CONFIG["model_id"]
    assert inspector.model_params == INSPECTOR_CONFIG["model_config"]
    assert inspector.policy == process_response
    assert callable(inspector.policy)


def test_inspector_creation_with_invalid_callable_name():
    """Test inspector creation with callable that has wrong function name"""

    def wrong_name(model_response: str, input_content: str) -> InspectorAction:
        return InspectorAction.CONTINUE

    with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
        Inspector(
            name=INSPECTOR_CONFIG["name"],
            model_id=INSPECTOR_CONFIG["model_id"],
            model_params=INSPECTOR_CONFIG["model_config"],
            policy=wrong_name,
        )


def test_inspector_creation_with_invalid_callable_arguments():
    """Test inspector creation with callable that has wrong arguments"""

    def process_response(wrong_arg: str, another_wrong_arg: str) -> InspectorAction:
        return InspectorAction.CONTINUE

    with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
        Inspector(
            name=INSPECTOR_CONFIG["name"],
            model_id=INSPECTOR_CONFIG["model_id"],
            model_params=INSPECTOR_CONFIG["model_config"],
            policy=process_response,
        )


def test_inspector_creation_with_invalid_callable_return_type():
    """Test inspector creation with callable that has wrong return type"""

    def process_response(model_response: str, input_content: str) -> str:
        return "continue"

    with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
        Inspector(
            name=INSPECTOR_CONFIG["name"],
            model_id=INSPECTOR_CONFIG["model_id"],
            model_params=INSPECTOR_CONFIG["model_config"],
            policy=process_response,
        )


def test_inspector_creation_with_invalid_policy_type():
    """Test inspector creation with invalid policy type"""
    with pytest.raises(ValueError, match="Input should be"):
        Inspector(
            name=INSPECTOR_CONFIG["name"],
            model_id=INSPECTOR_CONFIG["model_id"],
            model_params=INSPECTOR_CONFIG["model_config"],
            policy=123,  # Invalid type
        )


def test_inspector_auto_creation():
    """Test inspector creation with auto configuration"""
    inspector = Inspector(name="auto_inspector", auto=InspectorAuto.CORRECTNESS, policy=InspectorPolicy.WARN)

    assert inspector.name == "auto_inspector"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.WARN
    assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
    assert inspector.model_params is None


def test_inspector_auto_creation_with_callable_policy():
    """Test inspector creation with auto configuration and callable policy"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        return InspectorAction.RERUN

    inspector = Inspector(name="auto_inspector", auto=InspectorAuto.CORRECTNESS, policy=process_response)

    assert inspector.name == "auto_inspector"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == process_response
    assert callable(inspector.policy)
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
    mock_response.json.return_value = {
        **MOCK_MODEL_RESPONSE,
        "status": AssetStatus.ONBOARDED.value,
        "function": {"id": Function.GUARDRAILS.value},
    }

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        inspector = InspectorFactory.create_from_model(
            name=INSPECTOR_CONFIG["name"],
            model=INSPECTOR_CONFIG["model_id"],
            model_config=INSPECTOR_CONFIG["model_config"],
            policy=INSPECTOR_CONFIG["policy"],
        )

        assert inspector.name == INSPECTOR_CONFIG["name"]
        assert inspector.model_id == INSPECTOR_CONFIG["model_id"]
        assert inspector.model_params == INSPECTOR_CONFIG["model_config"]
        assert inspector.policy == INSPECTOR_CONFIG["policy"]


def test_inspector_factory_create_from_model_with_callable_policy():
    """Test creating inspector from model using factory with callable policy"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        return InspectorAction.CONTINUE

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        **MOCK_MODEL_RESPONSE,
        "status": AssetStatus.ONBOARDED.value,
        "function": {"id": Function.GUARDRAILS.value},
    }

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        inspector = InspectorFactory.create_from_model(
            name=INSPECTOR_CONFIG["name"],
            model=INSPECTOR_CONFIG["model_id"],
            model_config=INSPECTOR_CONFIG["model_config"],
            policy=process_response,
        )

        assert inspector.name == INSPECTOR_CONFIG["name"]
        assert inspector.model_id == INSPECTOR_CONFIG["model_id"]
        assert inspector.model_params == INSPECTOR_CONFIG["model_config"]
        assert inspector.policy == process_response
        assert callable(inspector.policy)


def test_inspector_factory_create_from_model_invalid_status():
    """Test creating inspector from model with invalid status"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        **MOCK_MODEL_RESPONSE,
        "status": AssetStatus.DRAFT.value,
        "function": {"id": Function.GUARDRAILS.value},
    }

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        with pytest.raises(ValueError, match="is not onboarded"):
            InspectorFactory.create_from_model(
                name=INSPECTOR_CONFIG["name"],
                model=INSPECTOR_CONFIG["model_id"],
                model_config=INSPECTOR_CONFIG["model_config"],
                policy=INSPECTOR_CONFIG["policy"],
            )


def test_inspector_factory_create_from_model_invalid_function():
    """Test creating inspector from model with invalid function"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        **MOCK_MODEL_RESPONSE,
        "status": AssetStatus.ONBOARDED.value,
        "function": {"id": Function.TRANSLATION.value},
    }

    with patch("aixplain.factories.team_agent_factory.inspector_factory._request_with_retry", return_value=mock_response):
        with pytest.raises(ValueError, match="models are supported"):
            InspectorFactory.create_from_model(
                name=INSPECTOR_CONFIG["name"],
                model=INSPECTOR_CONFIG["model_id"],
                model_config=INSPECTOR_CONFIG["model_config"],
                policy=INSPECTOR_CONFIG["policy"],
            )


def test_inspector_factory_create_auto():
    """Test creating auto-configured inspector using factory"""
    inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS, name="custom_name", policy=InspectorPolicy.ABORT)

    assert inspector.name == "custom_name"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.ABORT
    assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
    assert inspector.model_params is None


def test_inspector_factory_create_auto_with_callable_policy():
    """Test creating auto-configured inspector using factory with callable policy"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        return InspectorAction.ABORT

    inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS, name="custom_name", policy=process_response)

    assert inspector.name == "custom_name"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == process_response
    assert callable(inspector.policy)
    assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
    assert inspector.model_params is None


def test_inspector_factory_create_auto_default_name():
    """Test creating auto-configured inspector with default name"""
    inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS)

    assert inspector.name == "inspector_correctness"
    assert inspector.auto == InspectorAuto.CORRECTNESS
    assert inspector.policy == InspectorPolicy.ADAPTIVE  # default policy
