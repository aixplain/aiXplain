from typing import List, Optional, Text


class AgentTask:
    def __init__(
        self,
        name: Text,
        description: Text,
        expected_output: Optional[Text] = None,
        dependencies: Optional[List[Text]] = None,
    ):
        self.name = name
        self.description = description
        self.expected_output = expected_output
        self.dependencies = dependencies

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "expectedOutput": self.expected_output,
            "dependencies": self.dependencies,
        }
