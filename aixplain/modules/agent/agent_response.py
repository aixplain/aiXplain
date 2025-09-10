from aixplain.enums import ResponseStatus
from typing import Any, Dict, Optional, Text, Union, List, TYPE_CHECKING
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.modules.model.response import ModelResponse

if TYPE_CHECKING:
    from aixplain.modules.team_agent.evolver_response_data import EvolverResponseData


class AgentResponse(ModelResponse):
    """A response object for agent execution results.

    This class extends ModelResponse to handle agent-specific response data,
    including intermediate steps and execution statistics. It provides dictionary-like
    access to response data and serialization capabilities.

    Attributes:
        status (ResponseStatus): The status of the agent execution.
        data (Optional[AgentResponseData]): Structured data from the agent execution.
        details (Optional[Union[Dict, List]]): Additional execution details.
        completed (bool): Whether the execution has completed.
        error_message (Text): Error message if execution failed.
        used_credits (float): Number of credits used for execution.
        run_time (float): Total execution time in seconds.
        usage (Optional[Dict]): Resource usage information.
        url (Optional[Text]): URL for asynchronous result polling.
    """
    def __init__(
        self,
        status: ResponseStatus = ResponseStatus.FAILED,
        data: Optional[Union[AgentResponseData, "EvolverResponseData"]] = None,
        details: Optional[Union[Dict, List]] = {},
        completed: bool = False,
        error_message: Text = "",
        used_credits: float = 0.0,
        run_time: float = 0.0,
        usage: Optional[Dict] = None,
        url: Optional[Text] = None,
        **kwargs,
    ):
        """Initialize a new AgentResponse instance.

        Args:
            status (ResponseStatus, optional): The status of the agent execution.
                Defaults to ResponseStatus.FAILED.
            data (Optional[AgentResponseData], optional): Structured data from the
                agent execution. Defaults to None.
            details (Optional[Union[Dict, List]], optional): Additional execution
                details. Defaults to {}.
            completed (bool, optional): Whether the execution has completed.
                Defaults to False.
            error_message (Text, optional): Error message if execution failed.
                Defaults to "".
            used_credits (float, optional): Number of credits used for execution.
                Defaults to 0.0.
            run_time (float, optional): Total execution time in seconds.
                Defaults to 0.0.
            usage (Optional[Dict], optional): Resource usage information.
                Defaults to None.
            url (Optional[Text], optional): URL for asynchronous result polling.
                Defaults to None.
            **kwargs: Additional keyword arguments passed to ModelResponse.
        """

        super().__init__(
            status=status,
            data="",
            details=details,
            completed=completed,
            error_message=error_message,
            used_credits=used_credits,
            run_time=run_time,
            usage=usage,
            url=url,
            **kwargs,
        )
        self.data = data or AgentResponseData()

    def __getitem__(self, key: Text) -> Any:
        """Get a response attribute using dictionary-style access.

        Overrides the parent class's __getitem__ to handle AgentResponseData
        serialization when accessing the 'data' key.

        Args:
            key (Text): The name of the attribute to get.

        Returns:
            Any: The value of the attribute. For 'data' key, returns the
                serialized dictionary form.
        """
        if key == "data":
            return self.data.to_dict()
        return super().__getitem__(key)

    def __setitem__(self, key: Text, value: Any) -> None:
        """Set a response attribute using dictionary-style access.

        Overrides the parent class's __setitem__ to handle AgentResponseData
        deserialization when setting the 'data' key.

        Args:
            key (Text): The name of the attribute to set.
            value (Any): The value to assign. For 'data' key, can be either a
                dictionary or AgentResponseData instance.
        """
        if key == "data" and isinstance(value, Dict):
            self.data = AgentResponseData.from_dict(value)
        elif key == "data" and isinstance(value, AgentResponseData):
            self.data = value
        else:
            super().__setitem__(key, value)

    def to_dict(self) -> Dict[Text, Any]:
        """Convert the response to a dictionary representation.

        Overrides the parent class's to_dict to handle AgentResponseData
        serialization in the output dictionary.

        Returns:
            Dict[Text, Any]: A dictionary containing all response data, with the
                'data' field containing the serialized AgentResponseData.
        """
        base_dict = super().to_dict()
        base_dict["data"] = self.data.to_dict()
        return base_dict

    def __repr__(self) -> str:
        """Return a string representation of the response.

        Returns:
            str: A string showing all attributes and their values in a readable format,
                with the class name changed from ModelResponse to AgentResponse.
        """
        fields = super().__repr__()[len("ModelResponse(") : -1]
        return f"AgentResponse({fields})"
