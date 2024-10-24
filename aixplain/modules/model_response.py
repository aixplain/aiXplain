from dataclasses import dataclass
from typing import Text, Any, Optional, Dict
from aixplain.enums import ModelStatus


@dataclass
class ModelResponse:
    """Class for keeping track of an item in inventory."""

    status: ModelStatus
    data: Text
    completed: bool
    error_message: Text
    elapsed_time: Optional[float]
    used_credits: Optional[float]
    run_time: Optional[float]
    supplierError: Optional[Text]
    additional_fields: Dict[str, Any] = None
    def __init__(
        self,
        status: ModelStatus,
        data: Text = "",
        completed: bool = False,
        error_message: Text = "",
        elapsed_time: Optional[float] = 0.0,
        used_credits: Optional[float] = 0.0,
        run_time: Optional[float] = 0.0,
        supplierError: Optional[Text] = "",
        **kwargs,
    ):
        self.status = status
        self.data = data
        self.completed = completed
        self.error_message = error_message
        self.elapsed_time = elapsed_time
        self.used_credits = used_credits
        self.run_time = run_time
        self.supplierError =  supplierError
        self.additional_fields = kwargs

    def __getitem__(self, key: Text) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]
        if self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]
        raise KeyError(f"Key '{key}' not found in ModelResponse.")
