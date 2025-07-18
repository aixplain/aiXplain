from aixplain.enums import Function, Supplier, FunctionType, ResponseStatus
from aixplain.modules.model.connection import ConnectionTool
from aixplain.modules.model import Model
from typing import Text, Optional, Union, Dict, List


class ConnectAction:
    name: Text
    description: Text
    code: Optional[Text] = None
    inputs: Optional[Dict] = None

    def __init__(self, name: Text, description: Text, code: Optional[Text] = None, inputs: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.code = code
        self.inputs = inputs

    def __repr__(self):
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
        """Connection Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            scope (Text, optional): action scope of the connection. Defaults to None.
            **additional_info: Any additional Model info to be saved
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
        response = Model.run(self, {"action": "LIST_TOOLS", "data": " "})
        if response.status == ResponseStatus.SUCCESS:
            return [
                ConnectAction(name=action["name"], description=action["description"], code=action["name"])
                for action in response.data
            ]
        raise Exception(
            f"It was not possible to get the actions for the connection {self.id}. Error {response.error_code}: {response.error_message}"
        )

    def get_action_inputs(self, action: Union[ConnectAction, Text]):
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
