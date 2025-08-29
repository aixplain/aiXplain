"""
Unit tests for EvolveParam base model functionality
"""

import pytest
from aixplain.modules.agent.evolve_param import (
    EvolveParam,
    EvolveType,
    validate_evolve_param,
)


class TestEvolveParam:
    """Test class for EvolveParam functionality"""

    def test_default_initialization(self):
        """Test EvolveParam default initialization"""
        default_param = EvolveParam()

        assert default_param is not None
        assert default_param.to_evolve is False
        assert default_param.evolve_type == EvolveType.TEAM_TUNING
        assert default_param.max_successful_generations == 3
        assert default_param.max_failed_generation_retries == 3
        assert default_param.max_iterations == 50
        assert default_param.max_non_improving_generations == 2
        assert default_param.llm is None
        assert default_param.additional_params == {}

        # Test to_dict method
        result_dict = default_param.to_dict()
        assert isinstance(result_dict, dict)
        assert "toEvolve" in result_dict

    def test_custom_initialization(self):
        """Test EvolveParam custom initialization"""
        custom_param = EvolveParam(
            to_evolve=True,
            max_successful_generations=5,
            max_failed_generation_retries=2,
            max_iterations=30,
            max_non_improving_generations=4,
            evolve_type=EvolveType.TEAM_TUNING,
            llm={"id": "test_llm_id", "name": "Test LLM"},
            additional_params={"customParam": "custom_value"},
        )

        assert custom_param.to_evolve is True
        assert custom_param.max_successful_generations == 5
        assert custom_param.max_failed_generation_retries == 2
        assert custom_param.max_iterations == 30
        assert custom_param.max_non_improving_generations == 4
        assert custom_param.evolve_type == EvolveType.TEAM_TUNING
        assert custom_param.llm == {"id": "test_llm_id", "name": "Test LLM"}
        assert custom_param.additional_params == {"customParam": "custom_value"}

        # Test to_dict method
        result_dict = custom_param.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["max_successful_generations"] == 5
        assert result_dict["max_failed_generation_retries"] == 2
        assert result_dict["max_iterations"] == 30
        assert result_dict["max_non_improving_generations"] == 4
        assert result_dict["evolve_type"] == EvolveType.TEAM_TUNING
        assert result_dict["llm"] == {"id": "test_llm_id", "name": "Test LLM"}
        assert result_dict["customParam"] == "custom_value"

    def test_from_dict_with_api_format(self):
        """Test EvolveParam from_dict() with API format"""
        api_dict = {
            "toEvolve": True,
            "max_successful_generations": 10,
            "max_failed_generation_retries": 4,
            "max_iterations": 40,
            "max_non_improving_generations": 5,
            "evolve_type": EvolveType.TEAM_TUNING,
            "llm": {"id": "api_llm_id", "name": "API LLM"},
            "customParam": "custom_value",
        }

        from_dict_param = EvolveParam.from_dict(api_dict)

        assert from_dict_param.to_evolve is True
        assert from_dict_param.max_successful_generations == 10
        assert from_dict_param.max_failed_generation_retries == 4
        assert from_dict_param.max_iterations == 40
        assert from_dict_param.max_non_improving_generations == 5
        assert from_dict_param.evolve_type == EvolveType.TEAM_TUNING
        assert from_dict_param.llm == {"id": "api_llm_id", "name": "API LLM"}

        # Test round-trip conversion
        result_dict = from_dict_param.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["max_successful_generations"] == 10
        assert result_dict["max_failed_generation_retries"] == 4
        assert result_dict["max_iterations"] == 40
        assert result_dict["max_non_improving_generations"] == 5

    def test_validate_evolve_param_with_none(self):
        """Test validate_evolve_param() with None input"""
        validated_none = validate_evolve_param(None)

        assert validated_none is not None
        assert isinstance(validated_none, EvolveParam)
        assert validated_none.to_evolve is False

        result_dict = validated_none.to_dict()
        assert "toEvolve" in result_dict

    def test_validate_evolve_param_with_dict(self):
        """Test validate_evolve_param() with dictionary input"""
        input_dict = {"toEvolve": True, "max_successful_generations": 5}
        validated_dict = validate_evolve_param(input_dict)

        assert isinstance(validated_dict, EvolveParam)
        assert validated_dict.to_evolve is True
        assert validated_dict.max_successful_generations == 5

        result_dict = validated_dict.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["max_successful_generations"] == 5

    def test_validate_evolve_param_with_instance(self):
        """Test validate_evolve_param() with EvolveParam instance"""
        custom_param = EvolveParam(
            to_evolve=True,
            max_successful_generations=5,
            max_failed_generation_retries=2,
            max_iterations=30,
            max_non_improving_generations=4,
            evolve_type=EvolveType.TEAM_TUNING,
            llm={"id": "instance_llm_id"},
            additional_params={"customParam": "custom_value"},
        )

        validated_instance = validate_evolve_param(custom_param)

        assert validated_instance is custom_param  # Should return the same instance
        assert validated_instance.to_evolve is True
        assert validated_instance.max_successful_generations == 5
        assert validated_instance.max_failed_generation_retries == 2

    def test_invalid_max_successful_generations_raises_error(self):
        """Test that invalid max_successful_generations raises ValueError"""
        with pytest.raises(ValueError, match="max_successful_generations must be positive"):
            EvolveParam(max_successful_generations=0)  # max_successful_generations <= 0 should fail

    def test_validate_evolve_param_missing_to_evolve_key(self):
        """Test that missing toEvolve key raises ValueError"""
        with pytest.raises(ValueError, match="evolve parameter must contain 'toEvolve' key"):
            validate_evolve_param({"no_to_evolve": True})  # Missing toEvolve key

    def test_evolve_type_enum_values(self):
        """Test that EvolveType enum values work correctly"""
        param_team_tuning = EvolveParam(evolve_type=EvolveType.TEAM_TUNING)

        assert param_team_tuning.evolve_type == EvolveType.TEAM_TUNING

        # Test in to_dict conversion
        dict_team_tuning = param_team_tuning.to_dict()

        assert "evolve_type" in dict_team_tuning

    def test_invalid_additional_params_type(self):
        """Test that invalid additional_params type raises ValueError"""
        with pytest.raises(ValueError, match="additional_params must be a dictionary"):
            EvolveParam(additional_params="not a dict")

    def test_merge_with_dict(self):
        """Test merging with a dictionary"""
        base_param = EvolveParam(to_evolve=False, max_successful_generations=3, additional_params={"base": "value"})
        merge_dict = {
            "toEvolve": True,
            "max_successful_generations": 5,
            "llm": {"id": "merged_llm_id"},
            "customParam": "custom_value",
        }

        merged = base_param.merge(merge_dict)

        assert merged.to_evolve is True
        assert merged.max_successful_generations == 5
        assert merged.llm == {"id": "merged_llm_id"}
        assert merged.additional_params == {
            "base": "value",
            "customParam": "custom_value",
        }
