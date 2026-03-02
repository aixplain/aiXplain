from typing import List, Text, Union, Optional
from aixplain.utils.convert_datatype_utils import normalize_expected_output


class WorkflowTask:
    """A task definition for an AI agent to execute.

    This class represents a task that can be assigned to an agent, including its
    description, expected output, and any dependencies on other tasks.

    Attributes:
        name (Text): The unique identifier/name of the task.
        description (Text): Detailed description of what the task should accomplish.
        expected_output (Text): Description of the expected output format or content.
        dependencies (Optional[List[Union[Text, WorkflowTask]]]): List of tasks or task
            names that must be completed before this task. Defaults to None.
    """

    def __init__(
        self,
        name: Text,
        description: Text,
        expected_output: Text,
        dependencies: Optional[List[Union[Text, "WorkflowTask"]]] = [],
    ):
        """Initialize a new WorkflowTask instance.

        Args:
            name (Text): The unique identifier/name of the task.
            description (Text): Detailed description of what the task should accomplish.
            expected_output (Text): Description of the expected output format or content.
            dependencies (Optional[List[Union[Text, WorkflowTask]]], optional): List of
                tasks or task names that must be completed before this task.
                Defaults to None.
        """
        self.name = name
        self.description = description
        self.expected_output = expected_output
        self.dependencies = dependencies

    def to_dict(self) -> dict:
        """Convert the task to a dictionary representation.

        This method serializes the task data, converting any WorkflowTask dependencies
        to their name strings.

        Returns:
            dict: A dictionary containing the task data with keys:
                - name: The task name
                - description: The task description
                - expectedOutput: The expected output description
                - dependencies: List of dependency names or None
        """
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

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowTask":
        """Create an WorkflowTask instance from a dictionary representation.

        Args:
            data: Dictionary containing WorkflowTask parameters

        Returns:
            WorkflowTask instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            expected_output=data["expectedOutput"],
            dependencies=data.get("dependencies", None),
        )


# !this is a backward compatibility for the AgentTask class
# it will be removed in the future
class AgentTask(WorkflowTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dict(self):
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> "AgentTask":
        return super().from_dict(data)
