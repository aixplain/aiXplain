---
sidebar_label: mcp_connection
title: aixplain.modules.model.mcp_connection
---

### ConnectAction Objects

```python
class ConnectAction()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L7)

A class representing an action that can be performed by an MCP connection.

This class defines the structure of a connection action with its name, description,
code, and input parameters.

**Attributes**:

- `name` _Text_ - The display name of the action.
- `description` _Text_ - A detailed description of what the action does.
- `code` _Optional[Text]_ - The internal code/identifier for the action. Defaults to None.
- `inputs` _Optional[Dict]_ - The input parameters required by the action. Defaults to None.

#### \_\_init\_\_

```python
def __init__(name: Text,
             description: Text,
             code: Optional[Text] = None,
             inputs: Optional[Dict] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L25)

Initialize a new ConnectAction instance.

**Arguments**:

- `name` _Text_ - The display name of the action.
- `description` _Text_ - A detailed description of what the action does.
- `code` _Optional[Text], optional_ - The internal code/identifier for the action.
  Defaults to None.
- `inputs` _Optional[Dict], optional_ - The input parameters required by the action.
  Defaults to None.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L47)

Return a string representation of the ConnectAction instance.

**Returns**:

- `str` - A string in the format &quot;Action(code=&lt;code&gt;, name=&lt;name&gt;)&quot;.

### MCPConnection Objects

```python
class MCPConnection(ConnectionTool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L56)

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text = "",
             api_key: Optional[Text] = None,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             function: Optional[Function] = None,
             is_subscribed: bool = False,
             cost: Optional[Dict] = None,
             function_type: Optional[FunctionType] = FunctionType.CONNECTION,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L60)

Initialize a new MCPConnection instance.

**Arguments**:

- `id` _Text_ - ID of the MCP Connection.
- `name` _Text_ - Name of the MCP Connection.
- `description` _Text, optional_ - Description of the Connection. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key for the Connection. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the Connection.
  Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version of the Connection. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - Function of the Connection. Defaults to None.
- `is_subscribed` _bool, optional_ - Whether the user is subscribed. Defaults to False.
- `cost` _Dict, optional_ - Cost of the Connection. Defaults to None.
- `function_type` _FunctionType, optional_ - Type of the function. Must be
  FunctionType.MCP_CONNECTION. Defaults to FunctionType.CONNECTION.
- `name`0 - Any additional Connection info to be saved.
  

**Raises**:

- `name`1 - If function_type is not FunctionType.MCP_CONNECTION.

#### get\_action\_inputs

```python
def get_action_inputs(action: Union[ConnectAction, Text])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/mcp_connection.py#L136)

Retrieve the input parameters required for a specific tool.

This method fetches the input parameters that are required to use a specific
tool. If the action object already has its inputs cached, returns those
instead of making a server request.

**Arguments**:

- `action` _Union[ConnectAction, Text]_ - The tool to get inputs for, either as
  a ConnectAction object or as a string code.
  

**Returns**:

- `Dict` - A dictionary mapping input parameter codes to their specifications.
  

**Raises**:

- `Exception` - If the inputs cannot be retrieved from the server or if the
  response cannot be parsed.

