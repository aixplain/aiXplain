from typing import Any, Dict, List, Text, TYPE_CHECKING

if TYPE_CHECKING:
    from aixplain.modules.team_agent import TeamAgent


class EvolverResponseData:
    def __init__(
        self,
        evolved_agent: "TeamAgent",
        current_code: Text,
        evaluation_report: Text,
        comparison_report: Text,
        criteria: Text,
        archive: List[Text],
        current_output: Text = "",
    ) -> None:
        self.evolved_agent = evolved_agent
        self.current_code = current_code
        self.evaluation_report = evaluation_report
        self.comparison_report = comparison_report
        self.criteria = criteria
        self.archive = archive
        self.current_output = current_output

    @classmethod
    def from_dict(cls, data: Dict[str, Any], llm_id: Text, api_key: Text) -> "EvolverResponseData":
        from aixplain.factories.team_agent_factory.utils import build_team_agent_from_yaml

        yaml_code = data.get("current_code", "")
        evolved_team_agent = build_team_agent_from_yaml(yaml_code=yaml_code, llm_id=llm_id, api_key=api_key)
        return cls(
            evolved_agent=evolved_team_agent,
            current_code=yaml_code,
            evaluation_report=data.get("evaluation_report", ""),
            comparison_report=data.get("comparison_report", ""),
            criteria=data.get("criteria", ""),
            archive=data.get("archive", []),
            current_output=data.get("current_output", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolved_agent": self.evolved_agent,
            "current_code": self.current_code,
            "evaluation_report": self.evaluation_report,
            "comparison_report": self.comparison_report,
            "criteria": self.criteria,
            "archive": self.archive,
            "current_output": self.current_output,
        }

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{key} is not a valid attribute of {self.__class__.__name__}")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"evolved_agent='{self.evolved_agent}', "
            f"evaluation_report='{self.evaluation_report}', "
            f"comparison_report='{self.comparison_report}', "
            f"criteria='{self.criteria}', "
            f"archive='{self.archive}', "
        )
