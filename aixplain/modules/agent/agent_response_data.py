"""Agent response data.

This module contains the AgentResponseData class, which is used to encapsulate the
input, output, and execution details of an agent's response, including intermediate
steps and execution statistics.
"""

from typing import List, Dict, Any, Optional, Text


class AgentResponseData:
    """A container for agent execution response data.

    This class encapsulates the input, output, and execution details of an agent's
    response, including intermediate steps and execution statistics.

    Attributes:
        input (Optional[Any]): The input provided to the agent.
        output (Optional[Any]): The final output from the agent.
        session_id (str): Identifier for the conversation session.
        intermediate_steps (List[Any]): List of steps taken during execution.
        steps (List[Any]): Reformatted list of steps with detailed execution info.
        execution_stats (Optional[Dict[str, Any]]): Statistics about the execution.
        critiques (str): Any critiques or feedback about the execution.
    """

    def __init__(
        self,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        session_id: str = "",
        intermediate_steps: Optional[List[Any]] = None,
        steps: Optional[List[Any]] = None,
        execution_stats: Optional[Dict[str, Any]] = None,
        critiques: Optional[str] = None,
    ):
        """Initialize a new AgentResponseData instance.

        Args:
            input (Optional[Any], optional): The input provided to the agent.
                Defaults to None.
            output (Optional[Any], optional): The final output from the agent.
                Defaults to None.
            session_id (str, optional): Identifier for the conversation session.
                Defaults to "".
            intermediate_steps (Optional[List[Any]], optional): List of steps taken
                during execution. Defaults to None.
            steps (Optional[List[Any]], optional): Reformatted list of steps with
                detailed execution info. Defaults to None.
            execution_stats (Optional[Dict[str, Any]], optional): Statistics about
                the execution. Defaults to None.
            critiques (Optional[str], optional): Any critiques or feedback about
                the execution. Defaults to None.
        """
        self.input = input
        self.output = output
        self.session_id = session_id
        self.intermediate_steps = intermediate_steps or []
        self.steps = steps or []
        self.execution_stats = execution_stats
        self.critiques = critiques or ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData":
        """Create an AgentResponseData instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing response data with keys:
                - input: The input provided to the agent
                - output: The final output from the agent
                - session_id: Identifier for the conversation session
                - intermediate_steps: List of steps taken during execution
                - steps: Reformatted list of steps with detailed execution info
                - executionStats: Statistics about the execution
                - critiques: Any critiques or feedback

        Returns:
            AgentResponseData: A new instance populated with the dictionary data.
        """
        return cls(
            input=data.get("input"),
            output=data.get("output"),
            session_id=data.get("session_id", ""),
            intermediate_steps=data.get("intermediate_steps", []),
            steps=data.get("steps", []),
            execution_stats=data.get("executionStats"),
            critiques=data.get("critiques", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response data to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing all response data with keys:
                - input: The input provided to the agent
                - output: The final output from the agent
                - session_id: Identifier for the conversation session
                - intermediate_steps: List of steps taken during execution
                - steps: Reformatted list of steps with detailed execution info
                - executionStats: Statistics about the execution
                - execution_stats: Alias for executionStats
                - critiques: Any critiques or feedback
        """
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "steps": self.steps,
            "executionStats": self.execution_stats,
            "execution_stats": self.execution_stats,
            "critiques": self.critiques,
        }

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get an attribute value using attribute-style access.

        Args:
            key (str): The name of the attribute to get.
            default (Optional[Any], optional): The value to return if the attribute
                is not found. Defaults to None.

        Returns:
            Any: The value of the attribute, or the default value if not found.
        """
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Get an attribute value using dictionary-style access.

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value of the attribute, or None if not found.
        """
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an attribute value using dictionary-style access.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to assign to the attribute.

        Raises:
            KeyError: If the key is not a valid attribute of the class.
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{key} is not a valid attribute of {self.__class__.__name__}")

    def __repr__(self) -> str:
        """Return a string representation of the response data.

        Returns:
            str: A string showing all attributes and their values in a readable format.
        """
        return (
            f"{self.__class__.__name__}("
            f"input={self.input}, "
            f"output={self.output}, "
            f"session_id='{self.session_id}', "
            f"intermediate_steps={self.intermediate_steps}, "
            f"steps={self.steps}, "
            f"execution_stats={self.execution_stats}, "
            f"critiques='{self.critiques}')"
        )

    def __contains__(self, key: Text) -> bool:
        """Check if an attribute exists using 'in' operator.

        Args:
            key (Text): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists and is accessible, False otherwise.
        """
        try:
            self[key]
            return True
        except KeyError:
            return False
