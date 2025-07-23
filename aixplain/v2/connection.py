from typing import List, Optional, Union, Dict
from dataclasses import dataclass
from .model import Model
from .resource import Result


@dataclass
class ConnectAction:
    """Represents an action available in a connection."""

    name: str
    description: str
    code: Optional[str] = None
    inputs: Optional[Dict] = None

    def __repr__(self):
        return f"Action(code={self.code}, name={self.name})"


class Connection(Model):
    """V2 Connection that handles action scope and parameters like the legacy version."""

    RESOURCE_PATH = "sdk/tools"  # Use tools endpoint for connections

    actions: Optional[List[ConnectAction]] = None
    action_scope: Optional[List[ConnectAction]] = None

    def __post_init__(self):
        super().__post_init__()
        # Don't get actions during initialization to avoid errors
        # Actions will be fetched when needed

    def _get_actions(self) -> List[ConnectAction]:
        """Get available actions from the connection."""
        try:
            response = super().run(data={"action": "LIST_ACTIONS", "data": " "})
            if response.status == "SUCCESS":
                return [
                    ConnectAction(
                        name=action["displayName"],
                        description=action["description"],
                        code=action["name"],
                    )
                    for action in response.data
                ]
            else:
                error_msg = (
                    f"Failed to get actions for connection {self.id}. "
                    f"Error: {response.error_message}"
                )
                raise Exception(error_msg)
        except Exception as e:
            # Try alternative approach - get actions from the model data
            try:
                # Get the model data to see if actions are available
                model_data = self.context.Model.get(self.id)
                if hasattr(model_data, "actions") and model_data.actions:
                    return [
                        ConnectAction(
                            name=action.get("displayName", action.get("name", "")),
                            description=action.get("description", ""),
                            code=action.get("name", ""),
                        )
                        for action in model_data.actions
                    ]
                else:
                    # Return a default action based on the function type
                    return [
                        ConnectAction(
                            name="Default Action",
                            description="Default action for this connection",
                            code="DEFAULT_ACTION",
                        )
                    ]
            except Exception as fallback_error:
                raise Exception(
                    f"Failed to get actions for connection {self.id}. "
                    f"Original error: {e}. Fallback error: {fallback_error}"
                )

    def get_action_inputs(self, action: Union[ConnectAction, str]) -> Dict:
        """Get input parameters for a specific action."""
        if isinstance(action, ConnectAction):
            if action.inputs:
                return action.inputs
            action_code = action.code
        else:
            action_code = action

        try:
            response = super().run(
                data={"action": "LIST_INPUTS", "data": {"actions": [action_code]}}
            )
            if response.status == "SUCCESS":
                inputs = {inp["code"]: inp for inp in response.data[0]["inputs"]}
                # Update the action object if it exists
                if isinstance(action, ConnectAction):
                    action.inputs = inputs
                return inputs
            else:
                raise Exception(
                    f"Failed to get inputs for action {action_code}. "
                    f"Error: {response.error_message}"
                )
        except Exception as e:
            raise Exception(
                f"Failed to get inputs for action {action_code}. Error: {e}"
            )

    def run(self, action: Union[ConnectAction, str], data: Dict) -> Result:
        """Run a specific action with inputs."""
        if isinstance(action, ConnectAction):
            action_code = action.code
        else:
            action_code = action

        return super().run(data={"action": action_code, "data": data})

    def get_parameters(self) -> List[Dict]:
        """Get parameters for the current action scope."""
        if not self.action_scope or len(self.action_scope) == 0:
            raise ValueError(
                f"Action scope not set for connection '{self.id}'. "
                "Please set action_scope before calling get_parameters()."
            )

        parameters = []
        for action in self.action_scope:
            inputs = self.get_action_inputs(action)
            parameters.append(
                {
                    "code": action.code,
                    "name": action.name,
                    "description": action.description,
                    "inputs": inputs,
                }
            )

        return parameters

    def set_action_scope(self, action_codes: List[str]) -> None:
        """Set the action scope based on action codes."""
        # Create actions directly from action codes to avoid API calls
        self.actions = [
            ConnectAction(
                name=f"Action {code}", description=f"Action for {code}", code=code
            )
            for code in action_codes
        ]
        self.action_scope = self.actions

    def __repr__(self):
        return f"Connection(id={self.id}, name={self.name})"
