from typing import List, Dict, Any, Optional, Text


class AgentResponseData:
    def __init__(
        self,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        session_id: str = "",
        intermediate_steps: Optional[List[Any]] = None,
        execution_stats: Optional[Dict[str, Any]] = None,
        critiques: Optional[str] = None,
    ):
        self.input = input
        self.output = output
        self.session_id = session_id
        self.intermediate_steps = intermediate_steps or []
        self.execution_stats = execution_stats
        self.critiques = critiques or ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData":
        return cls(
            input=data.get("input"),
            output=data.get("output"),
            session_id=data.get("session_id", ""),
            intermediate_steps=data.get("intermediate_steps", []),
            execution_stats=data.get("executionStats"),
            critiques=data.get("critiques", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "executionStats": self.execution_stats,
            "execution_stats": self.execution_stats,
            "critiques": self.critiques,
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
            f"execution_stats={self.execution_stats}, "
            f"critiques='{self.critiques}')"
        )

    def __contains__(self, key: Text) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False
