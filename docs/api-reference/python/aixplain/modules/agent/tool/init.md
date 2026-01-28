---
sidebar_label: tool
title: aixplain.modules.agent.tool
---

Agent tool module for aiXplain SDK.

This module provides tool classes and functionality for agents to interact with
various services, models, and data sources.

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

### Tool Objects

```python
class Tool(ABC)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L33)

Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

**Attributes**:

- `name` _Text_ - name of the tool
- `description` _Text_ - description of the tool
- `version` _Text_ - version of the tool

#### \_\_init\_\_

```python
def __init__(name: Text,
             description: Text,
             version: Optional[Text] = None,
             api_key: Optional[Text] = config.TEAM_API_KEY,
             status: Optional[AssetStatus] = AssetStatus.DRAFT,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L42)

Initialize a new Tool instance.

**Arguments**:

- `name` _Text_ - The name of the tool.
- `description` _Text_ - A description of the tool&#x27;s functionality.
- `version` _Optional[Text], optional_ - The version of the tool. Defaults to None.
- `api_key` _Optional[Text], optional_ - The API key for authentication. Defaults to config.TEAM_API_KEY.
- `status` _Optional[AssetStatus], optional_ - The current status of the tool. Defaults to AssetStatus.DRAFT.
- `**additional_info` - Additional keyword arguments for tool configuration.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L68)

Converts the tool instance to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the tool&#x27;s attributes and configuration.
  

**Raises**:

- `NotImplementedError` - This is an abstract method that must be implemented by subclasses.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L79)

Validates the tool&#x27;s configuration and settings.

This method should check if all required attributes are properly set and
if the tool&#x27;s configuration is valid.

**Raises**:

- `NotImplementedError` - This is an abstract method that must be implemented by subclasses.

### DeployableTool Objects

```python
class DeployableTool(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L91)

Tool that can be deployed.

#### deploy

```python
def deploy() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/__init__.py#L94)

Deploy the tool.

