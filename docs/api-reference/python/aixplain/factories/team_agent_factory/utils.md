---
sidebar_label: utils
title: aixplain.factories.team_agent_factory.utils
---

#### build\_team\_agent

```python
def build_team_agent(payload: Dict,
                     agents: List[Agent] = None,
                     api_key: Text = config.TEAM_API_KEY) -> TeamAgent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/utils.py#L23)

Build a TeamAgent instance from configuration payload.

This function creates a TeamAgent instance from a configuration payload,
handling the setup of agents, LLMs, inspectors, and task dependencies.

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
  - inspectors: Optional list of inspector configurations
  - inspectorTargets: Optional list of inspection targets
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

#### is\_yaml\_formatted

```python
def is_yaml_formatted(text)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/team_agent_factory/utils.py#L231)

Check if a string is valid YAML format with additional validation.

**Arguments**:

- `text` _str_ - The string to check
  

**Returns**:

- `bool` - True if valid YAML, False otherwise

