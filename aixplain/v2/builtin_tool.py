"""Built-in agent toolkits (``file`` / ``python`` / ``bash``) as attachable tools.

See the README section on built-in toolkits for the worked example; the wire
contract itself is documented in the agent repo at
``docs/guides/builtin-toolkits-contract.md``.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from typing_extensions import Literal

from .mixins import ToolableMixin

#: The wire discriminator for every row this module emits.
BUILTIN_TYPE = "builtin"

#: The toolkits the worker exposes.
BuiltinToolkit = Literal["file", "python", "bash"]

#: Tool names available per toolkit. Frozen alongside the worker's wire contract.
TOOLKIT_TOOLS: Dict[str, FrozenSet[str]] = {
    "file": frozenset({"read_file", "list_directory", "glob", "grep", "write_file", "edit_file"}),
    "python": frozenset({"run_python"}),
    "bash": frozenset({"run_command"}),
}

#: Settings each toolkit accepts, in wire-key form.
TOOLKIT_SETTINGS: Dict[str, Tuple[str, ...]] = {
    "file": ("max_read_bytes", "max_results"),
    "python": ("timeout_s", "expose_files"),
    "bash": ("timeout_s", "max_output_bytes", "deny_patterns"),
}

#: Settings that take a list, so a non-list value is rejected rather than iterated.
_LIST_SETTINGS: Tuple[str, ...] = ("deny_patterns",)

#: Every settings key owned by any toolkit, derived once.
_ALL_SETTINGS: FrozenSet[str] = frozenset(name for names in TOOLKIT_SETTINGS.values() for name in names)

#: Per toolkit, the settings that belong to a *different* toolkit.
_FOREIGN_SETTINGS: Dict[str, FrozenSet[str]] = {
    toolkit: _ALL_SETTINGS - frozenset(names) for toolkit, names in TOOLKIT_SETTINGS.items()
}

#: Keys accepted from a persisted row into the typed fields.
_KNOWN_KEYS: Dict[str, FrozenSet[str]] = {
    toolkit: frozenset(names) | {"include"} for toolkit, names in TOOLKIT_SETTINGS.items()
}

#: Keys the worker owns; dropped in both directions so a fetched row cannot pin
#: a server-chosen sandbox path.
_SERVER_ONLY_KEYS: FrozenSet[str] = frozenset({"workspace_root"})

#: Asset-identity keys. A builtin toolkit is not a catalog asset, so a row that
#: somehow carries one must not replay it on save.
_IDENTITY_KEYS: FrozenSet[str] = frozenset({"id", "_id", "assetId", "asset_id"})

#: Wire keys that are structural rather than settings.
_STRUCTURAL_KEYS: FrozenSet[str] = frozenset({"type", "toolkit"})

#: Keys never carried into ``_extra``.
_NEVER_EXTRA: FrozenSet[str] = _STRUCTURAL_KEYS | _SERVER_ONLY_KEYS | _IDENTITY_KEYS


def _as_list(name: str, value: Any) -> List[Any]:
    """Snapshot a list-valued field, rejecting anything that is not a list.

    A bare string is the mistake worth catching: ``list("rm -rf")`` silently
    becomes six one-character entries, which for ``deny_patterns`` would block
    virtually every command the worker runs.
    """
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list of strings, got {type(value).__name__}: {value!r}.")
    return list(value)


@dataclass
class BuiltinTool(ToolableMixin):
    """A built-in worker toolkit (``file`` / ``python`` / ``bash``) attached to an agent.

    Every setting defaults to ``None`` meaning *not sent* — the worker then applies
    its own default. The SDK deliberately does not mirror those defaults, so the two
    cannot drift apart. An explicit value is always forwarded, including
    ``expose_files=False``.

    Attributes:
        toolkit: One of ``"file"``, ``"python"`` or ``"bash"``.
        include: Restrict the agent to these tool names. ``None`` exposes every
            tool in the toolkit; ``[]`` exposes none. See :data:`TOOLKIT_TOOLS`.
        max_read_bytes: ``file`` only. Cap on the bytes a single read returns.
        max_results: ``file`` only. Cap on the entries a ``glob``/``grep`` returns.
        timeout_s: ``python`` and ``bash``. Wall-clock limit for one execution.
        expose_files: ``python`` only. Whether the interpreter sees the workspace.
        max_output_bytes: ``bash`` only. Cap on captured stdout/stderr bytes.
        deny_patterns: ``bash`` only. Regexes a command must not match.

    Raises:
        ValueError: If ``toolkit`` is unknown, if ``include`` names a tool the
            toolkit does not have, if a list-valued field is not a list, or if a
            setting belonging to a different toolkit is set.

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
    timeout_s: Optional[float] = None
    # python
    expose_files: Optional[bool] = None
    # bash
    max_output_bytes: Optional[int] = None
    deny_patterns: Optional[List[str]] = None
    #: Keys seen on a fetched row that this SDK version does not model, replayed
    #: verbatim on save so a newer backend's row survives a get() -> save() cycle.
    #: Not a constructor argument: it must not become a way past validation.
    _extra: Dict[str, Any] = field(default_factory=dict, repr=False, init=False)

    @property
    def type(self) -> str:
        """The wire discriminator, always ``"builtin"``."""
        return BUILTIN_TYPE

    def __post_init__(self) -> None:
        """Validate the toolkit, the requested tool names and the settings."""
        # ``isinstance`` first: an unhashable toolkit (a list from a mangled
        # response, say) would make the membership test raise TypeError.
        if not isinstance(self.toolkit, str) or self.toolkit not in TOOLKIT_TOOLS:
            raise ValueError(f"Unknown toolkit {self.toolkit!r}. Allowed toolkits: {sorted(TOOLKIT_TOOLS)}.")

        if self.include is not None:
            # Snapshot before validating, so the caller's list cannot gain an
            # unvalidated name later by being mutated behind our back. ``[]`` is
            # a real value meaning "no tools from this toolkit", not an error.
            self.include = _as_list("include", self.include)
            unknown = [name for name in self.include if name not in TOOLKIT_TOOLS[self.toolkit]]
            if unknown:
                raise ValueError(
                    f"Unknown tool(s) {unknown} for the {self.toolkit!r} toolkit. "
                    f"Allowed: {sorted(TOOLKIT_TOOLS[self.toolkit])}."
                )

        misplaced = sorted(name for name in _FOREIGN_SETTINGS[self.toolkit] if getattr(self, name) is not None)
        if misplaced:
            raise ValueError(
                f"Setting(s) {misplaced} are not valid for the {self.toolkit!r} toolkit. "
                f"Allowed settings: {sorted(TOOLKIT_SETTINGS[self.toolkit])}."
            )

        for name in _LIST_SETTINGS:
            if getattr(self, name) is not None:
                setattr(self, name, _as_list(name, getattr(self, name)))

    def as_tool(self) -> dict:
        """Serialize as the ``{"type": "builtin", ...}`` row the agent payload carries.

        Only the settings that were actually set are emitted; an omitted key means
        "use the worker's default". The row never carries an ``id``, an ``assetId``
        or a ``workspace_root``, and shares no mutable value with this object.
        """
        # ``_extra`` first, then the structural keys and typed settings, so a
        # replayed key can never shadow a validated one.
        row: Dict[str, Any] = dict(self._extra)
        row["type"] = BUILTIN_TYPE
        row["toolkit"] = self.toolkit
        if self.include is not None:
            row["include"] = self.include
        for name in TOOLKIT_SETTINGS[self.toolkit]:
            value = getattr(self, name)
            if value is not None:
                row[name] = value
        # One deep copy covers every level, including a nested structure that
        # arrived in ``_extra`` from a newer backend.
        return copy.deepcopy(row)

    @classmethod
    def from_dict(cls, row: dict) -> "BuiltinTool":
        """Rebuild a :class:`BuiltinTool` from a persisted ``builtin`` row.

        Lenient by design so a row from a backend newer than this SDK still
        round-trips: any key this version does not model is kept aside and
        replayed by :meth:`as_tool`. Server-owned and asset-identity keys are
        dropped in both directions.

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

        # A non-string toolkit may be unhashable, so it cannot index the table
        # here; ``__post_init__`` rejects it as a ValueError.
        known = _KNOWN_KEYS.get(toolkit, frozenset()) if isinstance(toolkit, str) else frozenset()
        kwargs = {}
        extra = {}
        for key, value in row.items():
            if key in known:
                kwargs[key] = value
            elif key not in _NEVER_EXTRA:
                extra[key] = value

        tool = cls(toolkit=toolkit, **kwargs)
        tool._extra = copy.deepcopy(extra)
        return tool
