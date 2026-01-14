---
sidebar_label: team_agent
title: aixplain.modules.team_agent
---

Team Agent module for aiXplain SDK.

This module provides the TeamAgent class and related functionality for creating and managing
multi-agent teams that can collaborate on complex tasks.

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
Date: August 15th 2024
Description:
    Team Agent Class

### InspectorTarget Objects

```python
class InspectorTarget(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L61)

Target stages for inspector validation in the team agent pipeline.

This enumeration defines the stages where inspectors can be applied to
validate and ensure quality of the team agent&#x27;s operation.

**Attributes**:

- `INPUT` - Validates the input data before processing.
- `STEPS` - Validates intermediate steps during processing.
- `OUTPUT` - Validates the final output before returning.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L77)

Return the string value of the enum member.

**Returns**:

- `str` - The string value associated with the enum member.

### TeamAgent Objects

```python
class TeamAgent(Model, DeployableMixin[Agent])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L86)

Advanced AI system capable of using multiple agents to perform a variety of tasks.

**Attributes**:

- `id` _Text_ - ID of the Team Agent
- `name` _Text_ - Name of the Team Agent
- `agents` _List[Agent]_ - List of agents that the Team Agent uses.
- `description` _Text, optional_ - description of the Team Agent. Defaults to &quot;&quot;.
- `llm` _Optional[LLM]_ - Main LLM instance for the team agent.
- `supervisor_llm` _Optional[LLM]_ - Supervisor LLM instance for the team agent.
- `api_key` _str_ - The TEAM API key used for authentication.
- `supplier` _Text_ - Supplier of the Team Agent.
- `version` _Text_ - Version of the Team Agent.
- `cost` _Dict, optional_ - model price. Defaults to None.
- `name`0 _List[Inspector]_ - List of inspectors that the team agent uses.
- `name`1 _List[InspectorTarget]_ - List of targets where the inspectors are applied. Defaults to [InspectorTarget.STEPS].
- `name`2 _AssetStatus_ - Status of the Team Agent. Defaults to DRAFT.
- `name`3 _Optional[Text]_ - Instructions to guide the team agent.
- `name`4 _OutputFormat_ - Response format. Defaults to TEXT.
- `name`5 _Optional[Union[BaseModel, Text, dict]]_ - Expected output format.
  
  Deprecated Attributes:
- `name`6 _Text_ - DEPRECATED. Use &#x27;llm&#x27; parameter instead. Large language model ID.
- `name`7 _Optional[LLM]_ - DEPRECATED. LLM for planning.
- `name`8 _bool_ - DEPRECATED. Whether to use Mentalist agent for pre-planning.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             agents: List[Agent] = [],
             description: Text = "",
             llm: Optional[LLM] = None,
             supervisor_llm: Optional[LLM] = None,
             api_key: Optional[Text] = config.TEAM_API_KEY,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             cost: Optional[Dict] = None,
             inspectors: List[Inspector] = [],
             inspector_targets: List[InspectorTarget] = [
                 InspectorTarget.STEPS
             ],
             status: AssetStatus = AssetStatus.DRAFT,
             instructions: Optional[Text] = None,
             output_format: OutputFormat = OutputFormat.TEXT,
             expected_output: Optional[Union[BaseModel, Text, dict]] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L115)

Initialize a TeamAgent instance.

**Arguments**:

- `id` _Text_ - Unique identifier for the team agent.
- `name` _Text_ - Name of the team agent.
- `agents` _List[Agent], optional_ - List of agents in the team. Defaults to [].
- `description` _Text, optional_ - Description of the team agent. Defaults to &quot;&quot;.
- `llm` _Optional[LLM], optional_ - LLM instance. Defaults to None.
- `supervisor_llm` _Optional[LLM], optional_ - Supervisor LLM instance. Defaults to None.
- `api_key` _Optional[Text], optional_ - API key. Defaults to config.TEAM_API_KEY.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier. Defaults to &quot;aiXplain&quot;.
- `version` _Optional[Text], optional_ - Version. Defaults to None.
- `cost` _Optional[Dict], optional_ - Cost information. Defaults to None.
- `name`0 _List[Inspector], optional_ - List of inspectors. Defaults to [].
- `name`1 _List[InspectorTarget], optional_ - Inspector targets. Defaults to [InspectorTarget.STEPS].
- `name`2 _AssetStatus, optional_ - Status of the team agent. Defaults to AssetStatus.DRAFT.
- `name`3 _Optional[Text], optional_ - Instructions for the team agent. Defaults to None.
- `name`4 _OutputFormat, optional_ - Output format. Defaults to OutputFormat.TEXT.
- `name`5 _Optional[Union[BaseModel, Text, dict]], optional_ - Expected output format. Defaults to None.
- `name`6 - Additional keyword arguments.
  
  Deprecated Args:
- `name`7 _Text, optional_ - DEPRECATED. Use &#x27;llm&#x27; parameter instead. ID of the language model. Defaults to &quot;6646261c6eb563165658bbb1&quot;.
- `name`8 _Optional[LLM], optional_ - DEPRECATED. Mentalist/Planner LLM instance. Defaults to None.
- `name`9 _bool, optional_ - DEPRECATED. Whether to use mentalist/planner. Defaults to True.

#### generate\_session\_id

```python
def generate_session_id(history: list = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L252)

Generate a new session ID for the team agent.

**Arguments**:

- `history` _list, optional_ - Chat history to initialize the session with. Defaults to None.
  

**Returns**:

- `str` - The generated session ID in format &quot;\{team_agent_id}_\{timestamp}&quot;.

#### sync\_poll

```python
def sync_poll(poll_url: Text,
              name: Text = "model_process",
              wait_time: float = 0.5,
              timeout: float = 300,
              progress_verbosity: Optional[str] = "compact") -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L511)

Poll the platform until team agent execution completes or times out.

**Arguments**:

- `poll_url` _Text_ - URL to poll for operation status.
- `name` _Text, optional_ - Identifier for the operation. Defaults to &quot;model_process&quot;.
- `wait_time` _float, optional_ - Initial wait time in seconds between polls. Defaults to 0.5.
- `timeout` _float, optional_ - Maximum total time to poll in seconds. Defaults to 300.
- `progress_verbosity` _Optional[str], optional_ - Progress display mode - &quot;full&quot; (detailed), &quot;compact&quot; (brief), or None (no progress). Defaults to &quot;compact&quot;.
  

**Returns**:

- `AgentResponse` - The final response from the team agent execution.

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
        max_tokens: int = 2048,
        max_iterations: int = 30,
        trace_request: bool = False,
        progress_verbosity: Optional[str] = "compact",
        **kwargs) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L591)

Runs a team agent call.

**Arguments**:

- `data` _Optional[Union[Dict, Text]], optional_ - data to be processed by the team agent. Defaults to None.
- `query` _Optional[Text], optional_ - query to be processed by the team agent. Defaults to None.
- `session_id` _Optional[Text], optional_ - conversation Session ID. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - chat history (in case session ID is None). Defaults to None.
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;model_process&quot;.
- `timeout` _float, optional_ - total polling time. Defaults to 300.
- `parameters` _Dict, optional_ - optional parameters to the model. Defaults to &quot;\{}&quot;.
- `wait_time` _float, optional_ - wait time in seconds between polling calls. Defaults to 0.5.
- `content` _Union[Dict[Text, Text], List[Text]], optional_ - Content inputs to be processed according to the query. Defaults to None.
- `max_tokens` _int, optional_ - maximum number of tokens which can be generated by the agents. Defaults to 2048.
- `query`0 _int, optional_ - maximum number of iterations between the agents. Defaults to 30.
- `query`1 _bool, optional_ - return the request id for tracing the request. Defaults to False.
- `query`2 _Optional[str], optional_ - Progress display mode - &quot;full&quot; (detailed), &quot;compact&quot; (brief), or None (no progress). Defaults to &quot;compact&quot;.
- `query`3 - Additional deprecated keyword arguments (output_format, expected_output).
  

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
              max_iterations: int = 30,
              output_format: Optional[OutputFormat] = None,
              expected_output: Optional[Union[BaseModel, Text, dict]] = None,
              evolve: Union[Dict[str, Any], EvolveParam, None] = None,
              trace_request: bool = False) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L724)

Runs asynchronously a Team Agent call.

**Arguments**:

- `data` _Optional[Union[Dict, Text]], optional_ - data to be processed by the Team Agent. Defaults to None.
- `query` _Optional[Text], optional_ - query to be processed by the Team Agent. Defaults to None.
- `session_id` _Optional[Text], optional_ - conversation Session ID. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - chat history (in case session ID is None). Defaults to None.
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;model_process&quot;.
- `parameters` _Dict, optional_ - optional parameters to the model. Defaults to &quot;\{}&quot;.
- `content` _Union[Dict[Text, Text], List[Text]], optional_ - Content inputs to be processed according to the query. Defaults to None.
- `max_tokens` _int, optional_ - maximum number of tokens which can be generated by the agents. Defaults to 2048.
- `max_iterations` _int, optional_ - maximum number of iterations between the agents. Defaults to 30.
- `output_format` _OutputFormat, optional_ - response format. If not provided, uses the format set during initialization.
- `query`0 _Union[BaseModel, Text, dict], optional_ - expected output. Defaults to None.
- `query`1 _Union[Dict[str, Any], EvolveParam, None], optional_ - evolve the team agent configuration. Can be a dictionary, EvolveParam instance, or None.
- `query`2 _bool, optional_ - return the request id for tracing the request. Defaults to False.
  

**Returns**:

- `query`3 - polling URL in response

#### poll

```python
def poll(poll_url: Text, name: Text = "model_process") -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L888)

Poll once for team agent execution status.

**Arguments**:

- `poll_url` _Text_ - URL to poll for status.
- `name` _Text, optional_ - Identifier for the operation. Defaults to &quot;model_process&quot;.
  

**Returns**:

- `AgentResponse` - Response containing status, data, and progress information.

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L967)

Deletes Team Agent.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1031)

Convert the TeamAgent instance to a dictionary representation.

This method serializes the TeamAgent and all its components (agents,
inspectors, LLMs, etc.) into a dictionary format suitable for storage
or transmission.

**Returns**:

- `Dict` - A dictionary containing:
  - id (str): The team agent&#x27;s ID
  - name (str): The team agent&#x27;s name
  - agents (List[Dict]): Serialized list of agents
  - links (List): Empty list (reserved for future use)
  - description (str): The team agent&#x27;s description
  - llmId (str): ID of the main language model
  - supervisorId (str): ID of the supervisor language model
  - plannerId (str): ID of the planner model (if use_mentalist)
  - inspectors (List[Dict]): Serialized list of inspectors
  - inspectorTargets (List[str]): List of inspector target stages
  - supplier (str): The supplier code
  - version (str): The version number
  - status (str): The current status
  - instructions (str): The team agent&#x27;s instructions

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict) -> "TeamAgent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1090)

Create a TeamAgent instance from a dictionary representation.

**Arguments**:

- `data` - Dictionary containing TeamAgent parameters
  

**Returns**:

  TeamAgent instance

#### validate

```python
def validate(raise_exception: bool = False) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1222)

Validate the TeamAgent configuration.

This method checks the validity of the TeamAgent&#x27;s configuration,
including name format, LLM compatibility, and agent validity.

**Arguments**:

- `raise_exception` _bool, optional_ - If True, raises exceptions for
  validation failures. If False, logs warnings. Defaults to False.
  

**Returns**:

- `bool` - True if validation succeeds, False otherwise.
  

**Raises**:

- `Exception` - If raise_exception is True and validation fails, with
  details about the specific validation error.
  

**Notes**:

  - The team agent cannot be run until all validation issues are fixed
  - Name must contain only alphanumeric chars, spaces, hyphens, brackets
  - LLM must be a text generation model
  - All agents must pass their own validation

#### update

```python
def update() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1260)

Update the TeamAgent in the backend.

This method validates and updates the TeamAgent&#x27;s configuration in the
backend system. It is deprecated in favor of the save() method.

**Raises**:

- `Exception` - If validation fails or if the update request fails.
  Specific error messages will indicate:
  - Validation failures with details
  - HTTP errors with status codes
  - General update errors requiring admin attention
  

**Notes**:

  - This method is deprecated, use save() instead
  - Performs validation before attempting update
  - Requires valid team API key for authentication
  - Returns a new TeamAgent instance if successful

#### save

```python
def save() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1317)

Save the Agent.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1321)

Return a string representation of the TeamAgent.

**Returns**:

- `str` - A string in the format &quot;TeamAgent: &lt;name&gt; (id=&lt;id&gt;)&quot;.

#### evolve\_async

```python
def evolve_async(evolve_type: Union[EvolveType, str] = EvolveType.TEAM_TUNING,
                 max_successful_generations: int = 3,
                 max_failed_generation_retries: int = 3,
                 max_iterations: int = 50,
                 max_non_improving_generations: Optional[int] = 2,
                 llm: Optional[Union[Text, LLM]] = None) -> AgentResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1329)

Asynchronously evolve the Team Agent and return a polling URL in the AgentResponse.

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/team_agent/__init__.py#L1369)

Synchronously evolve the Team Agent and poll for the result.

**Arguments**:

- `evolve_type` _Union[EvolveType, str]_ - Type of evolution (TEAM_TUNING or INSTRUCTION_TUNING). Defaults to TEAM_TUNING.
- `max_successful_generations` _int_ - Maximum number of successful generations to evolve. Defaults to 3.
- `max_failed_generation_retries` _int_ - Maximum retry attempts for failed generations. Defaults to 3.
- `max_iterations` _int_ - Maximum number of iterations. Defaults to 50.
- `max_non_improving_generations` _Optional[int]_ - Stop condition parameter for non-improving generations. Defaults to 2, can be None.
- `llm` _Optional[Union[Text, LLM]]_ - LLM to use for evolution. Can be an LLM ID string or LLM object. Defaults to None.
  

**Returns**:

- `AgentResponse` - Final response from the evolution process.

