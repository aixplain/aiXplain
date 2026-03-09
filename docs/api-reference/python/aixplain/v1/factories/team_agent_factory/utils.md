---
sidebar_label: utils
title: aixplain.v1.factories.team_agent_factory.utils
---

Utils for building team agents.

#### build\_team\_agent

```python
def build_team_agent(payload: Dict,
                     agents: List[Agent] = None,
                     api_key: Text = config.TEAM_API_KEY) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/team_agent_factory/utils.py#L24)

Build a TeamAgent instance from configuration payload.

This function creates a TeamAgent instance from a configuration payload,
handling the setup of agents, LLMs,and task dependencies.

**Arguments**:

- `payload` _Dict_ - Configuration dictionary containing:
  - id: Optional team agent ID
  - name: Team agent name
  - agents: List of agent configurations
  - description: Optional description
  - instructions: Optional instructions
  - teamId: Optional supplier information
  - version: Optional version
  - cost: Optional cost information
  - llmId: LLM model ID (defaults to GPT-4)
  - plannerId: Optional planner model ID
  - status: Team agent status
  - tools: Optional list of tool configurations
- `agents` _List[Agent], optional_ - Pre-instantiated agent objects. If not
  provided, agents will be instantiated from IDs in the payload.
  Defaults to None.
- `api_key` _Text, optional_ - API key for authentication. Defaults to
  config.TEAM_API_KEY.
  

**Returns**:

- `TeamAgent` - Configured team agent instance with all components initialized.
  

**Raises**:

- `Exception` - If a task dependency referenced in an agent&#x27;s configuration
  cannot be found.

#### parse\_tool\_from\_yaml

```python
def parse_tool_from_yaml(tool: str) -> ModelTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/team_agent_factory/utils.py#L177)

Parse a tool from a string.

#### is\_yaml\_formatted

```python
def is_yaml_formatted(text)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/team_agent_factory/utils.py#L211)

Check if a string is valid YAML format with additional validation.

**Arguments**:

- `text` _str_ - The string to check
  

**Returns**:

- `bool` - True if valid YAML, False otherwise

#### build\_team\_agent\_from\_yaml

```python
def build_team_agent_from_yaml(yaml_code: str,
                               llm_id: str,
                               api_key: str,
                               team_id: Optional[str] = None) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/team_agent_factory/utils.py#L244)

Build a team agent from a YAML string.

