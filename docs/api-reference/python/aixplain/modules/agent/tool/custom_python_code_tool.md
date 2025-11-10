---
sidebar_label: custom_python_code_tool
title: aixplain.modules.agent.tool.custom_python_code_tool
---

Custom Python code tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute custom Python code
in a controlled environment.

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

### CustomPythonCodeTool Objects

```python
class CustomPythonCodeTool(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/custom_python_code_tool.py#L35)

A tool for executing custom Python code in the aiXplain platform.

This tool allows users to define and execute custom Python functions or code snippets
as part of their workflow. It supports both direct code input and callable functions.

**Attributes**:

- `code` _Union[Text, Callable]_ - The Python code to execute, either as a string or callable.
- `id` _str_ - The identifier for the code interpreter model.
- `status` _AssetStatus_ - The current status of the tool (DRAFT or ONBOARDED).

#### \_\_init\_\_

```python
def __init__(code: Union[Text, Callable],
             description: Text = "",
             name: Optional[Text] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/custom_python_code_tool.py#L47)

Initialize a new CustomPythonCodeTool instance.

**Arguments**:

- `code` _Union[Text, Callable]_ - The Python code to execute, either as a string or callable function.
- `description` _Text, optional_ - Description of what the code does. Defaults to &quot;&quot;.
- `name` _Optional[Text], optional_ - Name of the tool. Defaults to None.
- `**additional_info` - Additional keyword arguments for tool configuration.
  

**Notes**:

  If description or name are not provided, they may be automatically extracted
  from the code&#x27;s docstring if available.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/custom_python_code_tool.py#L69)

Convert the tool instance to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the tool&#x27;s configuration with keys:
  - id: The tool&#x27;s identifier
  - name: The tool&#x27;s name
  - description: The tool&#x27;s description
  - type: Always &quot;utility&quot;
  - utility: Always &quot;custom_python_code&quot;
  - utilityCode: The Python code to execute

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/custom_python_code_tool.py#L90)

Validate the tool&#x27;s configuration and code.

This method performs several checks:
1. Parses and validates the Python code if it&#x27;s not an S3 URL
2. Extracts description and name from code&#x27;s docstring if not provided
3. Ensures all required fields (description, code, name) are non-empty
4. Verifies the tool status is either DRAFT or ONBOARDED

**Raises**:

- `AssertionError` - If any validation check fails, with a descriptive error message.

#### \_\_repr\_\_

```python
def __repr__() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/custom_python_code_tool.py#L127)

Return a string representation of the tool.

**Returns**:

- `Text` - A string in the format &quot;CustomPythonCodeTool(name=&lt;tool_name&gt;)&quot;.

