---
sidebar_label: utility_model
title: aixplain.modules.model.utility_model
---

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

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: November 25th 2024
Description:
    Utility Model Class

### BaseUtilityModelParams Objects

```python
class BaseUtilityModelParams(BaseModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L36)

Base model for utility model parameters.

This class defines the basic parameters required to create or update a utility model.

**Attributes**:

- `name` _Text_ - The name of the utility model.
- `code` _Union[Text, Callable]_ - The implementation code, either as a string or
  a callable function.
- `description` _Optional[Text]_ - A description of what the utility model does.
  Defaults to None.

### UtilityModelInput Objects

```python
@dataclass
class UtilityModelInput()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L55)

A class representing an input parameter for a utility model.

This class defines the structure and validation rules for input parameters
that can be used with utility models.

**Attributes**:

- `name` _Text_ - The name of the input parameter.
- `description` _Text_ - A description of what this input parameter represents.
- `type` _DataType_ - The data type of the input parameter. Must be one of:
  TEXT, BOOLEAN, or NUMBER. Defaults to DataType.TEXT.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L72)

Validate that the input parameter has a supported data type.

**Raises**:

- `ValueError` - If the type is not one of: TEXT, BOOLEAN, or NUMBER.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L81)

Convert the input parameter to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the input parameter&#x27;s name, description,
  and type (as a string value).

#### utility\_tool

```python
def utility_tool(name: Text,
                 description: Text,
                 inputs: List[UtilityModelInput] = None,
                 output_examples: Text = "",
                 status=AssetStatus.DRAFT)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L92)

Decorator for utility tool functions

**Arguments**:

- `name` - Name of the utility tool
- `description` - Description of what the utility tool does
- `inputs` - List of input parameters, must be UtilityModelInput objects
- `output_examples` - Examples of expected outputs
- `status` - Asset status
  

**Raises**:

- `ValueError` - If name or description is empty
- `TypeError` - If inputs contains non-UtilityModelInput objects

### UtilityModel Objects

```python
class UtilityModel(Model, DeployableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L134)

Ready-to-use Utility Model.

Note: Non-deployed utility models (status=DRAFT) will expire after 24 hours after creation.
Use the .deploy() method to make the model permanent.

**Attributes**:

- `id` _Text_ - ID of the Model
- `name` _Text_ - Name of the Model
- `code` _Union[Text, Callable]_ - code of the model.
- `description` _Text_ - description of the model. Defaults to &quot;&quot;.
- `inputs` _List[UtilityModelInput]_ - inputs of the model. Defaults to [].
- `output_examples` _Text_ - output examples. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key of the Model. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - supplier of the asset. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - version of the model. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - model AI function. Defaults to None.
- `name`0 _bool, optional_ - Is the user subscribed. Defaults to False.
- `name`1 _Dict, optional_ - model price. Defaults to None.
- `name`2 _AssetStatus, optional_ - status of the model. Defaults to AssetStatus.DRAFT.
- `name`3 - Any additional Model info to be saved

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Optional[Text] = None,
             code: Union[Text, Callable] = None,
             description: Optional[Text] = None,
             inputs: List[UtilityModelInput] = [],
             output_examples: Text = "",
             api_key: Optional[Text] = None,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             function: Optional[Function] = None,
             is_subscribed: bool = False,
             cost: Optional[Dict] = None,
             status: AssetStatus = AssetStatus.DRAFT,
             function_type: Optional[FunctionType] = FunctionType.UTILITY,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L157)

Initialize a new UtilityModel instance.

**Arguments**:

- `id` _Text_ - ID of the utility model.
- `name` _Optional[Text], optional_ - Name of the utility model. If not provided,
  will be extracted from the code if decorated. Defaults to None.
- `code` _Union[Text, Callable], optional_ - Implementation code, either as a string
  or a callable function. Defaults to None.
- `description` _Optional[Text], optional_ - Description of what the model does.
  If not provided, will be extracted from the code if decorated.
  Defaults to None.
- `inputs` _List[UtilityModelInput], optional_ - List of input parameters the
  model accepts. If not provided, will be extracted from the code if
  decorated. Defaults to [].
- `output_examples` _Text, optional_ - Examples of the model&#x27;s expected outputs.
  Defaults to &quot;&quot;.
- `api_key` _Optional[Text], optional_ - API key for accessing the model.
  Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the model.
  Defaults to &quot;aiXplain&quot;.
- `version` _Optional[Text], optional_ - Version of the model. Defaults to None.
- `function` _Optional[Function], optional_ - Function type. Must be
  Function.UTILITIES. Defaults to None.
- `name`0 _bool, optional_ - Whether the user is subscribed.
  Defaults to False.
- `name`1 _Optional[Dict], optional_ - Cost information for the model.
  Defaults to None.
- `name`2 _AssetStatus, optional_ - Current status of the model.
  Defaults to AssetStatus.DRAFT.
- `name`3 _Optional[FunctionType], optional_ - Type of the function.
  Defaults to FunctionType.UTILITY.
- `name`4 - Any additional model info to be saved.
  

**Raises**:

- `name`5 - If function is not Function.UTILITIES.
  

**Notes**:

  Non-deployed utility models (status=DRAFT) will expire after 24 hours.
  Use the .deploy() method to make the model permanent.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L249)

Validate the Utility Model.

This method checks if the utility model exists in the backend and if the code is a string with s3://.
If not, it parses the code and updates the description and inputs and does the validation.
If yes, it just does the validation on the description and inputs.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L300)

Convert the utility model to a dictionary representation.

This method creates a dictionary containing all the essential information
about the utility model, suitable for API requests or serialization.

**Returns**:

- `dict` - A dictionary containing:
  - name (str): The model&#x27;s name
  - description (str): The model&#x27;s description
  - inputs (List[dict]): List of input parameters as dictionaries
  - code (Union[str, Callable]): The model&#x27;s implementation code
  - function (str): The function type as a string value
  - outputDescription (str): Examples of expected outputs
  - status (str): Current status as a string value

#### update

```python
def update()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L326)

Update the Utility Model.

This method validates the utility model and updates it in the backend.

**Raises**:

- `Exception` - If the update fails.

#### save

```python
def save()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L363)

Save the Utility Model.

This method updates the utility model in the backend.

#### delete

```python
def delete()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L370)

Delete the Utility Model.

This method deletes the utility model from the backend.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utility_model.py#L391)

Return a string representation of the UtilityModel instance.

**Returns**:

- `str` - A string in the format &quot;UtilityModel: &lt;name&gt; by &lt;supplier&gt; (id=&lt;id&gt;)&quot;.
  If supplier is a dictionary, uses supplier[&#x27;name&#x27;], otherwise uses
  supplier directly.

