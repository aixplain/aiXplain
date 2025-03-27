from dataclasses import dataclass
from typing import Any, Optional, Dict, Text
from aixplain.enums import ResponseStatus


@dataclass
class PipelineResponse:
    def __init__(
        self,
        status: ResponseStatus,
        error: Optional[Dict[str, Any]] = None,
        elapsed_time: Optional[float] = 0.0,
        data: Optional[Text] = None,
        url: Optional[Text] = "",
        **kwargs,
    ):
        self.status = status
        self.error = error
        self.elapsed_time = elapsed_time
        self.data = data
        self.additional_fields = kwargs
        self.url = url

    def __getattr__(self, key: str) -> Any:
        if self.additional_fields and key in self.additional_fields:
            return self.additional_fields[key]

        raise AttributeError()

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __repr__(self) -> str:
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
        return hasattr(self, key)
