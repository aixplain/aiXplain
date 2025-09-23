---
sidebar_label: connection
title: aixplain.modules.model.connection
---

### ConnectAction Objects

```python
class ConnectAction()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L7)

A class representing an action that can be performed by a connection.

This class defines the structure of a connection action with its name, description,
code, and input parameters.

**Attributes**:

- `name` _Text_ - The display name of the action.
- `description` _Text_ - A detailed description of what the action does.
- `code` _Optional[Text]_ - The internal code/identifier for the action.
- `inputs` _Optional[Dict]_ - The input parameters required by the action.

#### \_\_init\_\_

```python
def __init__(name: Text,
             description: Text,
             code: Optional[Text] = None,
             inputs: Optional[Dict] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L25)

Initialize a new ConnectAction instance.

**Arguments**:

- `name` _Text_ - The display name of the action.
- `description` _Text_ - A detailed description of what the action does.
- `code` _Optional[Text], optional_ - The internal code/identifier for the action. Defaults to None.
- `inputs` _Optional[Dict], optional_ - The input parameters required by the action. Defaults to None.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L45)

Return a string representation of the ConnectAction instance.

**Returns**:

- `str` - A string in the format &quot;Action(code=&lt;code&gt;, name=&lt;name&gt;)&quot;.

### ConnectionTool Objects

```python
class ConnectionTool(Model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L54)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L58)

Initialize a new ConnectionTool instance.

**Arguments**:

- `id` _Text_ - ID of the Connection
- `name` _Text_ - Name of the Connection
- `description` _Text, optional_ - Description of the Connection. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key of the Connection. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the Connection. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version of the Connection. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - Function of the Connection. Defaults to None.
- `is_subscribed` _bool, optional_ - Is the user subscribed. Defaults to False.
- `cost` _Dict, optional_ - Cost of the Connection. Defaults to None.
- `function_type` _FunctionType, optional_ - Type of the Connection. Defaults to FunctionType.CONNECTION.
- `name`0 - Any additional Connection info to be saved

#### get\_action\_inputs

```python
def get_action_inputs(action: Union[ConnectAction, Text])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L131)

Retrieve the input parameters required for a specific action.

**Arguments**:

- `action` _Union[ConnectAction, Text]_ - The action to get inputs for, either as a ConnectAction object
  or as a string code.
  

**Returns**:

- `Dict` - A dictionary containing the input parameters for the action.
  

**Raises**:

- `Exception` - If the inputs cannot be retrieved from the server.

#### run

```python
def run(action: Union[ConnectAction, Text], inputs: Dict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L165)

Execute a specific action with the provided inputs.

**Arguments**:

- `action` _Union[ConnectAction, Text]_ - The action to execute, either as a ConnectAction object
  or as a string code.
- `inputs` _Dict_ - The input parameters for the action.
  

**Returns**:

- `Response` - The response from the server after executing the action.

#### get\_parameters

```python
def get_parameters() -> List[Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L180)

Get the parameters for all actions in the current action scope.

**Returns**:

- `List[Dict]` - A list of dictionaries containing the parameters for each action
  in the action scope. Each dictionary contains the action&#x27;s code, name,
  description, and input parameters.
  

**Raises**:

- `AssertionError` - If the action scope is not set or is empty.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/connection.py#L205)

Return a string representation of the ConnectionTool instance.

**Returns**:

- `str` - A string in the format &quot;ConnectionTool(id=&lt;id&gt;, name=&lt;name&gt;)&quot;.

