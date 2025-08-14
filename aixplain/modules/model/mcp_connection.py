from aixplain.enums import Function, Supplier, FunctionType, ResponseStatus
from aixplain.modules.model.connection import ConnectionTool
from aixplain.modules.model import Model
from typing import Text, Optional, Union, Dict, List


class ConnectAction:
    """A class representing an action that can be performed by an MCP connection.

    This class defines the structure of a connection action with its name, description,
    code, and input parameters.

    Attributes:
        name (Text): The display name of the action.
        description (Text): A detailed description of what the action does.
        code (Optional[Text]): The internal code/identifier for the action. Defaults to None.
        inputs (Optional[Dict]): The input parameters required by the action. Defaults to None.
    """

    name: Text
    description: Text
    code: Optional[Text] = None
    inputs: Optional[Dict] = None

    def __init__(
        self,
        name: Text,
        description: Text,
        code: Optional[Text] = None,
        inputs: Optional[Dict] = None,
    ):
        """Initialize a new ConnectAction instance.

        Args:
            name (Text): The display name of the action.
            description (Text): A detailed description of what the action does.
            code (Optional[Text], optional): The internal code/identifier for the action.
                Defaults to None.
            inputs (Optional[Dict], optional): The input parameters required by the action.
                Defaults to None.
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


class MCPConnection(ConnectionTool):
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
        """Initialize a new MCPConnection instance.

        Args:
            id (Text): ID of the MCP Connection.
            name (Text): Name of the MCP Connection.
            description (Text, optional): Description of the Connection. Defaults to "".
            api_key (Text, optional): API key for the Connection. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the Connection.
                Defaults to "aiXplain".
            version (Text, optional): Version of the Connection. Defaults to "1.0".
            function (Function, optional): Function of the Connection. Defaults to None.
            is_subscribed (bool, optional): Whether the user is subscribed. Defaults to False.
            cost (Dict, optional): Cost of the Connection. Defaults to None.
            function_type (FunctionType, optional): Type of the function. Must be
                FunctionType.MCP_CONNECTION. Defaults to FunctionType.CONNECTION.
            **additional_info: Any additional Connection info to be saved.

        Raises:
            AssertionError: If function_type is not FunctionType.MCP_CONNECTION.
        """
        assert function_type == FunctionType.MCP_CONNECTION, "Connection only supports mcp connection function"
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

    def _get_actions(self):
        """Retrieve the list of available tools for this MCP connection.

        This internal method fetches the list of tools that can be used with this
        connection by calling the LIST_TOOLS action.

        Returns:
            List[ConnectAction]: A list of available tools, each represented as a
                ConnectAction object.

        Raises:
            Exception: If the tools cannot be retrieved from the server.
        """
        response = Model.run(self, {"action": "LIST_TOOLS", "data": " "})
        if response.status == ResponseStatus.SUCCESS:
            return [
                ConnectAction(
                    name=action["name"],
                    description=action["description"],
                    code=action["name"],
                )
                for action in response.data
            ]
        raise Exception(
            f"It was not possible to get the actions for the connection {self.id}. Error {response.error_code}: {response.error_message}"
        )

    def get_action_inputs(self, action: Union[ConnectAction, Text]):
        """Retrieve the input parameters required for a specific tool.

        This method fetches the input parameters that are required to use a specific
        tool. If the action object already has its inputs cached, returns those
        instead of making a server request.

        Args:
            action (Union[ConnectAction, Text]): The tool to get inputs for, either as
                a ConnectAction object or as a string code.

        Returns:
            Dict: A dictionary mapping input parameter codes to their specifications.

        Raises:
            Exception: If the inputs cannot be retrieved from the server or if the
                response cannot be parsed.
        """
        if action.inputs:
            return action.inputs

        if isinstance(action, ConnectAction):
            action = action.code

        response = Model.run(self, {"action": "LIST_TOOLS", "data": {"actions": [action]}})
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
