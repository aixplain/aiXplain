import pytest
import requests_mock
from aixplain.factories.model_factory import ModelFactory
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.enums import DataType, Function
from aixplain.modules.model.utility_model import UtilityModel, UtilityModelInput
from unittest.mock import patch


def test_utility_model():
    with requests_mock.Mocker() as mock:
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
                    mock.post(urljoin(config.BACKEND_URL, "sdk/utilities"), json={"id": "123"})
                    utility_model = ModelFactory.create_utility_model(
                        name="utility_model_test",
                        description="utility_model_test",
                        code="def main(originCode: str)",
                        inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        output_description="output_description",
                    )
                    assert utility_model.id == "123"
                    assert utility_model.name == "utility_model_test"
                    assert utility_model.description == "utility_model_test"
                    assert utility_model.code == "utility_model_test"
                    assert utility_model.inputs == [
                        UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)
                    ]
                    assert utility_model.output_description == "output_description"


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
                        output_description="output_description",
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
                    code="def main(originCode: str)",
                    output_description="output_description",
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
                        output_description="output_description",
                        inputs=[UtilityModelInput(name="originCode", description="originCode", type=DataType.TEXT)],
                        function=Function.UTILITIES,
                        api_key=config.TEAM_API_KEY,
                    )
                    utility_model.description = "updated_description"
                    utility_model.update()

                    assert utility_model.id == "123"
                    assert utility_model.description == "updated_description"
