---
sidebar_label: python_interpreter_tool
title: aixplain.modules.agent.tool.python_interpreter_tool
---

Python interpreter tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute Python code
using an interpreter in a controlled environment.

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

### PythonInterpreterTool Objects

```python
class PythonInterpreterTool(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/python_interpreter_tool.py#L34)

A tool that provides a Python shell for executing Python commands.

This tool allows direct execution of Python code within the aiXplain platform.
It acts as an interface to a Python interpreter, enabling dynamic code execution
and computation.

**Attributes**:

- `name` _Text_ - Always set to &quot;Python Interpreter&quot;.
- `description` _Text_ - Description of the tool&#x27;s functionality.
- `status` _AssetStatus_ - The current status of the tool (ONBOARDED or DRAFT).

#### \_\_init\_\_

```python
def __init__(**additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/python_interpreter_tool.py#L47)

Initialize a new PythonInterpreterTool instance.

This initializes a Python interpreter tool with a fixed name and description.
The tool is set to ONBOARDED status by default.

**Arguments**:

- `**additional_info` - Additional keyword arguments for tool configuration.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/python_interpreter_tool.py#L60)

Convert the tool instance to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the tool&#x27;s configuration with keys:
  - description: The tool&#x27;s description
  - type: Always &quot;utility&quot;
  - utility: Always &quot;custom_python_code&quot;

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/python_interpreter_tool.py#L75)

Validate the tool&#x27;s configuration.

This is a placeholder method as the Python interpreter tool has a fixed
configuration that doesn&#x27;t require validation.

#### \_\_repr\_\_

```python
def __repr__() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/python_interpreter_tool.py#L83)

Return a string representation of the tool.

**Returns**:

- `Text` - A string in the format &quot;PythonInterpreterTool()&quot;.

