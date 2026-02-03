from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class Parameter:
    """A class representing a single parameter with its properties.

    Attributes:
        name (str): The name of the parameter.
        required (bool): Whether the parameter is required or optional.
        value (Optional[Any]): The value of the parameter. Defaults to None.
        is_fixed (bool): Whether the parameter value is fixed. Defaults to False.
        values (List[Dict[str, Any]]): Pre-set values for the parameter. Defaults to empty list.
        default_values (List[Any]): Default values for the parameter. Defaults to empty list.
        available_options (List[Dict[str, Any]]): Available options for selection. Defaults to empty list.
        data_type (Optional[str]): The data type of the parameter (e.g., 'text', 'number').
        data_sub_type (Optional[str]): The sub-type of the data (e.g., 'json', 'text').
        multiple_values (bool): Whether multiple values are allowed. Defaults to False.
    """

    name: str
    required: bool
    value: Optional[Any] = None
    is_fixed: bool = False
    values: List[Dict[str, Any]] = None
    default_values: List[Any] = None
    available_options: List[Dict[str, Any]] = None
    data_type: Optional[str] = None
    data_sub_type: Optional[str] = None
    multiple_values: bool = False

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.values is None:
            self.values = []
        if self.default_values is None:
            self.default_values = []
        if self.available_options is None:
            self.available_options = []


class BaseParameters:
    """A base class for managing a collection of parameters.

    This class provides functionality to store, access, and manipulate parameters
    in a structured way. Parameters can be accessed using attribute syntax or
    dictionary-style access.

    Attributes:
        parameters (Dict[str, Parameter]): Dictionary storing Parameter objects.
    """

    def __init__(self) -> None:
        """Initialize the BaseParameters class.

        The initialization creates an empty dictionary to store parameters.
        """
        self.parameters: Dict[str, Parameter] = {}

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
        return {
            param.name: {
                "name": param.name,
                "required": param.required,
                "value": param.value,
                "isFixed": param.is_fixed,
                "values": param.values,
                "defaultValues": param.default_values,
                "availableOptions": param.available_options,
                "dataType": param.data_type,
                "dataSubType": param.data_sub_type,
                "multipleValues": param.multiple_values,
            }
            for param in self.parameters.values()
        }

    def to_list(self) -> List[str]:
        """Convert parameters to a list format.

        This method creates a list of dictionaries containing the name and value
        of each parameter that has a value set.

        Returns:
            List[str]: A list of dictionaries, each containing 'name' and 'value'
                keys for parameters that have values set.
        """
        return [
            {"name": param.name, "value": param.value}
            for param in self.parameters.values()
            if param.value is not None
        ]

    def __str__(self) -> str:
        """Create a pretty string representation of the parameters.

        Returns:
            str: Formatted string showing all parameters
        """
        if not self.parameters:
            return "No parameters defined"

        lines = ["Parameters:"]
        for param in self.parameters.values():
            value_str = str(param.value) if param.value is not None else "Not set"
            required_str = "(Required)" if param.required else "(Optional)"
            fixed_str = " [Fixed]" if param.is_fixed else ""
            type_str = f" [{param.data_type}]" if param.data_type else ""
            options_str = (
                f" Options: {[opt.get('value') for opt in param.available_options]}"
                if param.available_options
                else ""
            )
            lines.append(
                f"  - {param.name}: {value_str} {required_str}{fixed_str}{type_str}{options_str}"
            )

        return "\n".join(lines)

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting parameters using attribute syntax.

        This special method enables setting parameter values using attribute syntax
        (e.g., params.text = "Hello"). It only works for parameters that have been
        previously defined.

        Args:
            name (str): Name of the parameter to set.
            value (Any): Value to assign to the parameter.

        Raises:
            AttributeError: If attempting to set a parameter that hasn't been defined.
        """
        if name == "parameters":  # Allow setting the parameters dict normally
            super().__setattr__(name, value)
            return

        if name in self.parameters:
            self.parameters[name].value = value
        else:
            raise AttributeError(f"Parameter '{name}' is not defined")

    def __getattr__(self, name: str) -> Any:
        """Allow getting parameter values using attribute syntax.

        This special method enables accessing parameter values using attribute syntax
        (e.g., params.text). It only works for parameters that have been previously
        defined.

        Args:
            name (str): Name of the parameter to access.

        Returns:
            Any: The value of the requested parameter.

        Raises:
            AttributeError: If attempting to access a parameter that hasn't been defined.
        """
        if name in self.parameters:
            return self.parameters[name].value
        raise AttributeError(f"Parameter '{name}' is not defined")
