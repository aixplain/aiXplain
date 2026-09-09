"""Built-in agent toolkits (``file`` / ``python`` / ``bash``) as attachable tools.

The agent worker ships a small set of **built-in toolkits** that need no onboarded
asset: a sandboxed filesystem (``file``), a Python interpreter (``python``) and a
shell (``bash``). They are attached declaratively, by describing the toolkit on the
agent rather than by referencing an asset id::

    from aixplain import Aixplain
    from aixplain.v2 import BuiltinTool

    aix = Aixplain()
    agent = aix.Agent(
        name="Workspace agent",
        instructions="Read the uploaded files and compute the summary statistics.",
        tools=[
            BuiltinTool(toolkit="file", include=["read_file", "glob", "grep"]),
            BuiltinTool(toolkit="python", timeout_s=30),
        ],
    )

:class:`BuiltinTool` is a plain value object: it has no ``id``, never talks to the
network, and is never saved on its own — it is configuration carried inside the
agent's ``tools`` payload.

Note:
    ``bash`` must be enabled per deployment. Attaching it where it is not enabled
    is rejected by the backend, not by the SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from typing_extensions import Literal

from .mixins import ToolableMixin

#: The toolkits the worker exposes.
BuiltinToolkit = Literal["file", "python", "bash"]

#: Tool names available per toolkit. Frozen alongside the worker's wire contract;
#: a name outside this table is a client-side :class:`ValueError`.
TOOLKIT_TOOLS: Dict[str, FrozenSet[str]] = {
    "file": frozenset({"read_file", "list_directory", "glob", "grep", "write_file", "edit_file"}),
    "python": frozenset({"run_python"}),
    "bash": frozenset({"run_command"}),
}

#: Settings each toolkit accepts, in wire-key form. A setting listed here is
#: emitted verbatim when set; a setting belonging to a different toolkit is a
#: client-side :class:`ValueError`.
TOOLKIT_SETTINGS: Dict[str, Tuple[str, ...]] = {
    "file": ("max_read_bytes", "max_results"),
    "python": ("timeout_s", "expose_files"),
    "bash": ("timeout_s", "max_output_bytes", "deny_patterns"),
}

#: Keys the worker owns. The SDK drops them on the way in and never sends them
#: back, so a fetched agent cannot pin a server-chosen sandbox path.
_SERVER_ONLY_KEYS: FrozenSet[str] = frozenset({"workspace_root"})

#: Wire keys that are structural rather than settings.
_STRUCTURAL_KEYS: FrozenSet[str] = frozenset({"type", "toolkit"})


@dataclass
class BuiltinTool(ToolableMixin):
    """A built-in worker toolkit (``file`` / ``python`` / ``bash``) attached to an agent.

    Every setting defaults to ``None`` meaning *not sent* — the worker then applies
    its own default. The SDK deliberately does not mirror those defaults, so the two
    cannot drift apart. An explicit value is always forwarded, including
    ``expose_files=False``.

    Attributes:
        toolkit: Which built-in toolkit to attach. One of ``"file"``, ``"python"``
            or ``"bash"``.
        include: Restrict the agent to these tool names. ``None`` (the default)
            exposes every tool in the toolkit. See :data:`TOOLKIT_TOOLS` for the
            names each toolkit accepts.
        max_read_bytes: ``file`` only. Cap on the bytes a single read returns.
        max_results: ``file`` only. Cap on the entries a ``glob``/``grep`` returns.
        timeout_s: ``python`` and ``bash``. Wall-clock limit for one execution.
        expose_files: ``python`` only. Whether the interpreter can see the agent's
            workspace files.
        max_output_bytes: ``bash`` only. Cap on the captured stdout/stderr bytes.
        deny_patterns: ``bash`` only. Regular expressions a command must not match.

    Raises:
        ValueError: If ``toolkit`` is unknown, if ``include`` names a tool the
            toolkit does not have, or if a setting belonging to a different toolkit
            is set.

    Example:
        >>> BuiltinTool(toolkit="file", include=["read_file", "grep"]).as_tool()
        {'type': 'builtin', 'toolkit': 'file', 'include': ['read_file', 'grep']}
    """

    toolkit: BuiltinToolkit
    include: Optional[List[str]] = None
    # file
    max_read_bytes: Optional[int] = None
    max_results: Optional[int] = None
    # python and bash
    timeout_s: Optional[int] = None
    # python
    expose_files: Optional[bool] = None
    # bash
    max_output_bytes: Optional[int] = None
    deny_patterns: Optional[List[str]] = None
    #: Keys seen on a fetched row that this SDK version does not model, replayed
    #: verbatim on save so a newer backend's row survives a get() -> save() cycle.
    _extra: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def type(self) -> str:
        """The wire discriminator, always ``"builtin"``.

        Read-only on purpose: it is what routes the row to the worker's built-in
        toolkit handling, so it is not a constructor argument.
        """
        return "builtin"

    def __post_init__(self) -> None:
        """Validate the toolkit, the requested tool names and the settings."""
        if self.toolkit not in TOOLKIT_TOOLS:
            raise ValueError(f"Unknown toolkit {self.toolkit!r}. Allowed toolkits: {sorted(TOOLKIT_TOOLS)}.")

        if self.include is not None:
            if not self.include:
                raise ValueError("include must name at least one tool, or be None to expose every tool in the toolkit.")
            unknown = [name for name in self.include if name not in TOOLKIT_TOOLS[self.toolkit]]
            if unknown:
                raise ValueError(
                    f"Unknown tool(s) {unknown} for the {self.toolkit!r} toolkit. "
                    f"Allowed: {sorted(TOOLKIT_TOOLS[self.toolkit])}."
                )

        allowed = set(TOOLKIT_SETTINGS[self.toolkit])
        misplaced = sorted(
            {
                name
                for names in TOOLKIT_SETTINGS.values()
                for name in names
                if name not in allowed and getattr(self, name) is not None
            }
        )
        if misplaced:
            raise ValueError(
                f"Setting(s) {misplaced} are not valid for the {self.toolkit!r} toolkit. "
                f"Allowed settings: {sorted(allowed)}."
            )

    def as_tool(self) -> dict:
        """Serialize as the ``{"type": "builtin", ...}`` row the agent payload carries.

        Only the settings that were actually set are emitted; an omitted key means
        "use the worker's default". The row never carries an ``id``, an ``assetId``
        or a ``workspace_root``.

        Returns:
            dict: The wire row for this toolkit.
        """
        row: Dict[str, Any] = {"type": "builtin", "toolkit": self.toolkit}
        row.update({key: value for key, value in self._extra.items() if key not in _SERVER_ONLY_KEYS})
        if self.include is not None:
            row["include"] = list(self.include)
        for name in TOOLKIT_SETTINGS[self.toolkit]:
            value = getattr(self, name)
            if value is not None:
                row[name] = list(value) if isinstance(value, list) else value
        return row

    @classmethod
    def from_api_dict(cls, row: dict) -> "BuiltinTool":
        """Rebuild a :class:`BuiltinTool` from a persisted ``builtin`` row.

        Lenient by design, so that a row from a backend newer than this SDK still
        round-trips: any key this version does not model is kept aside and replayed
        by :meth:`as_tool`. Server-owned keys are dropped in both directions.

        Args:
            row: A persisted tool row carrying ``type="builtin"``.

        Returns:
            BuiltinTool: The reconstructed toolkit attachment.

        Raises:
            ValueError: If the row names no toolkit, or names an unknown one.
        """
        toolkit = row.get("toolkit")
        if toolkit is None:
            raise ValueError(f"A builtin tool row must carry a 'toolkit'. Got: {row!r}.")

        known = set(TOOLKIT_SETTINGS.get(toolkit, ())) | {"include"}
        kwargs = {key: value for key, value in row.items() if key in known}
        extra = {
            key: value
            for key, value in row.items()
            if key not in known and key not in _STRUCTURAL_KEYS and key not in _SERVER_ONLY_KEYS
        }
        return cls(toolkit=toolkit, _extra=extra, **kwargs)
