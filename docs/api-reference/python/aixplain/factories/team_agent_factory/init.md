---
sidebar_label: team_agent_factory
title: aixplain.factories.team_agent_factory
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
Date: August 15th 2024
Description:
    TeamAgent Factory Class

### TeamAgentFactory Objects

```python
class TeamAgentFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/__init__.py#L43)

Factory class for creating and managing team agents.

This class provides functionality for creating new team agents, retrieving existing
team agents, and managing team agent configurations in the aiXplain platform.
Team agents can be composed of multiple individual agents, LLMs, and inspectors
working together to accomplish complex tasks.

#### create

```python
@classmethod
def create(cls,
           name: Text,
           agents: List[Union[Text, Agent]],
           llm_id: Text = "669a63646eb56306647e1091",
           llm: Optional[Union[LLM, Text]] = None,
           supervisor_llm: Optional[Union[LLM, Text]] = None,
           mentalist_llm: Optional[Union[LLM, Text]] = None,
           description: Text = "",
           api_key: Text = config.TEAM_API_KEY,
           supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
           version: Optional[Text] = None,
           use_mentalist: bool = True,
           inspectors: List[Inspector] = [],
           inspector_targets: List[Union[InspectorTarget,
                                         Text]] = [InspectorTarget.STEPS],
           instructions: Optional[Text] = None,
           output_format: Optional[OutputFormat] = None,
           expected_output: Optional[Union[BaseModel, Text, dict]] = None,
           **kwargs) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/__init__.py#L53)

Create a new team agent in the platform.

**Arguments**:

- `name` - The name of the team agent.
- `agents` - A list of agents to be added to the team.
- `llm_id` - The ID of the LLM to be used for the team agent.
- `llm` _Optional[Union[LLM, Text]], optional_ - The LLM to be used for the team agent.
- `supervisor_llm` _Optional[Union[LLM, Text]], optional_ - Main supervisor LLM. Defaults to None.
- `mentalist_llm` _Optional[Union[LLM, Text]], optional_ - LLM for planning. Defaults to None.
- `description` - The description of the team agent to be displayed in the aiXplain platform.
- `api_key` - The API key to be used for the team agent.
- `supplier` - The supplier of the team agent.
- `version` - The version of the team agent.
- `agents`0 - Whether to use the mentalist agent.
- `agents`1 - A list of inspectors to be added to the team.
- `agents`2 - Which stages to be inspected during an execution of the team agent. (steps, output)
- `agents`3 - Whether to use the mentalist and inspector agents. (legacy)
- `agents`4 - The instructions to guide the team agent (i.e. appended in the prompt of the team agent).
- `agents`5 - The output format to be used for the team agent.
- `agents`6 - The expected output to be used for the team agent.

**Returns**:

  A new team agent instance.

#### create\_from\_dict

```python
@classmethod
def create_from_dict(cls, dict: Dict) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/__init__.py#L264)

Create a team agent from a dictionary representation.

This method instantiates a TeamAgent object from a dictionary containing
the agent&#x27;s configuration.

**Arguments**:

- `dict` _Dict_ - Dictionary containing team agent configuration including:
  - id: Team agent identifier
  - name: Team agent name
  - agents: List of agent configurations
  - llm: Optional LLM configuration
  - supervisor_llm: Optional supervisor LLM configuration
  - mentalist_llm: Optional mentalist LLM configuration
  

**Returns**:

- `TeamAgent` - Instantiated team agent with validated configuration.
  

**Raises**:

- `Exception` - If validation fails or required fields are missing.

#### list

```python
@classmethod
def list(cls) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/__init__.py#L291)

List all team agents available in the platform.

This method retrieves all team agents accessible to the current user,
using the configured API key.

**Returns**:

- `Dict` - Response containing:
  - results (List[TeamAgent]): List of team agent objects
  - page_total (int): Total items in current page
  - page_number (int): Current page number (always 0)
  - total (int): Total number of team agents
  

**Raises**:

- `Exception` - If the request fails or returns an error, including cases
  where authentication fails or the service is unavailable.

#### get

```python
@classmethod
def get(cls,
        agent_id: Optional[Text] = None,
        name: Optional[Text] = None,
        api_key: Optional[Text] = None) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/__init__.py#L343)

Retrieve a team agent by its ID or name.

This method fetches a specific team agent from the platform using its
unique identifier or name.

**Arguments**:

- `agent_id` _Optional[Text], optional_ - Unique identifier of the team agent to retrieve.
- `name` _Optional[Text], optional_ - Name of the team agent to retrieve.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `TeamAgent` - Retrieved team agent with its full configuration.
  

**Raises**:

- `Exception` - If:
  - Team agent ID/name is invalid
  - Authentication fails
  - Service is unavailable
  - Other API errors occur
- `ValueError` - If neither agent_id nor name is provided, or if both are provided.

