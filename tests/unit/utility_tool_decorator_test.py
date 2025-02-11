import pytest
from aixplain.enums import DataType
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.utility_model import utility_tool, UtilityModelInput


def test_utility_tool_basic_decoration():
    """Test basic decoration with minimal parameters"""

    @utility_tool(name="test_function", description="Test function description")
    def test_func(input_text: str) -> str:
        return input_text

    assert hasattr(test_func, "_is_utility_tool")
    assert test_func._is_utility_tool is True
    assert test_func._tool_name == "test_function"
    assert test_func._tool_description == "Test function description"
    assert test_func._tool_inputs == []
    assert test_func._tool_output_examples == ""
    assert test_func._tool_status == AssetStatus.DRAFT


def test_utility_tool_with_all_parameters():
    """Test decoration with all optional parameters"""
    inputs = [
        UtilityModelInput(name="text_input", type=DataType.TEXT, description="A text input"),
        UtilityModelInput(name="num_input", type=DataType.NUMBER, description="A number input"),
    ]

    @utility_tool(
        name="full_test_function",
        description="Full test function description",
        inputs=inputs,
        output_examples="Example output: Hello World",
        status=AssetStatus.ONBOARDED,
    )
    def test_func(text_input: str, num_input: int) -> str:
        return f"{text_input} {num_input}"

    assert test_func._is_utility_tool is True
    assert test_func._tool_name == "full_test_function"
    assert test_func._tool_description == "Full test function description"
    assert len(test_func._tool_inputs) == 2
    assert test_func._tool_inputs == inputs
    assert test_func._tool_output_examples == "Example output: Hello World"
    assert test_func._tool_status == AssetStatus.ONBOARDED


def test_utility_tool_function_still_callable():
    """Test that decorated function remains callable"""

    @utility_tool(name="callable_test", description="Test function callable")
    def test_func(x: int, y: int) -> int:
        return x + y

    assert test_func(2, 3) == 5
    assert test_func._is_utility_tool is True


def test_utility_tool_invalid_inputs():
    """Test validation of invalid inputs"""
    with pytest.raises(ValueError):

        @utility_tool(name="", description="Test description")  # Empty name should raise error
        def test_func():
            pass

    with pytest.raises(ValueError):

        @utility_tool(name="test_name", description="")  # Empty description should raise error
        def test_func():
            pass
