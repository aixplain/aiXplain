"""Agent response data.

This module contains the AgentResponseData class, which is used to encapsulate the
input, output, and execution details of an agent's response, including intermediate
steps and execution statistics.
"""

import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Text


@dataclass
class Artifact:
    """A user-facing deliverable produced during an agent run.

    v1 mirror of :class:`aixplain.v2.agent.Artifact` — same field names, same
    semantics. Artifacts come from two sources:

    - ``source="tool_output"`` — media a tool generated (image/audio/video/page).
      Carries a ``url``, usually a **presigned** URL.
    - ``source="workspace"`` — a file the agent wrote into its workspace.
      Carries inline UTF-8 text in ``content`` (binary workspace files are
      skipped by the engine; there is no uploader yet).

    Exactly one of ``url`` / ``content`` is populated.

    Warning:
        ``url_expires_at`` is when the **presigned URL** dies, not the artifact.
        Observed in the wild: a 24h window on a generated image URL. If you
        persist artifact URLs (database, cache, sent email), re-host the bytes
        before ``url_expires_at`` or the links will rot.

    ``category`` and ``source`` are plain strings, not enums: the engine may add
    new media categories before this SDK knows about them, and an unknown value
    must pass through rather than raise.

    Attributes:
        id (str): Unique identifier of the artifact.
        name (str): URL basename, or workspace-relative path (``outputs/report.csv``).
        title (Optional[str]): Human-friendly title, when the engine set one.
        mime_type (Optional[str]): MIME type of the artifact content.
        category (str): ``image`` / ``audio`` / ``video`` / ``page`` / ``document``
            / ``code`` / ``data`` / ``archive`` / ``other``, or any newer value
            the engine introduces.
        source (str): ``tool_output`` or ``workspace``.
        tool_name (Optional[str]): Tool that produced it (``tool_output`` only).
        url (Optional[str]): Presigned URL (``tool_output`` only).
        url_expires_at (Optional[str]): ISO-8601 expiry of ``url``.
        content (Optional[str]): Inline UTF-8 text (``workspace`` only).
        sha256 (Optional[str]): Content digest (``workspace`` only).
        byte_size (Optional[int]): Content size in bytes (``workspace`` only).
        mentioned_in_answer (bool): Whether the final answer cited the artifact.
        created_at (str): ISO-8601 creation timestamp.
    """

    id: str = ""
    name: str = ""
    title: Optional[str] = None
    mime_type: Optional[str] = None
    category: str = "other"
    source: str = ""
    tool_name: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[str] = None
    content: Optional[str] = None
    sha256: Optional[str] = None
    byte_size: Optional[int] = None
    mentioned_in_answer: bool = False
    created_at: str = ""

    # Webhook payloads are camelCased by the engine; poll payloads are snake_case
    # (which already matches the attribute names and binds directly).
    _ALIASES = {
        "mimeType": "mime_type",
        "toolName": "tool_name",
        "urlExpiresAt": "url_expires_at",
        "byteSize": "byte_size",
        "mentionedInAnswer": "mentioned_in_answer",
        "createdAt": "created_at",
    }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        """Create an Artifact from a snake_case or camelCase payload.

        Unknown keys are ignored, and missing keys fall back to the field
        defaults. If a payload carries both spellings of a field, the one
        appearing last wins (matching the v2 decoder).

        Args:
            data (Dict[str, Any]): The artifact payload.

        Returns:
            Artifact: A new instance populated with the payload data.
        """
        names = {f.name for f in dataclasses.fields(cls)}
        kwargs = {}
        for key, value in (data or {}).items():
            attr = cls._ALIASES.get(key, key)
            if attr in names:
                kwargs[attr] = value
        return cls(**kwargs)

    @classmethod
    def from_list(cls, value: Any) -> List["Artifact"]:
        """Decode an ``artifacts`` payload without ever raising.

        Args:
            value (Any): The raw ``artifacts`` value. Anything that is not a
                list (including ``None``) yields an empty list.

        Returns:
            List[Artifact]: The decodable entries; junk entries are dropped.
        """
        if not isinstance(value, list):
            return []
        artifacts: List["Artifact"] = []
        for item in value:
            if isinstance(item, cls):
                artifacts.append(item)
            elif isinstance(item, dict):
                try:
                    artifacts.append(cls.from_dict(item))
                except Exception:  # pragma: no cover - defensive; engine shape drift
                    continue
        return artifacts

    def to_dict(self) -> Dict[str, Any]:
        """Convert the artifact to its camelCase wire representation.

        Returns:
            Dict[str, Any]: The artifact as a dictionary, matching the keys the
                v2 SDK emits.
        """
        reverse = {attr: key for key, attr in self._ALIASES.items()}
        return {reverse.get(f.name, f.name): getattr(self, f.name) for f in dataclasses.fields(self)}

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get an attribute value, dict-style, with a default.

        Args:
            key (str): The name of the attribute to get.
            default (Optional[Any], optional): The value to return if the
                attribute is not found. Defaults to None.

        Returns:
            Any: The value of the attribute, or the default value if not found.
        """
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Get an attribute value using dictionary-style access.

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value of the attribute, or None if not found.
        """
        return getattr(self, key, None)


class AgentResponseData:
    """A container for agent execution response data.

    This class encapsulates the input, output, and execution details of an agent's
    response, including intermediate steps and execution statistics.

    Attributes:
        input (Optional[Any]): The input provided to the agent.
        output (Optional[Any]): The final output from the agent.
        session_id (str): Identifier for the conversation session.
        intermediate_steps (List[Any]): List of steps taken during execution.
        steps (List[Any]): Reformatted list of steps with detailed execution info.
        execution_stats (Optional[Dict[str, Any]]): Statistics about the execution.
        critiques (str): Any critiques or feedback about the execution.
        artifacts (List[Artifact]): Deliverables produced during the run. Always a
            list, empty when the run produced none or the backend predates
            artifact support.
    """

    def __init__(
        self,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        session_id: str = "",
        intermediate_steps: Optional[List[Any]] = None,
        steps: Optional[List[Any]] = None,
        execution_stats: Optional[Dict[str, Any]] = None,
        critiques: Optional[str] = None,
        artifacts: Optional[List[Any]] = None,
    ):
        """Initialize a new AgentResponseData instance.

        Args:
            input (Optional[Any], optional): The input provided to the agent.
                Defaults to None.
            output (Optional[Any], optional): The final output from the agent.
                Defaults to None.
            session_id (str, optional): Identifier for the conversation session.
                Defaults to "".
            intermediate_steps (Optional[List[Any]], optional): List of steps taken
                during execution. Defaults to None.
            steps (Optional[List[Any]], optional): Reformatted list of steps with
                detailed execution info. Defaults to None.
            execution_stats (Optional[Dict[str, Any]], optional): Statistics about
                the execution. Defaults to None.
            critiques (Optional[str], optional): Any critiques or feedback about
                the execution. Defaults to None.
            artifacts (Optional[List[Any]], optional): Deliverables produced during
                the run, as raw payload dictionaries or :class:`Artifact`
                instances. Anything undecodable is dropped. Defaults to None,
                which yields an empty list.
        """
        self.input = input
        self.output = output
        self.session_id = session_id
        self.intermediate_steps = intermediate_steps or []
        self.steps = steps or []
        self.execution_stats = execution_stats
        self.critiques = critiques or ""
        self.artifacts = Artifact.from_list(artifacts)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponseData":
        """Create an AgentResponseData instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing response data with keys:
                - input: The input provided to the agent
                - output: The final output from the agent
                - session_id: Identifier for the conversation session
                - intermediate_steps: List of steps taken during execution
                - steps: Reformatted list of steps with detailed execution info
                - executionStats: Statistics about the execution
                - critiques: Any critiques or feedback
                - artifacts: Deliverables produced during the run

        Returns:
            AgentResponseData: A new instance populated with the dictionary data.
        """
        return cls(
            input=data.get("input"),
            output=data.get("output"),
            session_id=data.get("session_id", ""),
            intermediate_steps=data.get("intermediate_steps", []),
            steps=data.get("steps", []),
            execution_stats=data.get("executionStats"),
            critiques=data.get("critiques", ""),
            artifacts=data.get("artifacts"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response data to a dictionary representation.

        Returns:
            Dict[str, Any]: A dictionary containing all response data with keys:
                - input: The input provided to the agent
                - output: The final output from the agent
                - session_id: Identifier for the conversation session
                - intermediate_steps: List of steps taken during execution
                - steps: Reformatted list of steps with detailed execution info
                - executionStats: Statistics about the execution
                - execution_stats: Alias for executionStats
                - critiques: Any critiques or feedback
                - artifacts: Deliverables produced during the run
        """
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "steps": self.steps,
            "executionStats": self.execution_stats,
            "execution_stats": self.execution_stats,
            "critiques": self.critiques,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get an attribute value using attribute-style access.

        Args:
            key (str): The name of the attribute to get.
            default (Optional[Any], optional): The value to return if the attribute
                is not found. Defaults to None.

        Returns:
            Any: The value of the attribute, or the default value if not found.
        """
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Get an attribute value using dictionary-style access.

        Args:
            key (str): The name of the attribute to get.

        Returns:
            Any: The value of the attribute, or None if not found.
        """
        return getattr(self, key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an attribute value using dictionary-style access.

        Args:
            key (str): The name of the attribute to set.
            value (Any): The value to assign to the attribute.

        Raises:
            KeyError: If the key is not a valid attribute of the class.
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{key} is not a valid attribute of {self.__class__.__name__}")

    def __repr__(self) -> str:
        """Return a string representation of the response data.

        Returns:
            str: A string showing all attributes and their values in a readable format.
        """
        return (
            f"{self.__class__.__name__}("
            f"input={self.input}, "
            f"output={self.output}, "
            f"session_id='{self.session_id}', "
            f"intermediate_steps={self.intermediate_steps}, "
            f"steps={self.steps}, "
            f"execution_stats={self.execution_stats}, "
            f"critiques='{self.critiques}', "
            f"artifacts={self.artifacts})"
        )

    def __contains__(self, key: Text) -> bool:
        """Check if an attribute exists using 'in' operator.

        Args:
            key (Text): The name of the attribute to check.

        Returns:
            bool: True if the attribute exists and is accessible, False otherwise.
        """
        try:
            self[key]
            return True
        except KeyError:
            return False
