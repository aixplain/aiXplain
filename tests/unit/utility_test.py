import pytest
import requests_mock
from aixplain.factories.model_factory import ModelFactory
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.enums import DataType, Function
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.utility_model import UtilityModel, UtilityModelInput
from aixplain.modules.model.utils import parse_code
from unittest.mock import patch


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
                assert utility_model.inputs == [UtilityModelInput(name="input_string", description="The input_string input is a text", type=DataType.TEXT)]
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
                    "status": AssetStatus.ONBOARDED.value,
                }


def test_update_utility_model():
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
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
                        match="update\(\) is deprecated and will be removed in a future version. Please use save\(\) instead.",
                    ):
                        utility_model.description = "updated_description"
                        utility_model.update()

                    assert utility_model.id == model_id
                    assert utility_model.description == "updated_description"


def test_save_utility_model():
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
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

                    import warnings

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
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
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
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value='def main(input_string:str):\n    """\n    Get driving directions from start_location to end_location\n    """\n    return f"This is the output for input: {input_string}"\n'):
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
