import warnings
from typing import Union, List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json, config as dj_config
from dataclasses import dataclass, field

from .resource import (
    Result,
    DeleteResourceMixin,
    BaseDeleteParams,
    DeleteResult,
)
from .model import Model, ModelRunParams
from .integration import Integration, Action, ActionMixin, Input


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult], ActionMixin):
    """Resource for tools.

    This class represents a tool resource that matches the backend structure.
    Tools can be integrations, utilities, or other specialized resources.
    Inherits from Model to reuse shared attributes and functionality.
    """

    RESOURCE_PATH = "v2/tools"
    RESPONSE_CLASS = ToolResult
    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration

    # Tool-specific fields
    asset_id: Optional[str] = field(
        default=None, metadata=dj_config(field_name="assetId")
    )
    integration: Optional[Union[Integration, str]] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    config: Optional[dict] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    code: Optional[str] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    allowed_actions: Optional[List[str]] = field(
        default_factory=list, metadata=dj_config(field_name="allowedActions")
    )
    auth_scheme: Optional[Integration.AuthenticationScheme] = field(
        default=Integration.AuthenticationScheme.NO_AUTH,
        metadata=dj_config(exclude=lambda x: True),
    )

    def __post_init__(self) -> None:
        if not self.id:
            if self.integration is None:
                code = self.code or (
                    self.config.pop("code", None) if self.config else None
                )
                assert code is not None, "Code is required to create a (script) Tool"
                # Use default integration ID for utility tools
                self.integration = self.context.Integration.get(
                    self.DEFAULT_INTEGRATION_ID
                )
                self.config = {
                    "code": code,
                }
            else:
                if isinstance(self.integration, str):
                    self.integration = self.context.Integration.get(self.integration)

                assert isinstance(
                    self.integration, Integration
                ), "Integration must be an Integration object or a string"

    # override list_actions to check if actions are available
    def list_actions(self) -> List[Action]:
        if not self.id:
            if self.integration:
                if self.integration.actions_available:
                    return self.integration.list_actions()

            raise ValueError("ERROR! Tool MUST be saved first.")

        try:
            return super().list_actions()
        except Exception as e:
            warnings.warn(
                f"Error listing actions: {e}. Using integration.list_actions() instead."
            )
            return self.integration.list_actions()

    # override list_inputs to check if inputs are available
    def list_inputs(self, *actions: str) -> List[Input]:
        if not self.id:
            if self.integration:
                if self.integration.actions_available:
                    return self.integration.list_actions()

            raise ValueError("ERROR! Tool MUST be saved first.")

        try:
            return super().list_inputs(*actions)
        except Exception as e:
            warnings.warn(
                f"Error listing inputs: {e}. Using integration.list_inputs() instead."
            )
            return self.integration.list_inputs(*actions)

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the tool by connecting to the integration."""
        if not self.integration:
            raise ValueError("Integration is required to create a tool")

        if not self.auth_scheme or self.auth_scheme.value == "NO_AUTH":
            connect_kwargs = self.config.copy()
        else:
            connect_kwargs = {
                "authScheme": self.auth_scheme,
                "data": self.config.copy(),
            }

        connection = self.integration.connect(**connect_kwargs)

        self.id = connection.id

        # Map attributes from connection to tool if they are None
        for attr_name in self.__dataclass_fields__:
            if not getattr(self, attr_name) and getattr(connection, attr_name, None):
                setattr(self, attr_name, getattr(connection, attr_name))

    def _update(self, resource_path: str, payload: dict) -> None:
        raise NotImplementedError("Updating a tool is not supported yet")

    def upsert(
        self,
        data: Union[List[dict], List[str], dict, str, "Resource"] = None,
        resource: Optional["Resource"] = None,
        index_column: Optional[str] = None,
        metadata_columns: Optional[List[str]] = None,
        id_column: Optional[str] = None,
        split_by: Optional[str] = None,
        **kwargs,
    ) -> "Tool":
        """Upsert data into the tool (for indexing functionality).

        Args:
            data: Data to upsert. Can be:
                - str: A single string
                - List[str]: A list of strings
                - dict: A single dictionary (e.g., {"id": "1", "data": "text"})
                - List[dict]: A list of dictionaries
                - Resource: A Resource object (for file-based indexing)
            resource: Resource object (alternative to data parameter)
            index_column: The column to use for indexing (defaults to "data").
            metadata_columns: List of columns to store as metadata.
            id_column: The column to use as the ID (defaults to "id").
            split_by: How to split the text (e.g., "sentence", "paragraph").
            **kwargs: Additional parameters for the upsert operation.

        Returns:
            Tool: The tool instance for chaining.
        """
        # Handle Resource object
        if resource is not None:
            # Use the resource for indexing
            payload = {
                "resource": (
                    resource.id if hasattr(resource, "id") and resource.id else resource
                ),
                "action": "upsert",
            }
        elif data is not None:
            # Format data for upsert
            formatted_data = self._format_data_for_upsert(data, index_column, id_column)
            payload = {"data": formatted_data, "action": "upsert"}
        else:
            raise ValueError("Either 'data' or 'resource' parameter must be provided")

        # Add optional parameters
        if index_column:
            payload["index_column"] = index_column
        if metadata_columns:
            payload["metadata_columns"] = metadata_columns
        if id_column:
            payload["id_column"] = id_column
        if split_by:
            payload["split_by"] = split_by

        # Add any additional kwargs
        payload.update(kwargs)

        # Run the upsert operation
        self.run(**payload)
        return self

    def _format_data_for_upsert(
        self,
        data: Union[List[dict], List[str], dict, str],
        index_column: Optional[str] = None,
        id_column: Optional[str] = None,
    ) -> List[dict]:
        """Format data for upsert operation."""
        index_col = index_column or "data"
        id_col = id_column or "id"

        # Handle single string
        if isinstance(data, str):
            return [{id_col: "1", index_col: data}]

        # Handle single dict
        if isinstance(data, dict):
            return [data]

        # Handle list of strings
        if isinstance(data, list) and data and isinstance(data[0], str):
            return [
                {id_col: str(i + 1), index_col: item} for i, item in enumerate(data)
            ]

        # Handle list of dicts (already formatted)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data

        # Fallback
        return []

    def validate_allowed_actions(self) -> None:
        if self.allowed_actions:
            assert (
                self.integration is not None
            ), "Integration is required to validate allowed actions"

            available_actions = [action.name for action in self.list_actions()]
            assert (
                available_actions is not None
            ), "Integration must have available actions"
            assert all(
                action in available_actions for action in self.allowed_actions
            ), "All allowed actions must be available"

    def get_parameters(self) -> List[dict]:
        """Get parameters for the tool in the format expected by agent saving.

        This method includes both static backend values and dynamically set values
        from the ActionInputsProxy instances, ensuring agents get the current
        configured action inputs.
        """
        self.validate_allowed_actions()

        parameters = []

        # Get all actions at once to avoid multiple API calls
        actions = self.list_inputs(*self.allowed_actions)

        for action in actions:
            # Convert action inputs to the expected parameter format
            action_inputs = {}

            # Get the current action proxy to access dynamically set values
            action_proxy = None
            action_name = action.name or action.slug or ""
            if action_name:
                try:
                    action_proxy = self.actions[action_name]
                except (ValueError, KeyError):
                    # If we can't get the action proxy, skip this action
                    continue

            for input_param in action.inputs:
                input_code = input_param.code or input_param.name.lower().replace(
                    " ", "_"
                )

                # Get the current value from the action proxy if available
                current_value = None
                if action_proxy:
                    current_value = action_proxy.get(input_code)

                # Fall back to backend default if no current value
                if current_value is None and input_param.defaultValue:
                    current_value = (
                        input_param.defaultValue[0]
                        if input_param.defaultValue
                        else None
                    )

                action_inputs[input_code] = {
                    "name": input_param.name,
                    "value": current_value,
                    "required": input_param.required,
                    "datatype": input_param.datatype,
                    "allowMulti": input_param.allowMulti,
                    "supportsVariables": input_param.supportsVariables,
                    "fixed": input_param.fixed,
                    "description": input_param.description,
                }

            parameters.append(
                {
                    "code": action.slug,
                    "name": action_name,
                    "description": action.description or "",
                    "inputs": action_inputs,
                }
            )

        return parameters

    def _validate_params(self, **kwargs: Any) -> List[str]:
        """Validate parameters for the tool."""
        errors = super()._validate_params(**kwargs)
        if "action" not in kwargs:
            errors.append("action is required")

        self.validate_allowed_actions()

        action = kwargs["action"]
        if self.allowed_actions and action not in self.allowed_actions:
            errors.append(f"Action {action} is not allowed for this tool")

        return errors

    def before_run(
        self, *args: Any, **kwargs: Unpack[ModelRunParams]
    ) -> Optional[ToolResult]:
        """Validate tool state before running."""
        # Check if tool is saved before running
        if not self.id:
            raise ValueError(
                f"Tool '{getattr(self, 'name', 'unnamed')}' must be saved before running. "
                "Use tool.save() to save the tool first."
            )
        return None

    def run(self, *args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult:
        """Run the tool."""
        if len(args) > 0:
            kwargs["data"] = args[0]
            args = args[1:]

        # If no action is provided and we have allowed actions, use the first one
        if "action" not in kwargs:
            if self.allowed_actions and len(self.allowed_actions) == 1:
                kwargs["action"] = self.allowed_actions[0]

        if "action" not in kwargs:
            raise ValueError("No action provided")

        return super().run(*args, **kwargs)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Override to handle tool-specific parameter merging.

        Tools don't have the standard 'inputs' attribute like models do,
        so we need to handle parameter merging differently.
        """
        # Start with current tool parameters
        merged = {}
        action_name = kwargs.get("action")
        if not action_name and len(self.allowed_actions) == 1:
            action_name = self.allowed_actions[0]

        if not action_name:
            raise ValueError("No action provided")

        action_proxy = self.actions[action_name]

        # Extract all current input values
        for input_code in action_proxy.keys():
            value = action_proxy.get(input_code)
            if value is not None:
                merged[input_code] = value

        kwargs.setdefault("data", {})

        # Handle both string and dict data
        if isinstance(kwargs["data"], str):
            # For string data (like AIXplain Search), pass it directly
            # Include all other parameters (like dataType) in the request
            result = {
                "action": action_name,
                "data": kwargs["data"],
            }
            # Add all other parameters except 'data' and 'action'
            for key, value in kwargs.items():
                if key not in ["data", "action"]:
                    result[key] = value
            return result
        else:
            # For dict data, merge with merged parameters
            return {
                "action": action_name,
                "data": {
                    **merged,
                    **kwargs["data"],
                },
            }
