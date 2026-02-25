from dataclasses import dataclass
from typing import Any, Optional, Dict, Text
from aixplain.enums import ResponseStatus


@dataclass
class PipelineResponse:
    """A response object for pipeline operations.

    This class encapsulates the response from pipeline operations, including
    status, error information, timing data, and any additional fields.

    Attributes:
        status (ResponseStatus): The status of the pipeline operation.
        error (Optional[Dict[str, Any]]): Error details if operation failed.
        elapsed_time (Optional[float]): Time taken to complete the operation.
        data (Optional[Text]): The main response data.
        url (Optional[Text]): URL for polling or accessing results.
        additional_fields (Dict[str, Any]): Any extra fields provided.
    """

    def __init__(
        self,
        status: ResponseStatus,
        error: Optional[Dict[str, Any]] = None,
        elapsed_time: Optional[float] = 0.0,
        data: Optional[Text] = None,
        url: Optional[Text] = "",
        **kwargs,
    ):
        """Initialize a new PipelineResponse instance.

        Args:
            status (ResponseStatus): The status of the pipeline operation.
            error (Optional[Dict[str, Any]], optional): Error details if operation
                failed. Defaults to None.
            elapsed_time (Optional[float], optional): Time taken to complete the
                operation in seconds. Defaults to 0.0.
            data (Optional[Text], optional): The main response data.
                Defaults to None.
            url (Optional[Text], optional): URL for polling or accessing results.
                Defaults to "".
            **kwargs: Additional fields to store in the response.
        """
        self.status = status
        self.error = error
        self.elapsed_time = elapsed_time
        self.data = data
        self.additional_fields = kwargs
        self.url = url

    def __getattr__(self, key: str) -> Any:
        """Get an attribute from additional_fields if it exists.

        This method is called when an attribute lookup has not found the
        attribute in the usual places (i.e., it is not an instance attribute
        nor found through the __mro__ chain).

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value from additional_fields.

        Raises:
            AttributeError: If the key is not found in additional_fields.
        """
        if self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]

        raise AttributeError()

    def get(self, key: str, default: Any = None) -> Any:
        """Get an attribute value with a default if not found.

        Args:
            key (str): The name of the attribute to get.
            default (Any, optional): Value to return if key is not found.
                Defaults to None.

        Returns:
            Any: The attribute value or default if not found.
        """
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Get an attribute value using dictionary-style access.

        This method enables dictionary-style access to attributes
        (e.g., response["status"]).

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The attribute value.

        Raises:
            AttributeError: If the key is not found.
        """
        return getattr(self, key)

    def __repr__(self) -> str:
        """Return a string representation of the PipelineResponse.

        Returns:
            str: A string in the format "PipelineResponse(status=X, error=Y, ...)"
                containing all non-empty fields.
        """
        fields = []
        if self.status:
            fields.append(f"status={self.status}")
        if self.error:
            fields.append(f"error={self.error}")
        if self.elapsed_time is not None:
            fields.append(f"elapsed_time={self.elapsed_time}")
        if self.data:
            fields.append(f"data={self.data}")
        if self.additional_fields:
            fields.extend([f"{k}={repr(v)}" for k, v in self.additional_fields.items()])
        return f"PipelineResponse({', '.join(fields)})"

    def __contains__(self, key: str) -> bool:
        """Check if an attribute exists using 'in' operator.

        This method enables using the 'in' operator to check for attribute
        existence (e.g., "status" in response).

        Args:
            key (str): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists, False otherwise.
        """
        return hasattr(self, key)
