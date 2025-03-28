from typing import Any, Optional, Text, Dict, List, Union
from aixplain.enums import ResponseStatus
from aixplain.modules.model.response import ModelResponse
from aixplain.modules.team_agent.evolver_response_data import EvolverResponseData


class EvolverResponse(ModelResponse):

    def __init__(
        self,
        status: ResponseStatus = ResponseStatus.FAILED,
        data: Optional[EvolverResponseData] = None,
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
        self.data = data or EvolverResponseData()

    def __getitem__(self, key: Text) -> Any:
        if key == "data":
            return self.data.to_dict()
        return super().__getitem__(key)

    def __setitem__(self, key: Text, value: Any) -> None:
        if key == "data" and isinstance(value, Dict):
            self.data = EvolverResponseData.from_dict(value)
        elif key == "data" and isinstance(value, EvolverResponseData):
            self.data = value
        else:
            super().__setitem__(key, value)

    def to_dict(self) -> Dict[Text, Any]:
        base_dict = super().to_dict()
        base_dict["data"] = self.data.to_dict()
        return base_dict

    def __repr__(self) -> str:
        fields = super().__repr__()[len("ModelResponse(") : -1]
        return f"EvolverResponse({fields})"