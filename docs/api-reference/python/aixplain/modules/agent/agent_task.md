---
sidebar_label: agent_task
title: aixplain.modules.agent.agent_task
---

### AgentTask Objects

```python
class AgentTask()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_task.py#L4)

A task definition for an AI agent to execute.

This class represents a task that can be assigned to an agent, including its
description, expected output, and any dependencies on other tasks.

**Attributes**:

- `name` _Text_ - The unique identifier/name of the task.
- `description` _Text_ - Detailed description of what the task should accomplish.
- `expected_output` _Text_ - Description of the expected output format or content.
- `dependencies` _Optional[List[Union[Text, AgentTask]]]_ - List of tasks or task
  names that must be completed before this task. Defaults to None.

#### \_\_init\_\_

```python
def __init__(name: Text,
             description: Text,
             expected_output: Text,
             dependencies: Optional[List[Union[Text, "AgentTask"]]] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_task.py#L17)

Initialize a new AgentTask instance.

**Arguments**:

- `name` _Text_ - The unique identifier/name of the task.
- `description` _Text_ - Detailed description of what the task should accomplish.
- `expected_output` _Text_ - Description of the expected output format or content.
- `dependencies` _Optional[List[Union[Text, AgentTask]]], optional_ - List of
  tasks or task names that must be completed before this task.
  Defaults to None.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_task.py#L39)

Convert the task to a dictionary representation.

This method serializes the task data, converting any AgentTask dependencies
to their name strings.

**Returns**:

- `dict` - A dictionary containing the task data with keys:
  - name: The task name
  - description: The task description
  - expectedOutput: The expected output description
  - dependencies: List of dependency names or None

#### from\_dict

```python
@classmethod
def from_dict(cls, data: dict) -> "AgentTask"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/agent_task.py#L66)

Create an AgentTask instance from a dictionary representation.

**Arguments**:

- `data` - Dictionary containing AgentTask parameters
  

**Returns**:

  AgentTask instance

