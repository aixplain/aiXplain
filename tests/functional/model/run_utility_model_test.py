from aixplain.factories import ModelFactory
from aixplain.modules.model.utility_model import UtilityModelInput, utility_tool
from aixplain.enums import DataType, AssetStatus
import pytest


def test_run_utility_model():
    utility_model = None
    try:
        inputs = [
            UtilityModelInput(name="inputA", description="input A is the only input", type=DataType.TEXT),
        ]

        output_description = "An example is 'test'"

        utility_model = ModelFactory.create_utility_model(
            name="test_script",
            description="This is a test script",
            inputs=inputs,
            code="def main(inputA: str):\n\treturn inputA",
            output_examples=output_description,
        )

        assert utility_model.id is not None
        assert utility_model.inputs == inputs
        assert utility_model.output_examples == output_description
        response = utility_model.run(data={"inputA": "test"})
        assert response.status == "SUCCESS"
        assert response.data == "test"

        utility_model.code = "def main(inputA: str):\n\treturn 5"
        utility_model.save()
        response = utility_model.run(data={"inputA": "test"})
        assert response.status == "SUCCESS"
        assert str(response.data) == "5"
    finally:
        if utility_model:
            utility_model.delete()


def test_utility_model_with_decorator():
    utility_model = None
    try:

        @utility_tool(
            name="add_numbers_test name",
            description="Adds two numbers together.",
            inputs=[
                UtilityModelInput(name="num1", type=DataType.NUMBER, description="The first number."),
                UtilityModelInput(name="num2", type=DataType.NUMBER, description="The second number."),
            ],
        )
        def add_numbers(num1: int, num2: int) -> int:
            return num1 + num2

        utility_model = ModelFactory.create_utility_model(code=add_numbers)

        assert utility_model.id is not None
        assert len(utility_model.inputs) == 2
        assert utility_model.inputs[0].name == "num1"
        assert utility_model.inputs[1].name == "num2"

        response = utility_model.run(data={"num1": 1, "num2": 2})
        assert response.status == "SUCCESS"
        assert response.data == str(3)
    finally:
        if utility_model:
            utility_model.delete()


def test_utility_model_string_concatenation():
    utility_model = None
    try:

        @utility_tool(
            name="concatenate_strings",
            description="Concatenates two strings.",
            inputs=[
                UtilityModelInput(name="str1", type=DataType.TEXT, description="The first string."),
                UtilityModelInput(name="str2", type=DataType.TEXT, description="The second string."),
            ],
        )
        def concatenate_strings(str1: str, str2: str) -> str:
            """Concatenates two strings and returns the result."""
            return str1 + str2

        utility_model = ModelFactory.create_utility_model(
            name="Concatenate Strings Test",
            code=concatenate_strings,
        )

        assert utility_model.id is not None
        assert len(utility_model.inputs) == 2
        assert utility_model.inputs[0].type == DataType.TEXT
        assert utility_model.inputs[1].type == DataType.TEXT

        response = utility_model.run(data={"str1": "Hello", "str2": "World"})
        assert response.status == "SUCCESS"
        assert response.data == "HelloWorld"
    finally:
        if utility_model:
            utility_model.delete()


def test_utility_model_code_as_string():
    utility_model = None
    try:
        code = """
    @utility_tool(
        name="multiply_numbers",
        description="Multiply two numbers.",
    )
    def multiply_numbers(int1: int, int2: int) -> int:
        \"\"\"Multiply two numbers and returns the result.\"\"\"
        return int1 * int2
    """
        utility_model = ModelFactory.create_utility_model(name="Multiply Numbers Test", code=code)

        assert utility_model.id is not None
        assert len(utility_model.inputs) == 2

        response = utility_model.run(data={"int1": 2, "int2": 3})
        assert response.status == "SUCCESS"
        assert response.data == str(6)
    finally:
        if utility_model:
            utility_model.delete()


def test_utility_model_simple_function():
    utility_model = None
    try:

        def test_string(input: str):
            """test string"""
            return input

        utility_model = ModelFactory.create_utility_model(
            name="String Model Test",
            code=test_string,
        )

        assert utility_model.id is not None
        assert len(utility_model.inputs) == 1
        assert utility_model.inputs[0].type == DataType.TEXT

        response = utility_model.run(data={"input": "Hello World"})
        assert response.status == "SUCCESS"
        assert response.data == "Hello World"
    finally:
        if utility_model:
            utility_model.delete()


def test_utility_model_status():
    utility_model = None
    try:

        def get_user_location(dummy_input: str, dummy_input2: str) -> str:
            """Get user's city using dummy input"""
            import requests
            import json

            try:
                response = requests.get("http://ip-api.com/json/")
                response.raise_for_status()
                data = response.json()
                location = {"city": data["city"], "latitude": data["lat"], "longitude": data["lon"]}
                return json.dumps(location)
            except Exception as e:
                return json.dumps({"error": str(e)})

        utility_model = ModelFactory.create_utility_model(
            name="Location Utility Test",
            code=get_user_location,
        )

        # Test model creation
        assert utility_model.id is not None
        assert len(utility_model.inputs) == 2
        assert utility_model.inputs[0].name == "dummy_input"
        assert utility_model.inputs[1].name == "dummy_input2"
        assert utility_model.inputs[0].type == DataType.TEXT
        assert utility_model.inputs[1].type == DataType.TEXT

        # Check initial status is DRAFT
        assert utility_model.status == AssetStatus.DRAFT

        # deploy the model
        utility_model.deploy()

        # Check status is now ONBOARDED
        assert utility_model.status == AssetStatus.ONBOARDED

        # try  reinitialize the model this should fail
        # Second deployment attempt - should fail
        utility_model_duplicate = ModelFactory.create_utility_model(
            name="Location Utility Test",  # Same name
            code=get_user_location,
        )

        # Be more specific about the exception you're expecting
        with pytest.raises(Exception, match=".*Utility name already exists*"):
            utility_model_duplicate.deploy()

    finally:
        if utility_model:
            utility_model.delete()
        if utility_model_duplicate:
            utility_model_duplicate.delete()
