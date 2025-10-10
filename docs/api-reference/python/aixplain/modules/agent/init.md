---
sidebar_label: agent
title: aixplain.modules.agent
---

Agent module for aiXplain SDK.

This module provides the Agent class and related functionality for creating and managing
AI agents that can execute tasks using various tools and models.

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

### Agent Objects

```python
class Agent(Model, DeployableMixin[Union[Tool, DeployableTool]])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L56)

An advanced AI system that performs tasks using specialized tools from the aiXplain marketplace.

This class represents an AI agent that can understand natural language instructions,
use various tools and models, and execute complex tasks. It combines a large language
model (LLM) with specialized tools to provide comprehensive task-solving capabilities.

**Attributes**:

- `id` _Text_ - ID of the Agent.
- `name` _Text_ - Name of the Agent.
- `tools` _List[Union[Tool, Model]]_ - Collection of tools and models the Agent can use.
- `description` _Text, optional_ - Detailed description of the Agent&#x27;s capabilities.
  Defaults to &quot;&quot;.
- `instructions` _Text_ - System instructions/prompt defining the Agent&#x27;s behavior.
- `llm_id` _Text_ - ID of the large language model. Defaults to GPT-4o
  (6646261c6eb563165658bbb1).
- `llm` _Optional[LLM]_ - The LLM instance used by the Agent.
- `supplier` _Text_ - The provider/creator of the Agent.
- `version` _Text_ - Version identifier of the Agent.
- `status` _AssetStatus_ - Current status of the Agent (DRAFT or ONBOARDED).
- `name`0 _List[AgentTask]_ - List of tasks the Agent can perform.
- `name`1 _str_ - URL endpoint for the backend API.
- `name`2 _str_ - Authentication key for API access.
- `name`3 _Dict, optional_ - Pricing information for using the Agent. Defaults to None.
- `name`4 _bool_ - Whether the Agent&#x27;s configuration is valid.
- `name`3 _Dict, optional_ - model price. Defaults to None.
- `name`6 _OutputFormat_ - default output format for agent responses.
- `name`7 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text,
             instructions: Optional[Text] = None,
             tools: List[Union[Tool, Model]] = [],
             llm_id: Text = "6646261c6eb563165658bbb1",
             llm: Optional[LLM] = None,
             api_key: Optional[Text] = config.TEAM_API_KEY,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             cost: Optional[Dict] = None,
             status: AssetStatus = AssetStatus.DRAFT,
             tasks: List[AgentTask] = [],
             workflow_tasks: List[WorkflowTask] = [],
             output_format: OutputFormat = OutputFormat.TEXT,
             expected_output: Optional[Union[BaseModel, Text, dict]] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L88)

Initialize a new Agent instance.

**Arguments**:

- `id` _Text_ - ID of the Agent.
- `name` _Text_ - Name of the Agent.
- `description` _Text_ - Detailed description of the Agent&#x27;s capabilities.
- `instructions` _Optional[Text], optional_ - System instructions/prompt defining
  the Agent&#x27;s behavior. Defaults to None.
- `tools` _List[Union[Tool, Model]], optional_ - Collection of tools and models
  the Agent can use. Defaults to empty list.
- `llm_id` _Text, optional_ - ID of the large language model. Defaults to GPT-4o
  (6646261c6eb563165658bbb1).
- `llm` _Optional[LLM], optional_ - The LLM instance to use. If provided, takes
  precedence over llm_id. Defaults to None.
- `api_key` _Optional[Text], optional_ - Authentication key for API access.
  Defaults to config.TEAM_API_KEY.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - The provider/creator
  of the Agent. Defaults to &quot;aiXplain&quot;.
- `version` _Optional[Text], optional_ - Version identifier. Defaults to None.
- `name`0 _Optional[Dict], optional_ - Pricing information. Defaults to None.
- `name`1 _AssetStatus, optional_ - Current status of the Agent.
  Defaults to AssetStatus.DRAFT.
- `name`2 _List[AgentTask], optional_ - List of tasks the Agent can perform.
  Defaults to empty list.
- `name`3 _List[WorkflowTask], optional_ - List of workflow tasks
  the Agent can execute. Defaults to empty list.
- `name`4 _OutputFormat, optional_ - default output format for agent responses. Defaults to OutputFormat.TEXT.
- `name`5 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.
- `name`6 - Additional configuration parameters.

#### validate

```python
def validate(raise_exception: bool = False) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L215)

Validate the Agent&#x27;s configuration and mark its validity status.

This method runs all validation checks and updates the is_valid flag.
If validation fails, it can either raise an exception or log warnings.

**Arguments**:

- `raise_exception` _bool, optional_ - Whether to raise exceptions on validation
  failures. If False, failures are logged as warnings. Defaults to False.
  

**Returns**:

- `bool` - True if validation passed, False otherwise.
  

**Raises**:

- `Exception` - If validation fails and raise_exception is True.

#### generate\_session\_id

```python
def generate_session_id(history: list = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L243)

Generate a unique session ID for agent conversations.

**Arguments**:

- `history` _list, optional_ - Previous conversation history. Defaults to None.
  

**Returns**:

- `str` - A unique session identifier based on timestamp and random components.

#### run

```python
def run(data: Optional[Union[Dict, Text]] = None,
        query: Optional[Text] = None,
        session_id: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Dict = {},
        wait_time: float = 0.5,
        content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
        max_tokens: int = 4096,
        max_iterations: int = 5,
        output_format: Optional[OutputFormat] = None,
        expected_output: Optional[Union[BaseModel, Text, dict]] = None,
        trace_request: bool = False) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L294)

Runs an agent call.

**Arguments**:

- `data` _Optional[Union[Dict, Text]], optional_ - data to be processed by the agent. Defaults to None.
- `query` _Optional[Text], optional_ - query to be processed by the agent. Defaults to None.
- `session_id` _Optional[Text], optional_ - conversation Session ID. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - chat history (in case session ID is None). Defaults to None.
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;model_process&quot;.
- `timeout` _float, optional_ - total polling time. Defaults to 300.
- `parameters` _Dict, optional_ - optional parameters to the model. Defaults to &quot;\{}&quot;.
- `wait_time` _float, optional_ - wait time in seconds between polling calls. Defaults to 0.5.
- `content` _Union[Dict[Text, Text], List[Text]], optional_ - Content inputs to be processed according to the query. Defaults to None.
- `max_tokens` _int, optional_ - maximum number of tokens which can be generated by the agent. Defaults to 2048.
- `query`0 _int, optional_ - maximum number of iterations between the agent and the tools. Defaults to 10.
- `query`1 _OutputFormat, optional_ - response format. If not provided, uses the format set during initialization.
- `query`2 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.
- `query`3 _bool, optional_ - return the request id for tracing the request. Defaults to False.

**Returns**:

- `query`4 - parsed output from model

#### run\_async

```python
def run_async(data: Optional[Union[Dict, Text]] = None,
              query: Optional[Text] = None,
              session_id: Optional[Text] = None,
              history: Optional[List[Dict]] = None,
              name: Text = "model_process",
              parameters: Dict = {},
              content: Optional[Union[Dict[Text, Text], List[Text]]] = None,
              max_tokens: int = 2048,
              max_iterations: int = 5,
              output_format: Optional[OutputFormat] = None,
              expected_output: Optional[Union[BaseModel, Text, dict]] = None,
              evolve: Union[Dict[str, Any], EvolveParam, None] = None,
              trace_request: bool = False) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L397)

Runs asynchronously an agent call.

**Arguments**:

- `data` _Optional[Union[Dict, Text]], optional_ - data to be processed by the agent. Defaults to None.
- `query` _Optional[Text], optional_ - query to be processed by the agent. Defaults to None.
- `session_id` _Optional[Text], optional_ - conversation Session ID. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - chat history (in case session ID is None). Defaults to None.
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;model_process&quot;.
- `parameters` _Dict, optional_ - optional parameters to the model. Defaults to &quot;\{}&quot;.
- `content` _Union[Dict[Text, Text], List[Text]], optional_ - Content inputs to be processed according to the query. Defaults to None.
- `max_tokens` _int, optional_ - maximum number of tokens which can be generated by the agent. Defaults to 2048.
- `max_iterations` _int, optional_ - maximum number of iterations between the agent and the tools. Defaults to 10.
- `output_format` _OutputFormat, optional_ - response format. If not provided, uses the format set during initialization.
- `query`0 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.
- `output_format` _ResponseFormat, optional_ - response format. Defaults to TEXT.
- `query`2 _Union[Dict[str, Any], EvolveParam, None], optional_ - evolve the agent configuration. Can be a dictionary, EvolveParam instance, or None.
- `query`3 _bool, optional_ - return the request id for tracing the request. Defaults to False.

**Returns**:

- `query`4 - polling URL in response

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L540)

Convert the Agent instance to a dictionary representation.

**Returns**:

- `Dict` - Dictionary containing the agent&#x27;s configuration and metadata.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L577)

Create an Agent instance from a dictionary representation.

**Arguments**:

- `data` - Dictionary containing Agent parameters
  

**Returns**:

  Agent instance

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L652)

Delete this Agent from the aiXplain platform.

This method attempts to delete the Agent. The operation will fail if the
Agent is being used by any team agents.

**Raises**:

- `Exception` - If deletion fails, with detailed error messages for different
  failure scenarios:
  - Agent is in use by accessible team agents (lists team agent IDs)
  - Agent is in use by inaccessible team agents
  - Other deletion errors (with HTTP status code)

#### update

```python
def update() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L715)

Update the Agent&#x27;s configuration on the aiXplain platform.

This method validates and updates the Agent&#x27;s configuration. It is deprecated
in favor of the save() method.

**Raises**:

- `Exception` - If validation fails or if there are errors during the update.
- `DeprecationWarning` - This method is deprecated, use save() instead.
  

**Notes**:

  This method is deprecated and will be removed in a future version.
  Please use save() instead.

#### save

```python
def save() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L762)

Save the Agent&#x27;s current configuration to the aiXplain platform.

This method validates and saves any changes made to the Agent&#x27;s configuration.
It is the preferred method for updating an Agent&#x27;s settings.

**Raises**:

- `Exception` - If validation fails or if there are errors during the save operation.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L773)

Return a string representation of the Agent.

**Returns**:

- `str` - A string in the format &quot;Agent: &lt;name&gt; (id=&lt;id&gt;)&quot;.

#### evolve\_async

```python
def evolve_async(evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
                 max_successful_generations: int = 3,
                 max_failed_generation_retries: int = 3,
                 max_iterations: int = 50,
                 max_non_improving_generations: Optional[int] = 2,
                 llm: Optional[Union[Text, LLM]] = None) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L781)

Asynchronously evolve the Agent and return a polling URL in the AgentResponse.

**Arguments**:

- `evolve_type` _Union[EvolveType, str]_ - Type of evolution (TEAM_TUNING or INSTRUCTION_TUNING). Defaults to TEAM_TUNING.
- `max_successful_generations` _int_ - Maximum number of successful generations to evolve. Defaults to 3.
- `max_failed_generation_retries` _int_ - Maximum retry attempts for failed generations. Defaults to 3.
- `max_iterations` _int_ - Maximum number of iterations. Defaults to 50.
- `max_non_improving_generations` _Optional[int]_ - Stop condition parameter for non-improving generations. Defaults to 2, can be None.
- `llm` _Optional[Union[Text, LLM]]_ - LLM to use for evolution. Can be an LLM ID string or LLM object. Defaults to None.
  

**Returns**:

- `AgentResponse` - Response containing polling URL and status.

#### evolve

```python
def evolve(evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
           max_successful_generations: int = 3,
           max_failed_generation_retries: int = 3,
           max_iterations: int = 50,
           max_non_improving_generations: Optional[int] = 2,
           llm: Optional[Union[Text, LLM]] = None) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/__init__.py#L820)

Synchronously evolve the Agent and poll for the result.

**Arguments**:

- `evolve_type` _Union[EvolveType, str]_ - Type of evolution (TEAM_TUNING or INSTRUCTION_TUNING). Defaults to TEAM_TUNING.
- `max_successful_generations` _int_ - Maximum number of successful generations to evolve. Defaults to 3.
- `max_failed_generation_retries` _int_ - Maximum retry attempts for failed generations. Defaults to 3.
- `max_iterations` _int_ - Maximum number of iterations. Defaults to 50.
- `max_non_improving_generations` _Optional[int]_ - Stop condition parameter for non-improving generations. Defaults to 2, can be None.
- `llm` _Optional[Union[Text, LLM]]_ - LLM to use for evolution. Can be an LLM ID string or LLM object. Defaults to None.
  

**Returns**:

- `AgentResponse` - Final response from the evolution process.

