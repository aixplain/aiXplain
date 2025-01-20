from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Parameter:
    name: str
    required: bool
    value: Optional[Any] = None


class ModelParameters:
    def __init__(self, input_params: Dict[str, Dict[str, Any]]) -> None:
        """Initialize ModelParameters with input parameters dictionary.

        Args:
            input_params (Dict[str, Dict[str, Any]]): Dictionary containing parameter configurations
        """
        self.parameters: Dict[str, Parameter] = {}

        for param_name, param_config in input_params.items():
            self.parameters[param_name] = Parameter(name=param_config["name"], required=param_config["required"])

    def get_parameter(self, name: str) -> Optional[Parameter]:
        """Get a parameter by name.

        Args:
            name (str): Name of the parameter

        Returns:
            Optional[Parameter]: Parameter object if found, None otherwise
        """
        return self.parameters.get(name)

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert parameters back to dictionary format.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary representation of parameters
        """
        return {param.name: {"required": param.required, "value": param.value} for param in self.parameters.values()}

    def __str__(self) -> str:
        """Create a pretty string representation of the parameters.

        Returns:
            str: Formatted string showing all parameters
        """
        if not self.parameters:
            return "No parameters defined"

        lines = ["Model Parameters:"]
        for param in self.parameters.values():
            value_str = str(param.value) if param.value is not None else "Not set"
            required_str = "(Required)" if param.required else "(Optional)"
            lines.append(f"  - {param.name}: {value_str} {required_str}")

        return "\n".join(lines)

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting parameters using attribute syntax (e.g., model_params.text = "Hello").

        Args:
            name (str): Name of the parameter
            value (Any): Value to set for the parameter
        """
        if name == "parameters":  # Allow setting the parameters dict normally
            super().__setattr__(name, value)
            return

        if name in self.parameters:
            self.parameters[name].value = value
        else:
            raise AttributeError(f"Parameter '{name}' is not defined")

    def __getattr__(self, name: str) -> Any:
        """Allow getting parameter values using attribute syntax (e.g., model_params.text).

        Args:
            name (str): Name of the parameter

        Returns:
            Any: Value of the parameter

        Raises:
            AttributeError: If parameter is not defined
        """
        if name in self.parameters:
            return self.parameters[name].value
        raise AttributeError(f"Parameter '{name}' is not defined")
