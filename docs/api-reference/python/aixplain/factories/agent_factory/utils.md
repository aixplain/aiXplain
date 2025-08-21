---
sidebar_label: utils
title: aixplain.factories.agent_factory.utils
---

#### build\_tool\_payload

```python
def build_tool_payload(tool: Union[Tool, Model])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/utils.py#L26)

Build a tool payload from a tool or model object.

**Arguments**:

- `tool` _Union[Tool, Model]_ - The tool or model object to build the payload from.
  

**Returns**:

- `Dict` - The tool payload.

#### build\_tool

```python
def build_tool(tool: Dict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/utils.py#L56)

Build a tool from a dictionary.

**Arguments**:

- `tool` _Dict_ - Tool dictionary.
  

**Returns**:

- `Tool` - Tool object.

#### build\_llm

```python
def build_llm(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> LLM
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/utils.py#L119)

Build a Large Language Model (LLM) instance from a dictionary configuration.

This function attempts to create an LLM instance either from a cached LLM object
in the payload or by creating a new instance using the provided configuration.

**Arguments**:

- `payload` _Dict_ - Dictionary containing LLM configuration and possibly a cached
  LLM object.
- `api_key` _Text, optional_ - API key for authentication. Defaults to config.TEAM_API_KEY.
  

**Returns**:

- `LLM` - Instantiated LLM object with configured parameters.

#### build\_agent

```python
def build_agent(payload: Dict,
                tools: List[Tool] = None,
                api_key: Text = config.TEAM_API_KEY) -> Agent
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/agent_factory/utils.py#L170)

Build an agent instance from a dictionary configuration.

This function creates an agent with its associated tools, LLM, and tasks based
on the provided configuration.

**Arguments**:

- `payload` _Dict_ - Dictionary containing agent configuration including tools,
  LLM settings, and tasks.
- `tools` _List[Tool], optional_ - List of pre-configured tools to use. If None,
  tools will be built from the payload. Defaults to None.
- `api_key` _Text, optional_ - API key for authentication. Defaults to config.TEAM_API_KEY.
  

**Returns**:

- `Agent` - Instantiated agent object with configured tools, LLM, and tasks.
  

**Raises**:

- `ValueError` - If a tool type is not supported.
- `AssertionError` - If tool configuration is invalid.

