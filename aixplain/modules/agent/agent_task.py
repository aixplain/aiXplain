from typing import List, Text, Union


class AgentTask:
    def __init__(
        self,
        name: Text,
        description: Text,
        expected_output: Text,
        dependencies: List[Union[Text, "AgentTask"]] = [],
    ):
        self.name = name
        self.description = description
        self.expected_output = expected_output
        self.dependencies = dependencies

    def to_dict(self):
        agent_task_dict = {
            "name": self.name,
            "description": self.description,
            "expectedOutput": self.expected_output,
            "dependencies": self.dependencies,
        }

        for i, dependency in enumerate(agent_task_dict.get("dependencies") or []):
            if isinstance(dependency, AgentTask):
                agent_task_dict["dependencies"][i] = dependency.name
        return agent_task_dict
