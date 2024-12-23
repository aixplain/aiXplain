from aixplain.enums import ResponseStatus
from typing import Any, Dict, Optional, Text, Union

class AgentResponse:

    def __init__(
        self,
        status: ResponseStatus = ResponseStatus.FAILED,
        data: Dict={},
        input: Union[Text, Dict[str, Any]] = None,
        output: Any = None,
        url: Text = "",
        session_id: Text = "",
        run_time: float = 0.0,
        used_credits: float = 0.0,
        execution_stats: Optional[Dict[str, Any]] = None,
        error: Optional[Text] = None,
    ):

        self.status = status
        self.data=data
        self.input = self.validate_input(input)
        self.output = self.validate_output(output)
        self.url = url
        self.session_id = session_id
        self.run_time = run_time
        self.used_credits = used_credits
        self.execution_stats = execution_stats
        self.error=error

    @staticmethod
    def validate_input(value):
        if isinstance(value, list):
            return [str(row) if type(row) not in [dict, list, str, int, float, bool] else row for row in value]
        elif isinstance(value, dict):
            return {key: str(val) if type(val) not in [dict, list, str, int, float, bool] else val for key, val in value.items()}
        elif type(value) not in [dict, list, str, int, float, bool]:
            return str(value)
        return value

    @staticmethod
    def validate_output(value):
        if isinstance(value, list):
            return [str(row) if type(row) not in [dict, list, str, int, float, bool] else row for row in value]
        elif isinstance(value, dict):
            return {key: str(val) if type(val) not in [dict, list, str, int, float, bool] else val for key, val in value.items()}
        elif type(value) not in [dict, list, str, int, float, bool]:
            return str(value)
        return value

    def __getitem__(self, item):
        return getattr(self, item, None)

    def __setitem__(self, item, value):
        if hasattr(self, item):
            setattr(self, item, value)
        else:
            raise KeyError(f"Key '{item}' not found in AgentResponse.")

    def to_dict(self):
        return {
        "status": self.status,
        "input": self.input,
        "data": self.data,
        "output": self.output,
        "url":self.url,
        "session_id": self.session_id,
        "run_time": self.run_time,
        "used_credits": self.used_credits,
        "execution_stats": self.execution_stats,
        "error": self.error
        }