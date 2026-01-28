from typing import Dict, Any
from aixplain.base.parameters import BaseParameters, Parameter


class ModelParameters(BaseParameters):
    def __init__(self, input_params: Dict[str, Dict[str, Any]]) -> None:
        """Initialize ModelParameters with input parameters dictionary.

        Args:
            input_params (Dict[str, Dict[str, Any]]): Dictionary containing parameter configurations
        """
        super().__init__()
        for param_name, param_config in input_params.items():
            self.parameters[param_name] = Parameter(
                name=param_name,
                required=param_config.get("required", False),
                is_fixed=param_config.get("isFixed", False),
                values=param_config.get("values", []),
                default_values=param_config.get("defaultValues", []),
                available_options=param_config.get("availableOptions", []),
                data_type=param_config.get("dataType"),
                data_sub_type=param_config.get("dataSubType"),
                multiple_values=param_config.get("multipleValues", False),
            )
