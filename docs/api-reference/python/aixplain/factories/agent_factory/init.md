---
sidebar_label: agent_factory
title: aixplain.factories.agent_factory
---

#### \_\_author\_\_

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

Author: Thiago Castro Ferreira and Lucas Pavanelli
Date: May 16th 2024
Description:
    Agent Factory Class

### AgentFactory Objects

```python
class AgentFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L52)

Factory class for creating and managing agents in the aiXplain system.

This class provides class methods for creating various types of agents and tools,
as well as managing existing agents in the platform.

#### create

```python
@classmethod
def create(
        cls,
        name: Text,
        description: Text,
        instructions: Optional[Text] = None,
        llm: Optional[Union[LLM, Text]] = None,
        llm_id: Optional[Text] = None,
        tools: Optional[List[Union[Tool, Model]]] = None,
        api_key: Text = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        tasks: List[WorkflowTask] = None,
        workflow_tasks: Optional[List[WorkflowTask]] = None,
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text,
                                        dict]] = None) -> Agent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L60)

Create a new agent in the platform.

**Warnings**:

  The &#x27;instructions&#x27; parameter was recently added and serves the same purpose as &#x27;description&#x27; did previously: set the role of the agent as a system prompt.
  The &#x27;description&#x27; parameter is still required and should be used to set a short summary of the agent&#x27;s purpose.
  For the next releases, the &#x27;instructions&#x27; parameter will be required.
  

**Arguments**:

- `name` _Text_ - name of the agent
- `description` _Text_ - description of the agent instructions.
- `instructions` _Text_ - instructions of the agent.
- `llm` _Optional[Union[LLM, Text]], optional_ - LLM instance to use as an object or as an ID.
- `llm_id` _Optional[Text], optional_ - ID of LLM to use if no LLM instance provided. Defaults to None.
- `tools` _List[Union[Tool, Model]], optional_ - list of tool for the agent. Defaults to [].
- `api_key` _Text, optional_ - team/user API key. Defaults to config.TEAM_API_KEY.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - owner of the agent. Defaults to &quot;aiXplain&quot;.
- `version` _Optional[Text], optional_ - version of the agent. Defaults to None.
- `workflow_tasks` _List[WorkflowTask], optional_ - list of tasks for the agent. Defaults to [].
- `description`0 _OutputFormat, optional_ - default output format for agent responses. Defaults to OutputFormat.TEXT.
- `description`1 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.

**Returns**:

- `description`2 - created Agent

#### create\_from\_dict

```python
@classmethod
def create_from_dict(cls, dict: Dict) -> Agent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L206)

Create an agent instance from a dictionary representation.

**Arguments**:

- `dict` _Dict_ - Dictionary containing agent configuration and properties.
  

**Returns**:

- `Agent` - Instantiated agent object with properties from the dictionary.
  

**Raises**:

- `Exception` - If agent validation fails or required properties are missing.

#### create\_model\_tool

```python
@classmethod
def create_model_tool(cls,
                      model: Optional[Union[Model, Text]] = None,
                      function: Optional[Union[Function, Text]] = None,
                      supplier: Optional[Union[Supplier, Text]] = None,
                      description: Text = "",
                      parameters: Optional[Dict] = None,
                      name: Optional[Text] = None) -> ModelTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L250)

Create a new model tool for use with an agent.

**Arguments**:

- `model` _Optional[Union[Model, Text]], optional_ - Model instance or ID. Defaults to None.
- `function` _Optional[Union[Function, Text]], optional_ - Function enum or ID. Defaults to None.
- `supplier` _Optional[Union[Supplier, Text]], optional_ - Supplier enum or name. Defaults to None.
- `description` _Text, optional_ - Description of the tool. Defaults to &quot;&quot;.
- `parameters` _Optional[Dict], optional_ - Tool parameters. Defaults to None.
- `name` _Optional[Text], optional_ - Name of the tool. Defaults to None.
  

**Returns**:

- `ModelTool` - Created model tool object.
  

**Raises**:

- `AssertionError` - If the supplier is not valid.

#### create\_pipeline\_tool

```python
@classmethod
def create_pipeline_tool(cls,
                         description: Text,
                         pipeline: Union[Pipeline, Text],
                         name: Optional[Text] = None) -> PipelineTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L298)

Create a new pipeline tool for use with an agent.

**Arguments**:

- `description` _Text_ - Description of what the pipeline tool does.
- `pipeline` _Union[Pipeline, Text]_ - Pipeline instance or pipeline ID.
- `name` _Optional[Text], optional_ - Name of the tool. Defaults to None.
  

**Returns**:

- `PipelineTool` - Created pipeline tool object.

#### create\_python\_interpreter\_tool

```python
@classmethod
def create_python_interpreter_tool(cls) -> PythonInterpreterTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L317)

Create a new Python interpreter tool for use with an agent.

This tool allows the agent to execute Python code in a controlled environment.

**Returns**:

- `PythonInterpreterTool` - Created Python interpreter tool object.

#### create\_custom\_python\_code\_tool

```python
@classmethod
def create_custom_python_code_tool(
        cls,
        code: Union[Text, Callable],
        name: Text,
        description: Text = "") -> ConnectionTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L328)

Create a new custom Python code tool for use with an agent.

**Arguments**:

- `code` _Union[Text, Callable]_ - Python code as string or callable function.
- `name` _Text_ - Name of the tool.
- `description` _Text, optional_ - Description of what the tool does. Defaults to &quot;&quot;.
  

**Returns**:

- `ConnectionTool` - Created custom Python code tool object.

#### create\_sql\_tool

```python
@classmethod
def create_sql_tool(cls,
                    name: Text,
                    description: Text,
                    source: str,
                    source_type: Union[str, DatabaseSourceType],
                    schema: Optional[Text] = None,
                    tables: Optional[List[Text]] = None,
                    enable_commit: bool = False) -> SQLTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L344)

Create a new SQL tool

**Arguments**:

- `name` _Text_ - name of the tool
- `description` _Text_ - description of the database tool
- `source` _Union[Text, Dict]_ - database source - can be a connection string or dictionary with connection details
- `source_type` _Union[str, DatabaseSourceType]_ - type of source (postgresql, sqlite, csv) or DatabaseSourceType enum
- `schema` _Optional[Text], optional_ - database schema description
- `tables` _Optional[List[Text]], optional_ - table names to work with (optional)
- `enable_commit` _bool, optional_ - enable to modify the database (optional)

**Returns**:

- `SQLTool` - created SQLTool
  

**Examples**:

  # CSV - Simple
  sql_tool = AgentFactory.create_sql_tool(
  description=&quot;My CSV Tool&quot;,
  source=&quot;/path/to/data.csv&quot;,
  source_type=&quot;csv&quot;,
  tables=[&quot;data&quot;]
  )
  
  # SQLite - Simple
  sql_tool = AgentFactory.create_sql_tool(
  description=&quot;My SQLite Tool&quot;,
  source=&quot;/path/to/database.sqlite&quot;,
  source_type=&quot;sqlite&quot;,
  tables=[&quot;users&quot;, &quot;products&quot;]
  )

#### list

```python
@classmethod
def list(cls) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L477)

List all agents available in the platform.

**Returns**:

- `Dict` - Dictionary containing:
  - results (List[Agent]): List of available agents.
  - page_total (int): Number of agents in current page.
  - page_number (int): Current page number.
  - total (int): Total number of agents.
  

**Raises**:

- `Exception` - If there is an error listing the agents.

#### get

```python
@classmethod
def get(cls,
        agent_id: Optional[Text] = None,
        name: Optional[Text] = None,
        api_key: Optional[Text] = None) -> Agent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/__init__.py#L531)

Retrieve an agent by its ID or name.

**Arguments**:

- `agent_id` _Optional[Text], optional_ - ID of the agent to retrieve.
- `name` _Optional[Text], optional_ - Name of the agent to retrieve.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `Agent` - Retrieved agent object.
  

**Raises**:

- `Exception` - If the agent cannot be retrieved or doesn&#x27;t exist.
- `ValueError` - If neither agent_id nor name is provided, or if both are provided.

