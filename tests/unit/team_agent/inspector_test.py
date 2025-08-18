import pytest
from unittest.mock import patch, MagicMock
from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorPolicy,
    InspectorAuto,
    AUTO_DEFAULT_MODEL_ID,
    InspectorAction,
    InspectorOutput,
    callable_to_code_string,
    code_string_to_callable,
    get_policy_source,
)
from aixplain.factories.team_agent_factory.inspector_factory import InspectorFactory
from aixplain.enums.function import Function
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.response import ModelResponse
from aixplain.enums.response_status import ResponseStatus

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


class TestInspectorCreation:
    """Test inspector creation with various configurations"""

    def test_basic_inspector_creation(self):
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

    def test_inspector_with_callable_policy(self):
        """Test inspector creation with valid callable policy"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            if "error" in model_response.error_message.lower():
                return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
            return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)

        inspector = Inspector(
            name=INSPECTOR_CONFIG["name"],
            model_id=INSPECTOR_CONFIG["model_id"],
            model_params=INSPECTOR_CONFIG["model_config"],
            policy=process_response,
        )

        assert inspector.name == INSPECTOR_CONFIG["name"]
        assert callable(inspector.policy)
        assert inspector.policy.__name__ == "process_response"

    def test_inspector_auto_creation(self):
        """Test inspector creation with auto configuration"""
        inspector = Inspector(name="auto_inspector", auto=InspectorAuto.CORRECTNESS, policy=InspectorPolicy.WARN)

        assert inspector.name == "auto_inspector"
        assert inspector.auto == InspectorAuto.CORRECTNESS
        assert inspector.policy == InspectorPolicy.WARN
        assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
        assert inspector.model_params is None

    def test_inspector_auto_creation_with_callable_policy(self):
        """Test inspector creation with auto configuration and callable policy"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test critique", content_edited="", action=InspectorAction.RERUN)

        inspector = Inspector(name="auto_inspector", auto=InspectorAuto.CORRECTNESS, policy=process_response)

        assert inspector.name == "auto_inspector"
        assert inspector.auto == InspectorAuto.CORRECTNESS
        assert inspector.policy == process_response
        assert callable(inspector.policy)
        assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
        assert inspector.model_params is None

    def test_inspector_name_validation(self):
        """Test inspector name validation"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Inspector(name="", model_id="test_model_id")


class TestInspectorValidation:
    """Test inspector validation and error handling"""

    def test_invalid_callable_name(self):
        """Test inspector creation with callable that has wrong function name"""

        def wrong_name(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test", content_edited="", action=InspectorAction.CONTINUE)

        with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
            Inspector(
                name=INSPECTOR_CONFIG["name"],
                model_id=INSPECTOR_CONFIG["model_id"],
                model_params=INSPECTOR_CONFIG["model_config"],
                policy=wrong_name,
            )

    def test_invalid_callable_arguments(self):
        """Test inspector creation with callable that has wrong arguments"""

        def process_response(wrong_arg: ModelResponse, another_wrong_arg: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test", content_edited="", action=InspectorAction.CONTINUE)

        with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
            Inspector(
                name=INSPECTOR_CONFIG["name"],
                model_id=INSPECTOR_CONFIG["model_id"],
                model_params=INSPECTOR_CONFIG["model_config"],
                policy=process_response,
            )

    def test_invalid_callable_return_type(self):
        """Test inspector creation with callable that has wrong return type"""

        def process_response(model_response: ModelResponse, input_content: str) -> str:
            return "continue"

        with pytest.raises(ValueError, match="Policy callable must have name 'process_response'"):
            Inspector(
                name=INSPECTOR_CONFIG["name"],
                model_id=INSPECTOR_CONFIG["model_id"],
                model_params=INSPECTOR_CONFIG["model_config"],
                policy=process_response,
            )

    def test_invalid_policy_type(self):
        """Test inspector creation with invalid policy type"""
        with pytest.raises(ValueError, match="Input should be"):
            Inspector(
                name=INSPECTOR_CONFIG["name"],
                model_id=INSPECTOR_CONFIG["model_id"],
                model_params=INSPECTOR_CONFIG["model_config"],
                policy=123,  # Invalid type
            )


class TestCodeStringConversion:
    """Test conversion between callable functions and code strings"""

    def test_callable_to_code_string(self):
        """Test converting callable to code string"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            if "error" in model_response.error_message.lower():
                return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
            return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)

        code_string = callable_to_code_string(process_response)
        assert isinstance(code_string, str)
        assert "def process_response" in code_string
        assert "model_response" in code_string
        assert "input_content" in code_string
        assert "InspectorAction.ABORT" in code_string

    def test_code_string_to_callable(self):
        """Test converting code string back to callable"""
        code_string = """def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
    if "error" in model_response.error_message.lower():
        return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
    return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)"""

        func = code_string_to_callable(code_string)
        assert callable(func)
        assert func.__name__ == "process_response"

        # Test the function works correctly
        result1 = func(ModelResponse(status=ResponseStatus.FAILED, error_message="This is an error message"), "input")
        assert result1.action == InspectorAction.ABORT

        result2 = func(ModelResponse(status=ResponseStatus.SUCCESS, data="This is a normal message"), "input")
        assert result2.action == InspectorAction.CONTINUE

    def test_roundtrip_conversion(self):
        """Test that serialization and deserialization work correctly together"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            if "error" in model_response.error_message.lower():
                return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
            elif "warning" in model_response.data.lower():
                return InspectorOutput(critiques="Warning detected", content_edited="", action=InspectorAction.RERUN)
            return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)

        # Serialize
        code_string = callable_to_code_string(process_response)

        # Deserialize
        deserialized_func = code_string_to_callable(code_string)

        # Test that the deserialized function works the same
        assert (
            deserialized_func(ModelResponse(status=ResponseStatus.FAILED, error_message="error message"), "input").action
            == InspectorAction.ABORT
        )
        assert (
            deserialized_func(ModelResponse(status=ResponseStatus.SUCCESS, data="warning message"), "input").action
            == InspectorAction.RERUN
        )
        assert (
            deserialized_func(ModelResponse(status=ResponseStatus.SUCCESS, data="normal message"), "input").action
            == InspectorAction.CONTINUE
        )

    def test_source_code_preservation(self):
        """Test that code_string_to_callable preserves the original source code"""
        code_string = """def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
    if "error" in model_response.error_message.lower():
        return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
    elif "warning" in model_response.data.lower():
        return InspectorOutput(critiques="Warning detected", content_edited="", action=InspectorAction.RERUN)
    return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)"""

        func = code_string_to_callable(code_string)

        # Verify the function has the _source_code attribute
        assert hasattr(func, "_source_code")
        assert func._source_code == code_string

        # Verify the function works correctly
        assert (
            func(ModelResponse(status=ResponseStatus.FAILED, error_message="This is an error message"), "input").action
            == InspectorAction.ABORT
        )
        assert (
            func(ModelResponse(status=ResponseStatus.SUCCESS, data="This is a warning message"), "input").action
            == InspectorAction.RERUN
        )
        assert (
            func(ModelResponse(status=ResponseStatus.SUCCESS, data="This is a normal message"), "input").action
            == InspectorAction.CONTINUE
        )


class TestSourceCodeRetrieval:
    """Test source code retrieval functionality"""

    def test_get_policy_source_original_function(self):
        """Test get_policy_source with an original function (should use inspect.getsource)"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            if "error" in model_response.error_message.lower():
                return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
            return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)

        source = get_policy_source(process_response)
        assert source is not None
        assert "def process_response" in source
        assert "InspectorAction.ABORT" in source

    def test_get_policy_source_deserialized_function(self):
        """Test get_policy_source with a deserialized function (should use _source_code attribute)"""
        code_string = """def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
    if "error" in model_response.error_message.lower():
        return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
    return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)"""

        func = code_string_to_callable(code_string)

        # Verify get_policy_source works with the deserialized function
        source = get_policy_source(func)
        assert source is not None
        assert source == code_string

    def test_get_policy_source_fallback(self):
        """Test get_policy_source fallback when neither approach works"""
        # Create a function without source code info by using exec()
        # This simulates a function created dynamically where inspect.getsource() would fail
        namespace = {}
        exec(
            "def dynamic_func(x, y): return InspectorOutput(critiques='', content_edited='', action=InspectorAction.CONTINUE)",
            namespace,
        )
        func = namespace["dynamic_func"]

        # Remove any potential source code attributes
        if hasattr(func, "_source_code"):
            delattr(func, "_source_code")

        source = get_policy_source(func)
        assert source is None


class TestInspectorSerialization:
    """Test Inspector serialization and deserialization"""

    def test_model_dump_with_callable_policy(self):
        """Test that Inspector.model_dump properly serializes callable policies"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test critique", content_edited="", action=InspectorAction.ABORT)

        inspector = Inspector(
            name="test_inspector",
            model_id="test_model_id",
            policy=process_response,
        )

        data = inspector.model_dump()
        assert data["policy_type"] == "callable"
        assert isinstance(data["policy"], str)
        assert "def process_response" in data["policy"]

    def test_model_dump_with_enum_policy(self):
        """Test that Inspector.model_dump properly serializes enum policies"""
        inspector = Inspector(
            name="test_inspector",
            model_id="test_model_id",
            policy=InspectorPolicy.WARN,
        )

        data = inspector.model_dump()
        assert data["policy_type"] == "enum"
        assert data["policy"] == "warn"

    def test_model_validate_with_callable_policy(self):
        """Test that Inspector.model_validate properly deserializes callable policies"""
        inspector_data = {
            "name": "test_inspector",
            "model_id": "test_model_id",
            "policy": """def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
    return InspectorOutput(critiques="Test critique", content_edited="", action=InspectorAction.ABORT)""",
            "policy_type": "callable",
        }

        inspector = Inspector.model_validate(inspector_data)
        assert callable(inspector.policy)
        assert inspector.policy.__name__ == "process_response"
        result = inspector.policy(ModelResponse(status=ResponseStatus.SUCCESS, data="test"), "input")
        assert result.action == InspectorAction.ABORT

    def test_model_validate_with_enum_policy(self):
        """Test that Inspector.model_validate properly deserializes enum policies"""
        inspector_data = {
            "name": "test_inspector",
            "model_id": "test_model_id",
            "policy": "warn",
            "policy_type": "enum",
        }

        inspector = Inspector.model_validate(inspector_data)
        assert inspector.policy == InspectorPolicy.WARN

    def test_model_validate_fallback(self):
        """Test that Inspector.model_validate falls back to default policy on error"""
        inspector_data = {
            "name": "test_inspector",
            "model_id": "test_model_id",
            "policy": "invalid code string",
            "policy_type": "callable",
        }

        inspector = Inspector.model_validate(inspector_data)
        assert inspector.policy == InspectorPolicy.ADAPTIVE  # Default fallback

    def test_roundtrip_serialization_preserves_source_code(self):
        """Test that Inspector round-trip serialization preserves source code"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            if "error" in model_response.error_message.lower():
                return InspectorOutput(critiques="Error detected", content_edited="", action=InspectorAction.ABORT)
            elif "warning" in model_response.data.lower():
                return InspectorOutput(critiques="Warning detected", content_edited="", action=InspectorAction.RERUN)
            return InspectorOutput(critiques="No issues", content_edited="", action=InspectorAction.CONTINUE)

        # Create inspector with callable policy
        inspector = Inspector(
            name="test_inspector",
            model_id="test_model_id",
            policy=process_response,
        )

        # Serialize to dict
        inspector_dict = inspector.model_dump()
        assert inspector_dict["policy_type"] == "callable"
        assert isinstance(inspector_dict["policy"], str)

        # Deserialize from dict
        inspector_copy = Inspector.model_validate(inspector_dict)
        assert callable(inspector_copy.policy)
        assert inspector_copy.policy.__name__ == "process_response"

        # Verify the deserialized function has source code and works correctly
        assert hasattr(inspector_copy.policy, "_source_code")
        assert "def process_response" in inspector_copy.policy._source_code
        assert (
            inspector_copy.policy(
                ModelResponse(status=ResponseStatus.FAILED, error_message="This is an error message"), "input"
            ).action
            == InspectorAction.ABORT
        )
        assert (
            inspector_copy.policy(
                ModelResponse(status=ResponseStatus.SUCCESS, data="This is a warning message"), "input"
            ).action
            == InspectorAction.RERUN
        )
        assert (
            inspector_copy.policy(ModelResponse(status=ResponseStatus.SUCCESS, data="This is a normal message"), "input").action
            == InspectorAction.CONTINUE
        )


class TestInspectorFactory:
    """Test InspectorFactory functionality"""

    def test_create_from_model(self):
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

    def test_create_from_model_with_callable_policy(self):
        """Test creating inspector from model using factory with callable policy"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test critique", content_edited="", action=InspectorAction.CONTINUE)

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

    def test_create_from_model_invalid_status(self):
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

    def test_create_from_model_invalid_function(self):
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

    def test_create_auto(self):
        """Test creating auto-configured inspector using factory"""
        inspector = InspectorFactory.create_auto(
            auto=InspectorAuto.CORRECTNESS, name="custom_name", policy=InspectorPolicy.ABORT
        )

        assert inspector.name == "custom_name"
        assert inspector.auto == InspectorAuto.CORRECTNESS
        assert inspector.policy == InspectorPolicy.ABORT
        assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
        assert inspector.model_params is None

    def test_create_auto_with_callable_policy(self):
        """Test creating auto-configured inspector using factory with callable policy"""

        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            return InspectorOutput(critiques="Test critique", content_edited="", action=InspectorAction.ABORT)

        inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS, name="custom_name", policy=process_response)

        assert inspector.name == "custom_name"
        assert inspector.auto == InspectorAuto.CORRECTNESS
        assert inspector.policy == process_response
        assert callable(inspector.policy)
        assert inspector.model_id == AUTO_DEFAULT_MODEL_ID
        assert inspector.model_params is None

    def test_create_auto_default_name(self):
        """Test creating auto-configured inspector with default name"""
        inspector = InspectorFactory.create_auto(auto=InspectorAuto.CORRECTNESS)

        assert inspector.name == "inspector_correctness"
        assert inspector.auto == InspectorAuto.CORRECTNESS
        assert inspector.policy == InspectorPolicy.ADAPTIVE  # default policy
