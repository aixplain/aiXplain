from dataclasses import dataclass
from typing import Text, Any, Optional, Dict, List, Union
from aixplain.enums import ModelStatus


@dataclass
class ModelResponse:
    """ModelResponse class to store the response of the model run."""

    def __init__(
        self,
        status: ModelStatus,
        data: Text = "",
        details: Optional[Union[Dict, List]] = {},
        completed: bool = False,
        error_message: Text = "",
        used_credits: float = 0.0,
        run_time: float = 0.0,
        usage: Optional[Dict] = None,
        url: Optional[Text] = None,
        **kwargs,
    ):
        self.status = status
        self.data = data
        self.details = details
        self.completed = completed
        self.error_message = error_message
        self.used_credits = used_credits
        self.run_time = run_time
        self.usage = usage
        self.url = url
        self.additional_fields = kwargs

    def __getitem__(self, key: Text) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]
        if self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]
        raise KeyError(f"Key '{key}' not found in ModelResponse.")
