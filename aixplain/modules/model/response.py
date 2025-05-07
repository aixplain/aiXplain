from typing import Text, Any, Optional, Dict, List, Union
from aixplain.enums import ResponseStatus
from aixplain.exceptions.types import ErrorCode


class ModelResponse:
    """ModelResponse class to store the response of the model run."""

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
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: Text, value: Any) -> None:
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
        try:
            self[key]
            return True
        except KeyError:
            return False

    def to_dict(self) -> Dict[Text, Any]:
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
