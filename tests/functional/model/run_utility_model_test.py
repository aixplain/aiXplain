from aixplain.factories import ModelFactory
from aixplain.modules.model.utility_model import UtilityModelInput, utility_tool
from aixplain.enums import DataType, AssetStatus
import pytest



def test_run_utility_model():
    utility_model = None
    try:
        inputs = [
            UtilityModelInput(name="inputA", description="The inputA input is a text", type=DataType.TEXT),
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


def test_utility_model_update():
    utility_model = None
    updated_model = None
    final_model = None
    try:
        # Define initial model with string concatenation
        def concat_strings(str1: str, str2: str):
            """Concatenates two strings.

            Args:
                str1: The first string.
                str2: The second string.

            Returns:
                The concatenated string.
            """
            return str1 + str2

        # Create and deploy the utility model
        utility_model = ModelFactory.create_utility_model(
            name="concat_strings_test",
            description="Initial string concatenation utility",
            code=concat_strings,
        )
        assert utility_model.status == AssetStatus.DRAFT
        utility_model.deploy()

        assert utility_model.status == AssetStatus.ONBOARDED

        # Verify initial state
        assert utility_model.name == "concat_strings_test"
        assert utility_model.description == "Initial string concatenation utility"
        assert len(utility_model.inputs) == 2
        assert utility_model.inputs[0].name == "str1"
        assert utility_model.inputs[1].name == "str2"

        # Test initial behavior
        response = utility_model.run({"str1": "Hello, ", "str2": "World!"})
        assert response.status == "SUCCESS"
        assert response.data == "Hello, World!"

        # Define new function with different signature
        def sum_numbers(num1: int, num2: int):
            """Sums two numbers.

            Args:
                num1: The first number.
                num2: The second number.

            Returns:
                The sum of the two numbers.
            """
            return num1 + num2

        # Update model with new name, description, and code
        utility_model.name = "sum_numbers_test"
        utility_model.description = "Updated to sum numbers utility"
        utility_model.code = sum_numbers
        utility_model.save()

        # Verify updated state
        updated_model = ModelFactory.get(utility_model.id)
        assert updated_model.status == AssetStatus.ONBOARDED
        assert updated_model.name == "sum_numbers_test"
        assert updated_model.description == "Updated to sum numbers utility"
        assert len(updated_model.inputs) == 2
        assert updated_model.inputs[0].name == "num1"
        assert updated_model.inputs[1].name == "num2"

        # Test updated behavior with new function
        response = updated_model.run({"num1": 5, "num2": 7})
        assert response.status == "SUCCESS"
        assert response.data == "12"

        # Test partial update - only update code, keeping name and description
        def multiply_numbers(num1: int, num2: int):
            """Multiplies two numbers.

            Args:
                num1: The first number.
                num2: The second number.

            Returns:
                The product of the two numbers.
            """
            return num1 * num2

        updated_model.code = multiply_numbers
        assert updated_model.status == AssetStatus.ONBOARDED
        # the next line should raise an exception
        with pytest.raises(Exception, match=".*UtilityModel is already deployed*"):
            updated_model.deploy()

        updated_model.save()
        assert updated_model.status == AssetStatus.ONBOARDED

        # Verify partial update
        final_model = ModelFactory.get(utility_model.id)
        assert final_model.name == "sum_numbers_test"
        assert final_model.description == "Updated to sum numbers utility"
        assert final_model.status == AssetStatus.ONBOARDED

        # Test final behavior with new function but same input field names
        response = final_model.run({"num1": 5, "num2": 7})
        assert response.status == "SUCCESS"
        assert response.data == "35"

    finally:
        if utility_model:
            utility_model.delete()
        if updated_model:
            updated_model.delete()
        if final_model:
            final_model.delete()


def test_model_tool_creation():
    from aixplain.factories import AgentFactory
    import warnings

    # Capture warnings during the create_model_tool call
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")
        # Create the model tool
        AgentFactory.create_model_tool(model="6736411cf127849667606689")  # Tavily Search
        # Check that no warnings were raised
        assert len(w) == 0, f"Warning was raised when calling create_model_tool: {[warning.message for warning in w]}"
