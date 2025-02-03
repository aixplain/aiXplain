import pytest
from unittest.mock import Mock, patch
import re
from unittest.mock import MagicMock

from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.model import Model
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.base.parameters import Parameter


@pytest.fixture
def mock_model():
    model = Mock(spec=Model)
    model.id = "test_model_id"
    model.function = Function.TRANSLATION
    model.supplier = Supplier.AIXPLAIN
    model.name = "Test Model"
    model.model_params = ModelParameters(
        {
            "sourcelanguage": {"name": "sourcelanguage", "required": True},
            "targetlanguage": {"name": "targetlanguage", "required": True},
        }
    )
    return model


@pytest.fixture
def mock_model_factory():
    with patch("aixplain.factories.model_factory.ModelFactory") as factory:
        yield factory


@pytest.mark.parametrize(
    "function_input,expected_function",
    [
        (Function.TRANSLATION, Function.TRANSLATION),
        ("translation", Function.TRANSLATION),
    ],
)
def test_init_with_function(function_input, expected_function):
    tool = ModelTool(function=function_input)
    assert tool.function == expected_function
    assert tool.model is None
    assert tool.supplier is None


def test_init_with_model(mock_model, mock_model_factory):
    mock_model_factory.get.return_value = mock_model
    tool = ModelTool(model="test_model_id")
    assert tool.function == Function.TRANSLATION
    assert tool.model == "test_model_id"
    assert tool.supplier == Supplier.AIXPLAIN
    assert tool.model_object == mock_model


def test_init_with_supplier_dict():
    supplier_dict = {"code": "aixplain", "name": "aiXplain"}
    mock_enum = {"AIXPLAIN": {"id": 1, "name": "aiXplain", "code": "aixplain"}}

    with patch("aixplain.modules.agent.tool.model_tool.Supplier") as mock_supplier:
        # Create a mock for the Supplier enum
        mock_supplier.AIXPLAIN = type("MockSupplier", (), {"value": mock_enum["AIXPLAIN"]})()
        mock_supplier.return_value = mock_supplier.AIXPLAIN

        tool = ModelTool(function=Function.TRANSLATION, supplier=supplier_dict)
        assert tool.supplier == mock_supplier.AIXPLAIN


@pytest.mark.parametrize(
    "error_case,expected_error,expected_message",
    [
        (lambda: ModelTool(), AssertionError, "Either function or model must be provided"),
        (
            lambda: ModelTool(function=Function.UTILITIES),
            AssertionError,
            "Utility function must be used with an associated model",
        ),
    ],
)
def test_init_validation_errors(error_case, expected_error, expected_message):
    with pytest.raises(expected_error, match=expected_message):
        error_case()


def test_to_dict(mock_model, mock_model_factory):
    mock_model_factory.get.return_value = mock_model
    tool = ModelTool(
        model="test_model_id",
        description="Test description",
        parameters=[{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
    )

    expected = {
        "function": mock_model.function.value,
        "type": "model",
        "description": "Test description",
        "supplier": mock_model.supplier.value["code"],
        "version": None,
        "assetId": "test_model_id",
        "parameters": [{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
    }

    result = tool.to_dict()
    assert result == expected


@pytest.mark.parametrize("model_exists", [True, False])
def test_validate(mock_model, mock_model_factory, model_exists):
    if model_exists:
        mock_model_factory.get.return_value = mock_model
        with patch.object(ModelTool, "__init__", return_value=None):
            tool = ModelTool()
            tool.model = "test_model_id"
            tool.api_key = None
            validated_model = tool.validate()
            assert validated_model == mock_model
    else:
        mock_model_factory.get.side_effect = Exception("Model not found")
        with patch.object(ModelTool, "__init__", return_value=None):
            tool = ModelTool()
            tool.model = "nonexistent_model"
            tool.api_key = None
            with pytest.raises(Exception, match="Model Tool Unavailable"):
                tool.validate()


def test_get_parameters():
    with patch.object(ModelTool, "validate_parameters", return_value={"sourcelanguage": "en", "targetlanguage": "es"}):
        tool = ModelTool(function=Function.TRANSLATION, parameters={"sourcelanguage": "en", "targetlanguage": "es"})
        assert tool.get_parameters() == {"sourcelanguage": "en", "targetlanguage": "es"}


@pytest.mark.parametrize(
    "params,expected_result,error_expected,error_message",
    [
        (
            [{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
            [{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
            False,
            None,
        ),
        (
            [{"name": "invalid_param", "value": "value"}],
            None,
            True,
            "Invalid parameters provided: {'invalid_param'}. Expected parameters are: ",
        ),
        (None, None, False, None),
    ],
)
def test_validate_parameters(mock_model, params, expected_result, error_expected, error_message):
    with patch.object(ModelTool, "__init__", return_value=None):
        tool = ModelTool()
        tool.model_object = mock_model
        tool.function = Function.TRANSLATION

        # Mock the model parameters
        mock_params = MagicMock()
        mock_params.parameters = {
            "sourcelanguage": Parameter(name="sourcelanguage", required=True),
            "targetlanguage": Parameter(name="targetlanguage", required=True),
        }
        # Mock the to_list method to return None when no parameters are set
        mock_params.to_list.return_value = None
        mock_model.model_params = mock_params

        if error_expected:
            with pytest.raises(ValueError, match=re.escape(error_message)):
                tool.validate_parameters(params)
        else:
            result = tool.validate_parameters(params)
            assert result == expected_result
