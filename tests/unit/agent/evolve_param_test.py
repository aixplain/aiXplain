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
        assert default_param.criteria is None
        assert default_param.max_iterations == 100
        assert default_param.temperature == 0.0
        assert default_param.type == EvolveType.TEAM_TUNING
        assert default_param.additional_params == {}

        # Test to_dict method
        result_dict = default_param.to_dict()
        assert isinstance(result_dict, dict)
        assert "toEvolve" in result_dict

    def test_custom_initialization(self):
        """Test EvolveParam custom initialization"""
        custom_param = EvolveParam(
            to_evolve=True,
            criteria="accuracy > 0.8",
            max_iterations=5,
            temperature=0.7,
            type=EvolveType.TEAM_TUNING,
            additional_params={"customParam": "custom_value"},
        )

        assert custom_param.to_evolve is True
        assert custom_param.criteria == "accuracy > 0.8"
        assert custom_param.max_iterations == 5
        assert custom_param.temperature == 0.7
        assert custom_param.type == EvolveType.TEAM_TUNING
        assert custom_param.additional_params == {"customParam": "custom_value"}

        # Test to_dict method
        result_dict = custom_param.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["criteria"] == "accuracy > 0.8"
        assert result_dict["maxIterations"] == 5
        assert result_dict["temperature"] == 0.7
        assert result_dict["type"] == EvolveType.TEAM_TUNING
        assert result_dict["customParam"] == "custom_value"

    def test_from_dict_with_api_format(self):
        """Test EvolveParam from_dict() with API format"""
        api_dict = {
            "toEvolve": True,
            "criteria": "custom criteria",
            "maxIterations": 10,
            "temperature": 0.5,
            "type": EvolveType.TEAM_TUNING,
            "customParam": "custom_value",
        }

        from_dict_param = EvolveParam.from_dict(api_dict)

        assert from_dict_param.to_evolve is True
        assert from_dict_param.criteria == "custom criteria"
        assert from_dict_param.max_iterations == 10
        assert from_dict_param.temperature == 0.5
        assert from_dict_param.type == EvolveType.TEAM_TUNING

        # Test round-trip conversion
        result_dict = from_dict_param.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["criteria"] == "custom criteria"
        assert result_dict["maxIterations"] == 10
        assert result_dict["temperature"] == 0.5

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
        input_dict = {"toEvolve": True, "temperature": 0.3}
        validated_dict = validate_evolve_param(input_dict)

        assert isinstance(validated_dict, EvolveParam)
        assert validated_dict.to_evolve is True
        assert validated_dict.temperature == 0.3

        result_dict = validated_dict.to_dict()
        assert result_dict["toEvolve"] is True
        assert result_dict["temperature"] == 0.3

    def test_validate_evolve_param_with_instance(self):
        """Test validate_evolve_param() with EvolveParam instance"""
        custom_param = EvolveParam(
            to_evolve=True,
            criteria="accuracy > 0.8",
            max_iterations=5,
            temperature=0.7,
            type=EvolveType.TEAM_TUNING,
            additional_params={"customParam": "custom_value"},
        )

        validated_instance = validate_evolve_param(custom_param)

        assert validated_instance is custom_param  # Should return the same instance
        assert validated_instance.to_evolve is True
        assert validated_instance.criteria == "accuracy > 0.8"
        assert validated_instance.max_iterations == 5

    def test_invalid_temperature_raises_error(self):
        """Test that invalid temperature raises ValueError"""
        with pytest.raises(ValueError, match="temperature"):
            EvolveParam(temperature=1.5)  # Temperature > 1.0 should fail

    def test_validate_evolve_param_missing_to_evolve_key(self):
        """Test that missing toEvolve key raises ValueError"""
        with pytest.raises(ValueError, match="toEvolve"):
            validate_evolve_param({"no_to_evolve": True})  # Missing toEvolve key

    def test_evolve_type_enum_values(self):
        """Test that EvolveType enum values work correctly"""
        param_team_tuning = EvolveParam(type=EvolveType.TEAM_TUNING)

        assert param_team_tuning.type == EvolveType.TEAM_TUNING

        # Test in to_dict conversion
        dict_team_tuning = param_team_tuning.to_dict()

        assert "type" in dict_team_tuning

    def test_empty_criteria_handling(self):
        """Test that empty criteria is handled properly"""
        param = EvolveParam(criteria="")

        assert param.criteria == ""

        result_dict = param.to_dict()
        assert result_dict["criteria"] == ""

    def test_none_criteria_handling(self):
        """Test that None criteria is handled properly"""
        param = EvolveParam(criteria=None)

        assert param.criteria is None

        result_dict = param.to_dict()
        assert "criteria" not in result_dict
