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
            self.parameters[param_name] = Parameter(name=param_name, required=param_config["required"])
