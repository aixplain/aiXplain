"""
Unit tests for evolver LLM utility functions
"""

from unittest.mock import Mock
from aixplain.utils.evolve_utils import create_llm_dict
from aixplain.modules.model.llm_model import LLM
from aixplain.enums import Function, Supplier


class TestCreateLLMDict:
    """Test class for create_llm_dict functionality"""

    def test_create_llm_dict_with_none(self):
        """Test create_llm_dict with None input"""
        result = create_llm_dict(None)
        assert result is None

    def test_create_llm_dict_with_string_id(self):
        """Test create_llm_dict with LLM ID string"""
        llm_id = "test_llm_id_123"
        result = create_llm_dict(llm_id)

        expected = {"id": llm_id}
        assert result == expected

    def test_create_llm_dict_with_llm_object(self):
        """Test create_llm_dict with LLM object"""
        # Create a mock LLM object
        mock_llm = Mock(spec=LLM)
        mock_llm.id = "llm_id_456"
        mock_llm.name = "Test LLM Model"
        mock_llm.description = "A test LLM model for unit testing"
        mock_llm.supplier = Supplier.OPENAI
        mock_llm.version = "1.0.0"
        mock_llm.function = Function.TEXT_GENERATION
        mock_llm.temperature = 0.7

        # Mock the get_parameters method
        mock_parameters = Mock()
        mock_parameters.to_list.return_value = [
            {"name": "max_tokens", "type": "integer", "default": 2048},
            {"name": "temperature", "type": "float", "default": 0.7},
        ]
        mock_llm.get_parameters.return_value = mock_parameters

        result = create_llm_dict(mock_llm)

        expected = {
            "id": "llm_id_456",
            "name": "Test LLM Model",
            "description": "A test LLM model for unit testing",
            "supplier": "openai",
            "version": "1.0.0",
            "function": "text-generation",
            "parameters": [
                {"name": "max_tokens", "type": "integer", "default": 2048},
                {"name": "temperature", "type": "float", "default": 0.7},
            ],
            "temperature": 0.7,
        }
        assert result == expected

    def test_create_llm_dict_with_llm_object_no_parameters(self):
        """Test create_llm_dict with LLM object that has no parameters"""
        # Create a mock LLM object
        mock_llm = Mock(spec=LLM)
        mock_llm.id = "llm_id_789"
        mock_llm.name = "Simple LLM"
        mock_llm.description = "A simple LLM without parameters"
        mock_llm.supplier = Supplier.OPENAI
        mock_llm.version = "2.0.0"
        mock_llm.function = Function.TEXT_GENERATION
        mock_llm.temperature = 0.5

        # Mock get_parameters to return None
        mock_llm.get_parameters.return_value = None

        result = create_llm_dict(mock_llm)

        expected = {
            "id": "llm_id_789",
            "name": "Simple LLM",
            "description": "A simple LLM without parameters",
            "supplier": "openai",
            "version": "2.0.0",
            "function": "text-generation",
            "parameters": None,
            "temperature": 0.5,
        }
        assert result == expected

    def test_create_llm_dict_with_llm_object_no_temperature(self):
        """Test create_llm_dict with LLM object that has no temperature attribute"""
        # Create a mock LLM object without temperature
        mock_llm = Mock(spec=LLM)
        mock_llm.id = "llm_id_999"
        mock_llm.name = "No Temp LLM"
        mock_llm.description = "LLM without temperature"
        mock_llm.supplier = Supplier.GOOGLE
        mock_llm.version = "3.0.0"
        mock_llm.function = Function.TEXT_GENERATION

        # Remove temperature attribute
        del mock_llm.temperature

        # Mock get_parameters to return None
        mock_llm.get_parameters.return_value = None

        result = create_llm_dict(mock_llm)

        expected = {
            "id": "llm_id_999",
            "name": "No Temp LLM",
            "description": "LLM without temperature",
            "supplier": "google",
            "version": "3.0.0",
            "function": "text-generation",
            "parameters": None,
            "temperature": None,
        }
        assert result == expected

    def test_create_llm_dict_with_empty_string(self):
        """Test create_llm_dict with empty string"""
        result = create_llm_dict("")

        expected = {"id": ""}
        assert result == expected
