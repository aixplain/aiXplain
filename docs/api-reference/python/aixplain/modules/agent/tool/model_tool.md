---
sidebar_label: model_tool
title: aixplain.modules.agent.tool.model_tool
---

Model tool for aiXplain SDK agents.

This module provides a tool that allows agents to interact with AI models
and execute model-based tasks.

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: May 16th 2024
Description:
    Agentification Class

#### set\_tool\_name

```python
def set_tool_name(function: Function,
                  supplier: Supplier = None,
                  model: Model = None) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L35)

Sets the name of the tool based on the function, supplier, and model.

**Arguments**:

- `function` _Function_ - The function to be used in the tool.
- `supplier` _Supplier_ - The supplier to be used in the tool.
- `model` _Model_ - The model to be used in the tool.
  

**Returns**:

- `Text` - The name of the tool.

### ModelTool Objects

```python
class ModelTool(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L59)

A tool that wraps AI models to execute specific tasks or functions based on user commands.

This class provides a standardized interface for working with various AI models,
allowing them to be used as tools in the aiXplain platform. It handles model
configuration, validation, and parameter management.

**Attributes**:

- `function` _Optional[Function]_ - The task that the tool performs.
- `supplier` _Optional[Supplier]_ - The preferred supplier to perform the task.
- `model` _Optional[Union[Text, Model]]_ - The model ID or Model instance.
- `model_object` _Optional[Model]_ - The actual Model instance for parameter access.
- `parameters` _Optional[Dict]_ - Configuration parameters for the model.
- `status` _AssetStatus_ - The current status of the tool.

#### \_\_init\_\_

```python
def __init__(function: Optional[Union[Function, Text]] = None,
             supplier: Optional[Union[Dict, Supplier]] = None,
             model: Optional[Union[Text, Model]] = None,
             name: Optional[Text] = None,
             description: Text = "",
             parameters: Optional[Dict] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L75)

Initialize a new ModelTool instance.

**Arguments**:

- `function` _Optional[Union[Function, Text]], optional_ - The task that the tool performs. Can be a Function enum
  or a string that will be converted to a Function. Defaults to None.
- `supplier` _Optional[Union[Dict, Supplier]], optional_ - The preferred supplier to perform the task.
  Can be a Supplier enum or a dictionary with supplier information. Defaults to None.
- `model` _Optional[Union[Text, Model]], optional_ - The model to use, either as a Model instance
  or a model ID string. Defaults to None.
- `name` _Optional[Text], optional_ - The name of the tool. If not provided, will be generated
  from function, supplier, and model. Defaults to None.
- `description` _Text, optional_ - A description of the tool&#x27;s functionality. If not provided,
  will be taken from model or function description. Defaults to &quot;&quot;.
- `parameters` _Optional[Dict], optional_ - Configuration parameters for the model. Defaults to None.
- `**additional_info` - Additional keyword arguments for tool configuration.
  

**Raises**:

- `Exception` - If the specified model doesn&#x27;t exist or is inaccessible.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L130)

Convert the tool instance to a dictionary representation.

This method handles the conversion of complex attributes like supplier and model
into their serializable forms.

**Returns**:

- `Dict` - A dictionary containing the tool&#x27;s configuration with keys:
  - function: The function value or None
  - type: Always &quot;model&quot;
  - name: The tool&#x27;s name
  - description: The tool&#x27;s description
  - supplier: The supplier code or None
  - version: The tool&#x27;s version or None
  - assetId: The model&#x27;s ID
  - parameters: The tool&#x27;s parameters
  - status: The tool&#x27;s status

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L169)

Validates the tool.

**Notes**:

  - Checks if the tool has a function or model.
  - If the function is a string, it converts it to a Function enum.
  - Checks if the function is a utility function and if it has an associated model.
  - Validates the supplier.
  - Validates the model.
  - If the description is empty, it sets the description to the function description or the model description.

#### get\_parameters

```python
def get_parameters() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L223)

Get the tool&#x27;s parameters, either from explicit settings or the model object.

**Returns**:

- `Dict` - The tool&#x27;s parameters. If no explicit parameters were set and a model
  object exists with model_params, returns those parameters as a list.

#### validate\_parameters

```python
def validate_parameters(
        received_parameters: Optional[List[Dict]] = None
) -> Optional[List[Dict]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L258)

Validates and formats the parameters for the tool.

**Arguments**:

- `received_parameters` _Optional[List[Dict]]_ - List of parameter dictionaries in format [\{&quot;name&quot;: &quot;param_name&quot;, &quot;value&quot;: param_value}]
  

**Returns**:

- `Optional[List[Dict]]` - Validated parameters in the required format
  

**Raises**:

- `ValueError` - If received parameters don&#x27;t match the expected parameters from model or function

#### \_\_repr\_\_

```python
def __repr__() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/model_tool.py#L315)

Return a string representation of the tool.

**Returns**:

- `Text` - A string in the format &quot;ModelTool(name=&lt;name&gt;, function=&lt;function&gt;,
  supplier=&lt;supplier&gt;, model=&lt;model&gt;)&quot;.

