import pytest
import requests_mock
from aixplain.factories.model_factory import ModelFactory
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.enums import DataType, Function
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
                    code="def main(originCode: str)",
                    output_examples="output_description",
                )
                assert utility_model.id == "123"
                assert utility_model.name == "utility_model_test"
                assert utility_model.description == "utility_model_test"
                assert utility_model.code == "utility_model_test"
                assert utility_model.inputs == [
                    UtilityModelInput(name="originCode", description="The originCode input is a text", type=DataType.TEXT)
                ]
                assert utility_model.output_examples == "output_description"


def test_utility_model_with_invalid_name():
    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="utility_model_test"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="utility_model_test"):
            with patch(
                "aixplain.modules.model.utils.parse_code",
                return_value=(
                    "def main(originCode: str)",
                    [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                    "utility_model_test",
                ),
            ):
                with pytest.raises(Exception) as exc_info:
                    ModelFactory.create_utility_model(
                        name="",
                        description="utility_model_test",
                        code="def main(originCode: str)",
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
                    "def main(originCode: str)",
                    [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
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
                }


def test_update_utility_model():
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="def main(originCode: str)"):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="def main(originCode: str)"):
                with patch(
                    "aixplain.modules.model.utils.parse_code",
                    return_value=(
                        "def main(originCode: str)",
                        [UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        "utility_model_test",
                    ),
                ):
                    mock.put(urljoin(config.BACKEND_URL, "sdk/utilities/123"), json={"id": "123"})
                    utility_model = UtilityModel(
                        id="123",
                        name="utility_model_test",
                        description="utility_model_test",
                        code="def main(originCode: str)",
                        output_examples="output_description",
                        inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        function=Function.UTILITIES,
                        api_key=config.TEAM_API_KEY,
                    )
                    utility_model.description = "updated_description"
                    utility_model.update()

                    assert utility_model.id == "123"
                    assert utility_model.description == "updated_description"


def test_delete_utility_model():
    with requests_mock.Mocker() as mock:
        with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="def main(originCode: str)"):
            with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="def main(originCode: str)"):
                mock.delete(urljoin(config.BACKEND_URL, "sdk/utilities/123"), status_code=200, json={"id": "123"})
                utility_model = UtilityModel(
                    id="123",
                    name="utility_model_test",
                    description="utility_model_test",
                    code="def main(originCode: str)",
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
            code_link, inputs, description = parse_code(code)
            assert inputs == [
                UtilityModelInput(name="originCode", description="The originCode input is a text", type=DataType.TEXT)
            ]
            assert description == ""
            assert code_link == "code_link"

    # Code is a function
    def main(a: int, b: int):
        """
        This function adds two numbers
        """
        return a + b

    with patch("aixplain.factories.file_factory.FileFactory.to_link", return_value="code_link"):
        with patch("aixplain.factories.file_factory.FileFactory.upload", return_value="code_link"):
            code = main
            code_link, inputs, description = parse_code(code)
            assert inputs == [
                UtilityModelInput(name="a", description="The a input is a number", type=DataType.NUMBER),
                UtilityModelInput(name="b", description="The b input is a number", type=DataType.NUMBER),
            ]
            assert description == "This function adds two numbers"
            assert code_link == "code_link"

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
