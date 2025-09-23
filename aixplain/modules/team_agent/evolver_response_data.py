from typing import Any, Dict, List, Text, TYPE_CHECKING

if TYPE_CHECKING:
    from aixplain.modules.team_agent import TeamAgent


class EvolverResponseData:
    """Container for team agent evolution response data.

    This class encapsulates all the data returned from a team agent evolution
    process, including the evolved agent, code, evaluation reports, and
    historical archive information.

    Attributes:
        evolved_agent (TeamAgent): The evolved team agent instance.
        current_code (str): The current YAML code representation of the agent.
        evaluation_report (str): Report containing evaluation results.
        comparison_report (str): Report comparing different agent versions.
        criteria (str): Criteria used for evolution evaluation.
        archive (List[str]): Historical archive of previous versions.
        current_output (str): Current output from the agent.

    """
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
        """Initialize the EvolverResponseData instance.

        Args:
            evolved_agent (TeamAgent): The evolved team agent instance.
            current_code (str): The current YAML code representation.
            evaluation_report (str): Report containing evaluation results.
            comparison_report (str): Report comparing different versions.
            criteria (str): Criteria used for evolution evaluation.
            archive (List[str]): Historical archive of previous versions.
            current_output (str, optional): Current output from the agent.
                Defaults to empty string.

        """
        self.evolved_agent = evolved_agent
        self.current_code = current_code
        self.evaluation_report = evaluation_report
        self.comparison_report = comparison_report
        self.criteria = criteria
        self.archive = archive
        self.current_output = current_output

    @classmethod
    def from_dict(cls, data: Dict[str, Any], llm_id: Text, api_key: Text) -> "EvolverResponseData":
        """Create an EvolverResponseData instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing the response data.
            llm_id (str): The LLM identifier for building the team agent.
            api_key (str): API key for accessing the LLM service.

        Returns:
            EvolverResponseData: A new instance created from the dictionary data.

        """
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
        """Convert the EvolverResponseData instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the instance data.

        """
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
        """Get an attribute value using dictionary-style access.

        Args:
            key (str): The attribute name to retrieve.

        Returns:
            Any: The value of the requested attribute, or None if not found.

        """
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an attribute value using dictionary-style access.

        Args:
            key (str): The attribute name to set.
            value (Any): The value to assign to the attribute.

        Raises:
            KeyError: If the key is not a valid attribute of the class.

        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{key} is not a valid attribute of {self.__class__.__name__}")

    def __repr__(self) -> str:
        """Return a string representation of the EvolverResponseData instance.

        Returns:
            str: A string representation showing key attributes of the instance.

        """
        return (
            f"{self.__class__.__name__}("
            f"evolved_agent='{self.evolved_agent}', "
            f"evaluation_report='{self.evaluation_report}', "
            f"comparison_report='{self.comparison_report}', "
            f"criteria='{self.criteria}', "
            f"archive='{self.archive}', "
        )
