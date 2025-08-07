import pytest
from unittest.mock import patch, MagicMock
from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorPolicy,
    InspectorAuto,
    AUTO_DEFAULT_MODEL_ID,
    InspectorAction,
    callable_to_code_string,
    code_string_to_callable,
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


def test_callable_to_code_string():
    """Test converting callable to code string"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        if "error" in model_response.lower():
            return InspectorAction.ABORT
        return InspectorAction.CONTINUE

    code_string = callable_to_code_string(process_response)
    assert isinstance(code_string, str)
    assert "def process_response" in code_string
    assert "model_response" in code_string
    assert "input_content" in code_string
    assert "InspectorAction.ABORT" in code_string


def test_code_string_to_callable():
    """Test converting code string back to callable"""
    code_string = """def process_response(model_response: str, input_content: str) -> InspectorAction:
    if "error" in model_response.lower():
        return InspectorAction.ABORT
    return InspectorAction.CONTINUE"""

    func = code_string_to_callable(code_string)
    assert callable(func)
    assert func.__name__ == "process_response"

    # Test the function works correctly
    result1 = func("This is an error message", "input")
    assert result1 == InspectorAction.ABORT

    result2 = func("This is a normal message", "input")
    assert result2 == InspectorAction.CONTINUE


def test_serialization_deserialization_roundtrip():
    """Test that serialization and deserialization work correctly together"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        if "error" in model_response.lower():
            return InspectorAction.ABORT
        elif "warning" in model_response.lower():
            return InspectorAction.RERUN
        return InspectorAction.CONTINUE

    # Serialize
    code_string = callable_to_code_string(process_response)

    # Deserialize
    deserialized_func = code_string_to_callable(code_string)

    # Test that the deserialized function works the same
    assert deserialized_func("error message", "input") == InspectorAction.ABORT
    assert deserialized_func("warning message", "input") == InspectorAction.RERUN
    assert deserialized_func("normal message", "input") == InspectorAction.CONTINUE


def test_inspector_model_dump_with_callable():
    """Test that Inspector.model_dump properly serializes callable policies"""

    def process_response(model_response: str, input_content: str) -> InspectorAction:
        return InspectorAction.ABORT

    inspector = Inspector(
        name="test_inspector",
        model_id="test_model_id",
        policy=process_response,
    )

    data = inspector.model_dump()
    assert data["policy_type"] == "callable"
    assert isinstance(data["policy"], str)
    assert "def process_response" in data["policy"]


def test_inspector_model_dump_with_enum():
    """Test that Inspector.model_dump properly serializes enum policies"""
    inspector = Inspector(
        name="test_inspector",
        model_id="test_model_id",
        policy=InspectorPolicy.WARN,
    )

    data = inspector.model_dump()
    assert data["policy_type"] == "enum"
    assert data["policy"] == "warn"


def test_inspector_model_validate_with_callable():
    """Test that Inspector.model_validate properly deserializes callable policies"""
    inspector_data = {
        "name": "test_inspector",
        "model_id": "test_model_id",
        "policy": """def process_response(model_response: str, input_content: str) -> InspectorAction:
    return InspectorAction.ABORT""",
        "policy_type": "callable",
    }

    inspector = Inspector.model_validate(inspector_data)
    assert callable(inspector.policy)
    assert inspector.policy.__name__ == "process_response"
    assert inspector.policy("test", "input") == InspectorAction.ABORT


def test_inspector_model_validate_with_enum():
    """Test that Inspector.model_validate properly deserializes enum policies"""
    inspector_data = {
        "name": "test_inspector",
        "model_id": "test_model_id",
        "policy": "warn",
        "policy_type": "enum",
    }

    inspector = Inspector.model_validate(inspector_data)
    assert inspector.policy == InspectorPolicy.WARN


def test_inspector_model_validate_fallback():
    """Test that Inspector.model_validate falls back to default policy on error"""
    inspector_data = {
        "name": "test_inspector",
        "model_id": "test_model_id",
        "policy": "invalid code string",
        "policy_type": "callable",
    }

    inspector = Inspector.model_validate(inspector_data)
    assert inspector.policy == InspectorPolicy.ADAPTIVE  # Default fallback


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
