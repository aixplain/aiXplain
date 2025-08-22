from typing import Text, Any, Optional, Dict, List, Union
from aixplain.enums import ResponseStatus
from aixplain.exceptions.types import ErrorCode


class ModelResponse:
    """ModelResponse class to store the response of the model run.
    
    This class provides a structured way to store and manage the response from model runs.
    It includes fields for status, data, details, completion status, error messages,
    usage information, and additional metadata.
    """

    def __init__(
        self,
        status: ResponseStatus,
        data: Text = "",
        details: Optional[Union[Dict, List]] = {},
        completed: bool = False,
        error_message: Text = "",
        used_credits: float = 0.0,
        run_time: float = 0.0,
        usage: Optional[Dict] = None,
        url: Optional[Text] = None,
        error_code: Optional[ErrorCode] = None,
        **kwargs,
    ):
        """Initialize a new ModelResponse instance.

        Args:
            status (ResponseStatus): The status of the response.
            data (Text): The data returned by the model.
            details (Optional[Union[Dict, List]]): Additional details about the response.
            completed (bool): Whether the response is complete.
            error_message (Text): The error message if the response is not successful.
            used_credits (float): The amount of credits used for the response.
            run_time (float): The time taken to generate the response.
            usage (Optional[Dict]): Usage information about the response.
            url (Optional[Text]): The URL of the response.
            error_code (Optional[ErrorCode]): The error code if the response is not successful.
            **kwargs: Additional keyword arguments.
        """
        self.status = status
        self.data = data
        self.details = details
        self.completed = completed
        if error_message == "":
            error_message = kwargs.get("error", "")
            if "supplierError" in kwargs:
                error_message = f"{error_message} - {kwargs.get('supplierError', '')}"
        self.error_message = error_message
        self.used_credits = used_credits
        self.run_time = run_time
        self.usage = usage
        self.url = url
        self.error_code = error_code
        self.additional_fields = kwargs

    def __getitem__(self, key: Text) -> Any:
        """Get an item from the ModelResponse.

        Args:
            key (Text): The key to get the value for.

        Returns:
            Any: The value associated with the key.

        Raises:
            KeyError: If the key is not found in the ModelResponse.
        """
        if key in self.__dict__:
            return self.__dict__[key]
        elif self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]
        elif key == "usedCredits":
            return self.used_credits
        elif key == "runTime":
            return self.run_time
        raise KeyError(f"Key '{key}' not found in ModelResponse.")

    def get(self, key: Text, default: Optional[Any] = None) -> Any:
        """Get an item from the ModelResponse with a default value.

        Args:
            key (Text): The key to get the value for.
            default (Optional[Any]): The default value to return if the key is not found.

        Returns:
            Any: The value associated with the key or the default value if the key is not found.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Text, value: Any) -> None:
        """Set an item in the ModelResponse.

        Args:
            key (Text): The key to set the value for.
            value (Any): The value to set.

        Raises:
            KeyError: If the key is not found in the ModelResponse.
        """
        if key in self.__dict__:
            self.__dict__[key] = value
        elif self.additional_fields and key in self.additional_fields:
            self.additional_fields[key] = value
        elif key == "usedCredits":
            self.used_credits = value
        elif key == "runTime":
            self.run_time = value
        else:
            raise KeyError(f"Key '{key}' not found in ModelResponse.")

    def __repr__(self) -> str:
        """Return a string representation of the ModelResponse.

        Returns:
            str: A string representation of the ModelResponse.
        """
        fields = []
        if self.status:
            fields.append(f"status={self.status}")
        if self.data:
            fields.append(f"data='{self.data}'")
        if self.details:
            fields.append(f"details={self.details}")
        if self.completed:
            fields.append(f"completed={self.completed}")
        if self.error_message:
            fields.append(f"error_message='{self.error_message}'")
        if self.used_credits:
            fields.append(f"used_credits={self.used_credits}")
        if self.run_time:
            fields.append(f"run_time={self.run_time}")
        if self.usage:
            fields.append(f"usage={self.usage}")
        if self.url:
            fields.append(f"url='{self.url}'")
        if self.error_code:
            fields.append(f"error_code='{self.error_code}'")
        if self.additional_fields:
            fields.extend([f"{k}={repr(v)}" for k, v in self.additional_fields.items()])
        return f"ModelResponse({', '.join(fields)})"

    def __contains__(self, key: Text) -> bool:
        """Check if a key is in the ModelResponse.

        Args:
            key (Text): The key to check for.

        Returns:
            bool: True if the key is in the ModelResponse, False otherwise.
        """
        try:
            self[key]
            return True
        except KeyError:
            return False

    def to_dict(self) -> Dict[Text, Any]:
        """Convert the ModelResponse to a dictionary.

        Returns:
            Dict[Text, Any]: A dictionary representation of the ModelResponse.
        """
        base_dict = {
            "status": self.status,
            "data": self.data,
            "details": self.details,
            "completed": self.completed,
            "error_message": self.error_message,
            "used_credits": self.used_credits,
            "run_time": self.run_time,
            "usage": self.usage,
            "url": self.url,
            "error_code": self.error_code,
        }
        if self.additional_fields:
            base_dict.update(self.additional_fields)
        return base_dict
