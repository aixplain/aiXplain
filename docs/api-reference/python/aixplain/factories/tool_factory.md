---
sidebar_label: tool_factory
title: aixplain.factories.tool_factory
---

### ToolFactory Objects

```python
class ToolFactory(ModelGetterMixin, ModelListMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/tool_factory.py#L17)

A factory class for creating and managing various types of tools including indexes, scripts, and connections.

This class provides functionality to create and manage different types of tools:
- Script models (utility models)
- Search collections (index models)
- Connectors (integration models)

The factory inherits from ModelGetterMixin and ModelListMixin to provide model retrieval
and listing capabilities.

**Attributes**:

- `backend_url` - The URL endpoint for the backend API.

#### recreate

```python
@classmethod
def recreate(cls,
             integration: Optional[Union[Text, Model]] = None,
             tool: Optional[Union[Text, Model]] = None,
             params: Optional[Union[BaseUtilityModelParams, BaseIndexParams,
                                    BaseAuthenticationParams]] = None,
             data: Optional[Dict] = None,
             **kwargs) -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/tool_factory.py#L35)

Recreates a tool based on an existing tool&#x27;s configuration.

This method creates a new tool instance using the configuration of an existing tool.
It&#x27;s useful for creating copies or variations of existing tools.

**Arguments**:

- `integration` _Optional[Union[Text, Model]], optional_ - The integration model or its ID. Defaults to None.
- `tool` _Optional[Union[Text, Model]], optional_ - The existing tool model or its ID to recreate from. Defaults to None.
  params (Optional[Union[BaseUtilityModelParams, BaseIndexParams, BaseAuthenticationParams]], optional):
  Parameters for the new tool. Defaults to None.
- `data` _Optional[Dict], optional_ - Additional data for tool creation. Defaults to None.
- `**kwargs` - Additional keyword arguments passed to the tool creation process.
  

**Returns**:

- `Model` - The newly created tool model.

#### create

```python
@classmethod
def create(cls,
           integration: Optional[Union[Text, Model]] = None,
           params: Optional[Union[BaseUtilityModelParams, BaseIndexParams,
                                  BaseAuthenticationParams]] = None,
           authentication_schema: Optional[AuthenticationSchema] = None,
           data: Optional[Dict] = None,
           **kwargs) -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/tool_factory.py#L65)

Factory method to create indexes, script models and connections

**Examples**:

  Create a script model (option 1):
  Option 1:
  from aixplain.modules.model.utility_model import BaseUtilityModelParams
  
  def add(a: int, b: int) -&gt; int:
  return a + b
  
  params = BaseUtilityModelParams(
  name=&quot;My Script Model&quot;,
  description=&quot;My Script Model Description&quot;,
  code=add
  )
  tool = ToolFactory.create(params=params)
  
  Option 2:
  def add(a: int, b: int) -&gt; int:
  &quot;&quot;&quot;Add two numbers&quot;&quot;&quot;
  return a + b
  
  tool = ToolFactory.create(
  name=&quot;My Script Model&quot;,
  code=add
  )
  
  Create a search collection:
  Option 1:
  from aixplain.factories.index_factory.utils import AirParams
  
  params = AirParams(
  name=&quot;My Search Collection&quot;,
  description=&quot;My Search Collection Description&quot;
  )
  tool = ToolFactory.create(params=params)
  
  Option 2:
  from aixplain.enums.index_stores import IndexStores
  
  tool = ToolFactory.create(
  integration=IndexStores.VECTARA.get_model_id(),
  name=&quot;My Search Collection&quot;,
  description=&quot;My Search Collection Description&quot;
  )
  
  Create a connector:
  Option 1:
  from aixplain.modules.model.connector import BearerAuthenticationParams
  
  params = BearerAuthenticationParams(
  connector_id=&quot;my_connector_id&quot;,
  token=&quot;my_token&quot;,
  name=&quot;My Connection&quot;
  )
  tool = ToolFactory.create(params=params)
  
  Option 2:
  tool = ToolFactory.create(
  integration=&quot;my_connector_id&quot;,
  name=&quot;My Connection&quot;,
  token=&quot;my_token&quot;
  )
  

**Arguments**:

- `params` - The parameters for the tool

**Returns**:

  The created tool

