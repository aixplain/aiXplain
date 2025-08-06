from aixplain.enums import Function, Supplier, FunctionType, ResponseStatus
from aixplain.modules.model import Model
from aixplain.utils import config
from typing import Text, Optional, Union, Dict, List


class ConnectAction:
    """A class representing an action that can be performed by a connection.

    This class defines the structure of a connection action with its name, description,
    code, and input parameters.

    Attributes:
        name (Text): The display name of the action.
        description (Text): A detailed description of what the action does.
        code (Optional[Text]): The internal code/identifier for the action.
        inputs (Optional[Dict]): The input parameters required by the action.
    """

    name: Text
    description: Text
    code: Optional[Text] = None
    inputs: Optional[Dict] = None

    def __init__(self, name: Text, description: Text, code: Optional[Text] = None, inputs: Optional[Dict] = None):
        """Initialize a new ConnectAction instance.

        Args:
            name (Text): The display name of the action.
            description (Text): A detailed description of what the action does.
            code (Optional[Text], optional): The internal code/identifier for the action. Defaults to None.
            inputs (Optional[Dict], optional): The input parameters required by the action. Defaults to None.
        """
        self.name = name
        self.description = description
        self.code = code
        self.inputs = inputs

    def __repr__(self):
        """Return a string representation of the ConnectAction instance.

        Returns:
            str: A string in the format "Action(code=<code>, name=<name>)".
        """
        return f"Action(code={self.code}, name={self.name})"


class ConnectionTool(Model):
    actions: List[ConnectAction]
    action_scope: Optional[List[ConnectAction]] = None

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        function_type: Optional[FunctionType] = FunctionType.CONNECTION,
        **additional_info,
    ) -> None:
        """Initialize a new ConnectionTool instance.

        Args:
            id (Text): ID of the Connection
            name (Text): Name of the Connection
            description (Text, optional): Description of the Connection. Defaults to "".
            api_key (Text, optional): API key of the Connection. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the Connection. Defaults to "aiXplain".
            version (Text, optional): Version of the Connection. Defaults to "1.0".
            function (Function, optional): Function of the Connection. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): Cost of the Connection. Defaults to None.
            function_type (FunctionType, optional): Type of the Connection. Defaults to FunctionType.CONNECTION.
            **additional_info: Any additional Connection info to be saved
        """
        assert (
            function_type == FunctionType.CONNECTION or function_type == FunctionType.MCP_CONNECTION
        ), "Connection only supports connection function"
        super().__init__(
            id=id,
            name=name,
            description=description,
            supplier=supplier,
            version=version,
            cost=cost,
            function=function,
            is_subscribed=is_subscribed,
            api_key=api_key,
            function_type=function_type,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.actions = self._get_actions()
        self.action_scope = None

    def _get_actions(self):
        """Retrieve the list of available actions for this connection.

        Returns:
            List[ConnectAction]: A list of available actions for this connection.

        Raises:
            Exception: If the actions cannot be retrieved from the server.
        """
        response = super().run({"action": "LIST_ACTIONS", "data": " "})
        if response.status == ResponseStatus.SUCCESS:
            return [
                ConnectAction(name=action["displayName"], description=action["description"], code=action["name"])
                for action in response.data
            ]
        raise Exception(
            f"It was not possible to get the actions for the connection {self.id}. Error {response.error_code}: {response.error_message}"
        )

    def get_action_inputs(self, action: Union[ConnectAction, Text]):
        """Retrieve the input parameters required for a specific action.

        Args:
            action (Union[ConnectAction, Text]): The action to get inputs for, either as a ConnectAction object
                or as a string code.

        Returns:
            Dict: A dictionary containing the input parameters for the action.

        Raises:
            Exception: If the inputs cannot be retrieved from the server.
        """
        if action.inputs:
            return action.inputs

        if isinstance(action, ConnectAction):
            action = action.code

        response = super().run({"action": "LIST_INPUTS", "data": {"actions": [action]}})
        if response.status == ResponseStatus.SUCCESS:
            try:
                inputs = {inp["code"]: inp for inp in response.data[0]["inputs"]}
                action_idx = next((i for i, a in enumerate(self.actions) if a.code == action), None)
                if action_idx is not None:
                    self.actions[action_idx].inputs = inputs
                return inputs
            except Exception as e:
                raise Exception(f"It was not possible to get the inputs for the action {action}. Error {e}")

        raise Exception(
            f"It was not possible to get the inputs for the action {action}. Error {response.error_code}: {response.error_message}"
        )

    def run(self, action: Union[ConnectAction, Text], inputs: Dict):
        """Execute a specific action with the provided inputs.

        Args:
            action (Union[ConnectAction, Text]): The action to execute, either as a ConnectAction object
                or as a string code.
            inputs (Dict): The input parameters for the action.

        Returns:
            Response: The response from the server after executing the action.
        """
        if isinstance(action, ConnectAction):
            action = action.code
        return super().run({"action": action, "data": inputs})

    def get_parameters(self) -> List[Dict]:
        """Get the parameters for all actions in the current action scope.

        Returns:
            List[Dict]: A list of dictionaries containing the parameters for each action
                in the action scope. Each dictionary contains the action's code, name,
                description, and input parameters.

        Raises:
            AssertionError: If the action scope is not set or is empty.
        """
        assert (
            self.action_scope is not None and len(self.action_scope) > 0
        ), f"Please set the scope of actions for the connection '{self.id}'."
        response = [
            {
                "code": action.code,
                "name": action.name,
                "description": action.description,
                "inputs": self.get_action_inputs(action),
            }
            for action in self.action_scope
        ]
        return response

    def __repr__(self):
        """Return a string representation of the ConnectionTool instance.

        Returns:
            str: A string in the format "ConnectionTool(id=<id>, name=<name>)".
        """
        return f"ConnectionTool(id={self.id}, name={self.name})"
