from typing import List, Optional, Text, Union


class WorkflowTask:
    def __init__(
        self,
        name: Text,
        description: Text,
        expected_output: Text,
        dependencies: Optional[List[Union[Text, "WorkflowTask"]]] = None,
    ):
        self.name = name
        self.description = description
        self.expected_output = expected_output
        self.dependencies = dependencies

    def to_dict(self):
        workflow_task_dict = {
            "name": self.name,
            "description": self.description,
            "expectedOutput": self.expected_output,
            "dependencies": self.dependencies,
        }

        if self.dependencies:
            for i, dependency in enumerate(workflow_task_dict["dependencies"]):
                if isinstance(dependency, WorkflowTask):
                    workflow_task_dict["dependencies"][i] = dependency.name
        return workflow_task_dict


# !this is a backward compatibility for the AgentTask class
# it will be removed in the future
class AgentTask(WorkflowTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dict(self):
        return super().to_dict()
