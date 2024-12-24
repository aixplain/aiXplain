from typing import List, Dict, Any, Optional

class AgentResponseData:
    def __init__(
        self,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        session_id: str = "",
        intermediate_steps: Optional[List[Any]] = None,
        run_time: float = 0.0,
        used_credits: float = 0.0,
        execution_stats: Optional[Dict[str, Any]] = None,
    ):
        self.input = input
        self.output = output
        self.session_id = session_id
        self.intermediate_steps = intermediate_steps or []
        self.run_time = run_time
        self.used_credits = used_credits
        self.execution_stats = execution_stats

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData":
        return cls(
            input=data.get("input"),
            output=data.get("output"),
            session_id=data.get("session_id", ""),
            intermediate_steps=data.get("intermediate_steps", []),
            run_time=data.get("runTime", 0.0),
            used_credits=data.get("usedCredits", 0.0),
            execution_stats=data.get("executionStats"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "runTime": self.run_time,
            "usedCredits": self.used_credits,
            "executionStats": self.execution_stats,
        }
    
    def __getitem__(self, key):
        return getattr(self, key, None)