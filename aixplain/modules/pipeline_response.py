from dataclasses import dataclass
from typing import Any, Optional, Dict, Text
from aixplain.enums import Status 

@dataclass
class PipelineResponse:
    status: Status  
    error: Optional[Dict[str, Any]] 
    elapsed_time: Optional[float]
    data: Optional[Dict[str, Any]] = None 
    additional_fields: Dict[str, Any] = None  
    def __init__(
        self,
        status: Status, 
        error: Optional[Dict[str, Any]] = None,
        elapsed_time: Optional[float] = 0.0,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,  
    ):
        self.status = status
        self.error = error
        self.elapsed_time = elapsed_time
        self.data = data 
        self.additional_fields = kwargs

    def __getitem__(self, key: str) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]

        if self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]

        raise KeyError(f"Key '{key}' not found in PipelineResponse.")
