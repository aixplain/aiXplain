---
sidebar_label: pipeline_tool
title: aixplain.modules.agent.tool.pipeline_tool
---

Pipeline tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute AI pipelines
and chain multiple AI operations together.

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

### PipelineTool Objects

```python
class PipelineTool(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/pipeline_tool.py#L35)

A tool that wraps aiXplain pipelines to execute complex workflows based on user commands.

This class provides an interface for using aiXplain pipelines as tools, allowing them
to be integrated into agent workflows. It handles pipeline validation, status management,
and execution.

**Attributes**:

- `description` _Text_ - A description of what the pipeline tool does.
- `pipeline` _Union[Text, Pipeline]_ - The pipeline to execute, either as a Pipeline instance
  or a pipeline ID string.
- `status` _AssetStatus_ - The current status of the pipeline tool.
- `name` _Text_ - The name of the tool, defaults to pipeline name if not provided.

#### \_\_init\_\_

```python
def __init__(description: Text,
             pipeline: Union[Text, Pipeline],
             name: Optional[Text] = None,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/pipeline_tool.py#L50)

Initialize a new PipelineTool instance.

**Arguments**:

- `description` _Text_ - A description of what the pipeline tool does.
- `pipeline` _Union[Text, Pipeline]_ - The pipeline to execute, either as a Pipeline instance
  or a pipeline ID string.
- `name` _Optional[Text], optional_ - The name of the tool. If not provided, will use
  the pipeline&#x27;s name. Defaults to None.
- `**additional_info` - Additional keyword arguments for tool configuration.
  

**Raises**:

- `Exception` - If the specified pipeline doesn&#x27;t exist or is inaccessible.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/pipeline_tool.py#L78)

Convert the tool instance to a dictionary representation.

**Returns**:

- `dict` - A dictionary containing the tool&#x27;s configuration with keys:
  - assetId: The pipeline ID
  - name: The tool&#x27;s name
  - description: The tool&#x27;s description
  - type: Always &quot;pipeline&quot;
  - status: The tool&#x27;s status

#### \_\_repr\_\_

```python
def __repr__() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/pipeline_tool.py#L97)

Return a string representation of the tool.

**Returns**:

- `Text` - A string in the format &quot;PipelineTool(name=&lt;name&gt;, pipeline=&lt;pipeline&gt;)&quot;.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/pipeline_tool.py#L105)

Validate the pipeline tool&#x27;s configuration.

This method performs several checks:
1. Verifies the pipeline exists and is accessible
2. Sets the tool name to the pipeline name if not provided
3. Updates the tool status to match the pipeline status

**Raises**:

- `Exception` - If the pipeline doesn&#x27;t exist or is inaccessible.

