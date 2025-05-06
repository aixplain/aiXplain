import pytest
import requests_mock
from aixplain.factories.model_factory import ModelFactory
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.enums import DataType, Function
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.utility_model import UtilityModel, UtilityModelInput
from aixplain.modules.model.utils import parse_code, parse_code_decorated
from unittest.mock import patch, MagicMock
import warnings


def test_utility_model():
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="utility_model_test"):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="utility_model_test"):
                mock.post(urljoin(config.BACKEND_URL, "sdk/utilities"), json={"id": "123"})
                utility_model = ModelFactory.create_utility_model(
                    name="utility_model_test",
                    description="utility_model_test",
                    code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                    output_examples="output_description",
                )
                assert utility_model.id == "123"
                assert utility_model.name == "utility_model_test"
                assert utility_model.description == "utility_model_test"
                assert utility_model.code == "utility_model_test"
                assert utility_model.inputs == [
                    UtilityModelInput(name="input_string", description="The input_string input is a text", type=DataType.TEXT)
                ]
                assert utility_model.output_examples == "output_description"


def test_utility_model_with_invalid_name():
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="utility_model_test"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="utility_model_test"):
            with patch(
                "aixplain.modules.model.utils.parse_code",
                return_value=(
                    'def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                    [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                    "utility_model_test",
                    "utility_model_test",
                ),
            ):
                with pytest.raises(Exception) as exc_info:
                    ModelFactory.create_utility_model(
                        name="",
                        description="utility_model_test",
                        code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                        inputs=[],
                        output_examples="output_description",
                    )
                assert str(exc_info.value) == "Name is required"


def test_utility_model_to_dict():
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="utility_model_test"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="utility_model_test"):
            with patch(
                "aixplain.modules.model.utils.parse_code",
                return_value=(
                    'def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                    [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                    "utility_model_test",
                    "utility_model_test",
                ),
            ):
                utility_model = UtilityModel(
                    id="123",
                    name="utility_model_test",
                    description="utility_model_test",
                    code="utility_model_test",
                    output_examples="output_description",
                    inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                    function=Function.UTILITIES,
                    api_key=config.TEAM_API_KEY,
                )
                assert utility_model.to_dict() == {
                    "name": "utility_model_test",
                    "description": "utility_model_test",
                    "inputs": [{"name": "originCode", "description": "originCode", "type": "text"}],
                    "code": "utility_model_test",
                    "function": "utilities",
                    "outputDescription": "output_description",
                    "status": AssetStatus.DRAFT.value,
                }


def test_update_utility_model():
    with requests_mock.Mocker() as mock:
        with patch(
            "aixplain.factories.file_factory.FileFactory.to_link",
            return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
        ):
            with patch(
                "aixplain.factories.file_factory.FileFactory.upload",
                return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
            ):
                with patch(
                    "aixplain.modules.model.utils.parse_code",
                    return_value=(
                        'def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                        [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        "utility_model_test",
                        "utility_model_test",
                    ),
                ):
                    # Mock both the model existence check and update endpoints
                    model_id = "123"
                    mock.get(urljoin(config.BACKEND_URL, f"sdk/models/{model_id}"), status_code=200)
                    mock.put(urljoin(config.BACKEND_URL, f"sdk/utilities/{model_id}"), json={"id": model_id})

                    utility_model = UtilityModel(
                        id=model_id,
                        name="utility_model_test",
                        description="utility_model_test",
                        code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                        output_examples="output_description",
                        inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        function=Function.UTILITIES,
                        api_key=config.TEAM_API_KEY,
                    )

                    with pytest.warns(
                        DeprecationWarning,
                        match=r"update\(\) is deprecated and will be removed in a future version. Please use save\(\) instead.",
                    ):
                        utility_model.description = "updated_description"
                        utility_model.update()

                    assert utility_model.id == model_id
                    assert utility_model.description == "updated_description"


def test_save_utility_model():
    with requests_mock.Mocker() as mock:
        with patch(
            "aixplain.factories.file_factory.FileFactory.to_link",
            return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
        ):
            with patch(
                "aixplain.factories.file_factory.FileFactory.upload",
                return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
            ):
                with patch(
                    "aixplain.modules.model.utils.parse_code",
                    return_value=(
                        'def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                        [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        "utility_model_test",
                        "utility_model_test",
                    ),
                ):
                    # Mock both the model existence check and the update endpoint
                    model_id = "123"
                    mock.get(urljoin(config.BACKEND_URL, f"sdk/models/{model_id}"), status_code=200)
                    mock.put(urljoin(config.BACKEND_URL, f"sdk/utilities/{model_id}"), json={"id": model_id})

                    utility_model = UtilityModel(
                        id=model_id,
                        name="utility_model_test",
                        description="utility_model_test",
                        code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                        output_examples="output_description",
                        inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        function=Function.UTILITIES,
                        api_key=config.TEAM_API_KEY,
                    )

                    # it should not trigger any warning
                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("always")  # Trigger all warnings
                        utility_model.description = "updated_description"
                        utility_model.save()

                        assert len(w) == 0

                    assert utility_model.id == model_id
                    assert utility_model.description == "updated_description"


def test_delete_utility_model():
    with requests_mock.Mocker() as mock:
        with patch(
            "aixplain.factories.file_factory.FileFactory.to_link",
            return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
        ):
            with patch(
                "aixplain.factories.file_factory.FileFactory.upload",
                return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
            ):
                mock.delete(urljoin(config.BACKEND_URL, "sdk/utilities/123"), status_code=200, json={"id": "123"})
                utility_model = UtilityModel(
                    id="123",
                    name="utility_model_test",
                    description="utility_model_test",
                    code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
                    output_examples="output_description",
                    inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                    function=Function.UTILITIES,
                    api_key=config.TEAM_API_KEY,
                )
                utility_model.delete()
                assert mock.called


def test_parse_code():
    # Code is a string
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="code_link"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="code_link"):
            code = "def main(originCode: str) -> str:\n    return originCode"
            code_link, inputs, description, name = parse_code(code)
            assert inputs == [
                UtilityModelInput(name="originCode", description="The originCode input is a text", type=DataType.TEXT)
            ]
            assert description == ""
            assert code_link == "code_link"
            assert name == "main"

    # Code is a function
    def main(a: int, b: int):
        """
        This function adds two numbers
        """
        return a + b

    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="code_link"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="code_link"):
            code = main
            code_link, inputs, description, name = parse_code(code)
            assert inputs == [
                UtilityModelInput(name="a", description="The a input is a number", type=DataType.NUMBER),
                UtilityModelInput(name="b", description="The b input is a number", type=DataType.NUMBER),
            ]
            assert description == "This function adds two numbers"
            assert code_link == "code_link"
            assert name == "main"

    # Code must have a main function
    code = "def wrong_function_name(originCode: str) -> str:\n    return originCode"
    with pytest.raises(Exception) as exc_info:
        parse_code(code)
    assert str(exc_info.value) == "Utility Model Error: Code must have a main function"

    # Input type is required
    def main(originCode):
        return originCode

    with pytest.raises(Exception) as exc_info:
        parse_code(main)
    assert str(exc_info.value) == "Utility Model Error: Input type is required. For instance def main(a: int, b: int) -> int:"

    # Unsupported input type
    code = "def main(originCode: list) -> str:\n    return originCode"
    with pytest.raises(Exception) as exc_info:
        parse_code(code)
    assert str(exc_info.value) == "Utility Model Error: Unsupported input type: list"


def test_validate_new_model():
    """Test validation for a new model"""
    with patch(
        "aixplain.factories.file_factory.FileFactory.to_link",
        return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
    ):
        with patch(
            "aixplain.factories.file_factory.FileFactory.upload",
            return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
        ):
            # Test with valid inputs
            utility_model = UtilityModel(
                id="",  # Empty ID for new model
                name="utility_model_test",
                description="utility_model_test",
                code="def main(originCode: str):\n    return originCode",
                output_examples="output_description",
                function=Function.UTILITIES,
                api_key=config.TEAM_API_KEY,
            )
            utility_model.validate()  # Should not raise any exception

            # Test with empty name
            utility_model.name = ""
            with pytest.raises(Exception) as exc_info:
                utility_model.validate()
            assert str(exc_info.value) == "Name is required"

            # Test with empty description
            utility_model.name = "utility_model_test"
            utility_model.description = ""
            with pytest.raises(Exception) as exc_info:
                utility_model.validate()
            assert str(exc_info.value) == "Description is required"

            # Test with empty code
            utility_model.description = "utility_model_test"
            utility_model.code = ""
            with pytest.raises(Exception) as exc_info:
                utility_model.validate()

            assert str(exc_info.value) == "Utility Model Error: Code must have a main function"


def test_validate_existing_model():
    """Test validation for an existing model with S3 code"""
    with requests_mock.Mocker() as mock:
        model_id = "123"
        # Mock the model existence check
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        mock.get(url, status_code=200)

        utility_model = UtilityModel(
            id=model_id,
            name="utility_model_test",
            description="utility_model_test",
            code="s3://bucket/path/to/code",
            output_examples="output_description",
            function=Function.UTILITIES,
            api_key=config.TEAM_API_KEY,
        )
        utility_model.validate()  # Should not raise any exception


def test_model_exists_success():
    """Test _model_exists when model exists"""
    with requests_mock.Mocker() as mock:
        model_id = "123"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        mock.get(url, status_code=200)

        utility_model = UtilityModel(
            id=model_id,
            name="utility_model_test",
            description="utility_model_test",
            code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
            output_examples="output_description",
            function=Function.UTILITIES,
            api_key=config.TEAM_API_KEY,
        )
        assert utility_model._model_exists() is True


def test_model_exists_failure():
    """Test _model_exists when model doesn't exist"""
    with requests_mock.Mocker() as mock:
        model_id = "123"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        mock.get(url, status_code=404)

        utility_model = UtilityModel(
            id=model_id,
            name="utility_model_test",
            description="utility_model_test",
            code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
            output_examples="output_description",
            function=Function.UTILITIES,
            api_key=config.TEAM_API_KEY,
        )
        with pytest.raises(Exception):
            utility_model._model_exists()


def test_model_exists_empty_id():
    """Test _model_exists with empty ID"""
    utility_model = UtilityModel(
        id="",  # Empty ID
        name="utility_model_test",
        description="utility_model_test",
        code='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n',
        output_examples="output_description",
        function=Function.UTILITIES,
        api_key=config.TEAM_API_KEY,
    )
    assert utility_model._model_exists() is False


def test_utility_model_with_return_annotation():
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="utility_model_test"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="utility_model_test"):

            def get_location(input_str: str) -> str:
                """
                Get location information

                Args:
                    input_str (str): Input string parameter
                Returns:
                    str: Location information
                """
                return input_str

            utility_model = UtilityModel(
                id="123",
                name="location_test",
                description="Get location information",
                code=get_location,
                output_examples="Location data example",
                inputs=[UtilityModelInput(name="input_str", description="Input string parameter", type=DataType.TEXT)],
                function=Function.UTILITIES,
                api_key=config.TEAM_API_KEY,
            )

            # Verify the model is created correctly with the return type annotation
            assert utility_model.id == "123"
            assert utility_model.name == "location_test"
            assert utility_model.description == "Get location information"
            assert len(utility_model.inputs) == 1
            assert utility_model.inputs[0].name == "input_str"
            assert utility_model.inputs[0].type == DataType.TEXT
            assert utility_model.inputs[0].description == "Input string parameter"

            # Verify the function parameters are parsed correctly
            code, inputs, description, name = parse_code_decorated(get_location)
            assert len(inputs) == 1
            assert inputs[0].name == "input_str"
            assert inputs[0].type == DataType.TEXT
            assert "Get location information" in description
            assert name == "get_location"


def test_parse_code_with_class():
    """Test that parsing code with a class raises proper error"""

    class DummyModel:
        def __init__(self):
            pass

    # Test with class
    with pytest.raises(
        TypeError,
        match=r"Code must be either a string or a callable function, not a class or class instance\. You tried to pass a class or class instance: <.*\.DummyModel object at 0x[0-9a-f]+>",
    ):
        parse_code_decorated(DummyModel())

    # Test with class instance
    with pytest.raises(
        TypeError,
        match=r"Code must be either a string or a callable function, not a class or class instance\. You tried to pass a class or class instance: <.*\.DummyModel object at 0x[0-9a-f]+>",
    ):
        parse_code_decorated(DummyModel())


def test_utility_model_creation_warning():
    """Test that appropriate warnings are shown during utility model creation and validation"""
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="s3://bucket/path/to/code"):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://bucket/path/to/code"):
                # Mock the model creation
                model_id = "123"
                mock.post(urljoin(config.BACKEND_URL, "sdk/utilities"), json={"id": model_id})

                # Mock the model existence check
                mock.get(urljoin(config.BACKEND_URL, f"sdk/models/{model_id}"), status_code=200)

                # Create the utility model and check for warning during creation
                with pytest.warns(UserWarning, match="WARNING: Non-deployed utility models .* will expire after 24 hours.*"):
                    utility_model = ModelFactory.create_utility_model(
                        name="utility_model_test",
                        description="utility_model_test",
                        code='def main(input_string:str):\n    return f"Test output: {input_string}"\n',
                        output_examples="output_description",
                    )

                # Verify initial status is DRAFT
                assert utility_model.status == AssetStatus.DRAFT


def test_utility_model_status_after_deployment():
    """Test that model status is updated correctly after deployment"""
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="s3://bucket/path/to/code"):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://bucket/path/to/code"):
                # Mock the model creation
                model_id = "123"
                mock.post(urljoin(config.BACKEND_URL, "sdk/utilities"), json={"id": model_id})

                # Mock the model existence check
                mock.get(urljoin(config.BACKEND_URL, f"sdk/models/{model_id}"), status_code=200)

                # Create the utility model
                utility_model = ModelFactory.create_utility_model(
                    name="utility_model_test",
                    description="utility_model_test",
                    code='def main(input_string:str):\n    return f"Test output: {input_string}"\n',
                    output_examples="output_description",
                )

                # Verify initial status is DRAFT
                assert utility_model.status == AssetStatus.DRAFT

                # Mock the model existence check and update endpoints
                mock.put(
                    urljoin(config.BACKEND_URL, f"sdk/utilities/{model_id}"),
                    json={"id": model_id, "status": AssetStatus.ONBOARDED.value},
                )

                # Deploy the model
                utility_model.deploy()

                # Verify the status is updated to ONBOARDED
                assert utility_model.status == AssetStatus.ONBOARDED

                # Verify no warning is shown after deployment
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    utility_model.validate()
                    assert len(w) == 0


def test_concat_strings():
    """Test the concat_strings function directly."""
    assert concat_strings("Hello, ", "World!") == "Hello, World!"
    assert concat_strings("", "") == ""
    assert concat_strings("123", "456") == "123456"


def concat_strings(str1: str, str2: str):
    """Concatenates two strings.

    Args:
      str1: The first string.
      str2: The second string.

    Returns:
      The concatenated string.
    """
    return str1 + str2


@patch("aixplain.factories.ModelFactory")
def test_create_and_deploy_utility_model(mock_model_factory):
    """Test creating and deploying a utility model with mocked backend requests."""
    # Mock the create_utility_model method
    mock_utility_model = MagicMock()
    mock_utility_model.id = "mock-utility-model-id"
    mock_model_factory.create_utility_model.return_value = mock_utility_model

    # Mock the get method
    mock_model = MagicMock()
    mock_model_factory.get.return_value = mock_model

    # Create utility model
    from aixplain.factories import ModelFactory

    utility_model = ModelFactory.create_utility_model(
        name="concat_strings",
        code=concat_strings,
    )

    # Assert create_utility_model was called with correct parameters
    mock_model_factory.create_utility_model.assert_called_once()

    # Get the model with mocked id
    model = ModelFactory.get(utility_model.id)

    # Assert get was called with the correct id
    mock_model_factory.get.assert_called_once()

    # Deploy the model
    model.deploy()

    # Assert deploy was called
    mock_model.deploy.assert_called_once()
