from aixplain.enums import ResponseStatus
from typing import Any, Dict, Optional, Text, Union, List
from aixplain.modules.model.response import ModelResponse


class AgentResponseData:
    def __init__(
        self,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        session_id: str = "",
        intermediate_steps: Optional[List[Any]] = None,
        execution_stats: Optional[Dict[str, Any]] = None,
    ):
        self.input = input
        self.output = output
        self.session_id = session_id
        self.intermediate_steps = intermediate_steps or []
        self.execution_stats = execution_stats

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData":
        return cls(
            input=data.get("input"),
            output=data.get("output"),
            session_id=data.get("session_id", ""),
            intermediate_steps=data.get("intermediate_steps", []),
            execution_stats=data.get("executionStats"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "executionStats": self.execution_stats,
            "execution_stats": self.execution_stats,
        }

    def __getitem__(self, key):
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{key} is not a valid attribute of {self.__class__.__name__}")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"input={self.input}, "
            f"output={self.output}, "
            f"session_id='{self.session_id}', "
            f"intermediate_steps={self.intermediate_steps}, "
            f"execution_stats={self.execution_stats})"
        )

    def __contains__(self, key: Text) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False


class AgentResponse(ModelResponse):
    def __init__(
        self,
        status: ResponseStatus = ResponseStatus.FAILED,
        data: Optional[AgentResponseData] = None,
        details: Optional[Union[Dict, List]] = {},
        completed: bool = False,
        error_message: Text = "",
        used_credits: float = 0.0,
        run_time: float = 0.0,
        usage: Optional[Dict] = None,
        url: Optional[Text] = None,
        **kwargs,
    ):

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
        if key == "data":
            return self.data.to_dict()
        return super().__getitem__(key)

    def __setitem__(self, key: Text, value: Any) -> None:
        if key == "data" and isinstance(value, Dict):
            self.data = AgentResponseData.from_dict(value)
        elif key == "data" and isinstance(value, AgentResponseData):
            self.data = value
        else:
            super().__setitem__(key, value)

    def to_dict(self) -> Dict[Text, Any]:
        base_dict = super().to_dict()
        base_dict["data"] = self.data.to_dict()
        return base_dict

    def __repr__(self) -> str:
        fields = super().__repr__()[len("ModelResponse(") : -1]
        return f"AgentResponse({fields})"
