import pytest
from unittest.mock import Mock, patch
import re
from unittest.mock import MagicMock

from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.model import Model
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.base.parameters import Parameter
from aixplain.enums import AssetStatus, Function, Supplier


@pytest.fixture
def mock_model():
    model = Mock(spec=Model)
    model.id = "test_model_id"
    model.function = Function.TRANSLATION
    model.supplier = Supplier.AIXPLAIN
    model.name = "Test Model"
    model.description = "Test Model Description"
    model.status = AssetStatus.ONBOARDED
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
    assert tool.model.id == "test_model_id"
    assert tool.supplier == Supplier.AIXPLAIN
    assert tool.model == mock_model
    assert tool.description == "Test Model Description"


def test_init_with_supplier_dict():
    supplier_dict = {"code": "aixplain", "name": "aiXplain"}
    mock_enum = {"AIXPLAIN": {"id": 1, "name": "aiXplain", "code": "aixplain"}}

    with patch("aixplain.modules.agent.tool.model_tool.Supplier") as mock_supplier:
        # Create a mock for the Supplier enum
        mock_supplier.AIXPLAIN = type("MockSupplier", (), {"value": mock_enum["AIXPLAIN"], "name": "aiXplain"})()
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


def test_to_dict(mocker, mock_model, mock_model_factory):
    mock_model_factory.get.return_value = mock_model

    mocker.patch("aixplain.modules.agent.tool.model_tool.set_tool_name", return_value="test_tool_name")

    tool = ModelTool(
        model="test_model_id",
        description="Test description",
        parameters=[{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
    )

    expected = {
        "function": mock_model.function.value,
        "type": "model",
        "name": "test_tool_name",
        "description": "Test description",
        "supplier": mock_model.supplier.value["code"],
        "version": None,
        "assetId": "test_model_id",
        "parameters": [{"name": "sourcelanguage", "value": "en"}, {"name": "targetlanguage", "value": "es"}],
        "status": mock_model.status.value,
    }

    result = tool.to_dict()
    assert result == expected


@pytest.mark.parametrize("model_exists", [True, False])
def test_validate(mock_model, mock_model_factory, model_exists):
    if model_exists:
        mock_model_factory.get.return_value = mock_model
        tool = ModelTool(model="test_model_id", api_key=None)
        assert tool.model == mock_model
    else:
        mock_model_factory.get.side_effect = Exception("Model not found")
        with pytest.raises(Exception, match="Model Tool Unavailable"):
            tool = ModelTool(model="nonexistent_model", api_key=None)


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
def test_validate_parameters(mocker, mock_model, params, expected_result, error_expected, error_message):
    mocker.patch("aixplain.factories.model_factory.ModelFactory.get", return_value=mock_model)
    tool = ModelTool(model=mock_model.id, function=Function.TRANSLATION)

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


@pytest.mark.parametrize(
    "tool_name,expected_name",
    [
        ("custom_tool", "custom_tool"),
        ("", "translation-aixplain-test_model"),  # Test empty name
        ("translation_model", "translation_model"),
        (None, "translation-aixplain-test_model"),  # Test None value should default to empty string
    ],
)
def test_tool_name(mock_model, mock_model_factory, tool_name, expected_name):
    mock_model_factory.get.return_value = mock_model
    tool = ModelTool(model="test_model_id", name=tool_name, function=Function.TRANSLATION)
    assert tool.name == expected_name
    # Verify name appears correctly in dictionary representation
    tool_dict = tool.to_dict()
    assert tool_dict["name"] == expected_name


def test_invalid_modeltool(mocker):
    mocker.patch("aixplain.factories.model_factory.ModelFactory.get", side_effect=Exception())
    with pytest.raises(Exception) as exc_info:
        model_tool = ModelTool(model="309851793")
        model_tool.validate()
    assert str(exc_info.value) == "Model Tool Unavailable. Make sure Model '309851793' exists or you have access to it."


def test_validate_model_tool_with_function():
    model_tool = ModelTool(function="text-generation")
    assert model_tool.function == Function.TEXT_GENERATION
    assert model_tool.description != ""


def test_validate_model_tool_with_model(mocker):
    mocker.patch(
        "aixplain.factories.model_factory.ModelFactory.get",
        return_value=Model(
            id="309851793", name="Test Model", description="Test Model Description", function=Function.TEXT_GENERATION
        ),
    )
    model_tool = ModelTool(model="309851793", function=Function.TRANSLATION)
    assert model_tool.model.id == "309851793"
    assert model_tool.function == Function.TEXT_GENERATION
    assert model_tool.description != ""


def test_validate_model_tool_without_function_or_model():
    with pytest.raises(Exception) as exc_info:
        ModelTool()
    assert str(exc_info.value) == "Agent Creation Error: Either function or model must be provided when instantiating a tool."
