"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

"""

import inspect
import logging
import textwrap
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .enums import Function
from .exceptions import ResourceError
from .resource import (
    BaseResource,
    BaseGetParams,
    BaseSearchParams,
    GetResourceMixin,
    SearchResourceMixin,
    Page,
    encode_resource_id,
    _flatten_asset_info,
)

logger = logging.getLogger(__name__)

AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"


def _callable_to_string(fn) -> str:
    """Convert a callable to its source string representation."""
    try:
        return textwrap.dedent(inspect.getsource(fn)).strip()
    except (OSError, IOError, TypeError):
        return f"{fn.__module__}.{fn.__qualname__}"


class InspectorTarget(str, Enum):
    """Target stages for inspector validation in the team agent pipeline."""

    INPUT = "input"
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class InspectorAction(str, Enum):
    """Actions an inspector can take when evaluating content."""

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"
    EDIT = "edit"


class InspectorOnExhaust(str, Enum):
    """Action to take when max retries are exhausted."""

    CONTINUE = "continue"
    ABORT = "abort"


class InspectorSeverity(str, Enum):
    """Severity level for inspector findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvaluatorType(str, Enum):
    """Type of evaluator or editor."""

    ASSET = "asset"
    FUNCTION = "function"


@dataclass
class InspectorActionConfig:
    """Inspector action configuration."""

    type: InspectorAction
    max_retries: Optional[int] = None
    on_exhaust: Optional[InspectorOnExhaust] = None

    def __post_init__(self) -> None:
        """Validate that max_retries and on_exhaust are only used with RERUN."""
        if self.type != InspectorAction.RERUN:
            if self.max_retries is not None:
                raise ValueError("max_retries is only valid when action type is 'rerun'")
            if self.on_exhaust is not None:
                raise ValueError("on_exhaust is only valid when action type is 'rerun'")
        if self.max_retries is not None and self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the action config to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.max_retries is not None:
            d["maxRetries"] = self.max_retries
        if self.on_exhaust is not None:
            d["onExhaust"] = self.on_exhaust.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InspectorActionConfig":
        """Create an InspectorActionConfig from a dictionary."""
        return cls(
            type=InspectorAction(data["type"]),
            max_retries=data.get("maxRetries"),
            on_exhaust=InspectorOnExhaust(data["onExhaust"]) if data.get("onExhaust") else None,
        )


@dataclass
class EvaluatorConfig:
    """Evaluator configuration for an inspector."""

    type: EvaluatorType
    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and convert callable functions to source strings."""
        if callable(self.function):
            self.function = _callable_to_string(self.function)
        if self.type == EvaluatorType.ASSET and not self.asset_id:
            raise ValueError("asset_id is required when evaluator type is 'asset'")
        if self.type == EvaluatorType.FUNCTION and not self.function:
            raise ValueError("function is required when evaluator type is 'function'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.asset_id is not None:
            d["assetId"] = self.asset_id
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.function is not None:
            d["function"] = self.function
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluatorConfig":
        """Create an EvaluatorConfig from a dictionary."""
        return cls(
            type=EvaluatorType(data["type"]),
            asset_id=data.get("assetId"),
            prompt=data.get("prompt"),
            function=data.get("function"),
        )


@dataclass
class EditorConfig:
    """Editor configuration for an inspector."""

    type: EvaluatorType
    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and convert callable functions to source strings."""
        if callable(self.function):
            self.function = _callable_to_string(self.function)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.asset_id is not None:
            d["assetId"] = self.asset_id
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.function is not None:
            d["function"] = self.function
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EditorConfig":
        """Create an EditorConfig from a dictionary."""
        return cls(
            type=EvaluatorType(data["type"]),
            asset_id=data.get("assetId"),
            prompt=data.get("prompt"),
            function=data.get("function"),
        )


# Default action/targets applied when a guard is fetched by its canonical
# marketplace path. Keyed by the guard's asset name so the SDK never has to
# hardcode a guard's asset id — a new guard ships purely as a marketplace entry
# and inherits the safe default below until/unless it gets a tuned entry here.
_DEFAULT_GUARD_CONFIG: Dict[str, Any] = {
    "targets": [InspectorTarget.INPUT.value],
    "action": {"type": InspectorAction.ABORT.value},
}

# Keys are the marketplace ``assetName`` (the middle segment of a guard's
# ``host/asset-name/instance`` path), verified against the onboarded AWS guards.
_GUARD_CONFIG_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "detect-prompt-attacks-guardrail": {
        "targets": [InspectorTarget.INPUT.value],
        "action": {"type": InspectorAction.ABORT.value},
    },
    "sensitive-information-guardrail": {
        "targets": [InspectorTarget.INPUT.value],
        "action": {"type": InspectorAction.EDIT.value},
    },
    "contextual-grounding-check-guardrail": {
        "targets": [InspectorTarget.OUTPUT.value],
        "action": {"type": InspectorAction.RERUN.value, "maxRetries": 2, "onExhaust": "abort"},
    },
}


def _guard_slugs(value: Optional[str]) -> List[str]:
    """Return every path segment of a guard path/id, lowercased.

    Marketplace guard paths are ``host/asset-name/instance`` (the ``instanceId``,
    e.g. ``"aws/sensitive-information-guardrail/aws"``) or ``host/asset-name``
    (the ``assetPath``). The guard's identity is the *asset-name* segment, not
    the trailing host — so we return all segments and let the registry match the
    asset name wherever it sits. A bare asset id has no ``"/"`` and yields a
    single non-matching slug, falling back to the safe default.
    """
    if not value:
        return []
    return [seg.lower() for seg in str(value).strip().strip("/").split("/") if seg]


def _resolve_guard_defaults(*candidates: Optional[str]) -> Dict[str, Any]:
    """Pick the tuned guard config matching the first known asset-name segment.

    Tries each candidate (asset name, path/id) in order and, within each, every
    path segment, preferring whichever matches a key in
    :data:`_GUARD_CONFIG_DEFAULTS`. This matters when a guard is retrieved by its
    bare asset id (which never matches the registry) but the payload also carries
    its canonical ``path`` — the path's asset-name segment still selects the
    tuned ``action``/``targets`` instead of the safe fallback. Falls back to the
    safe default when nothing matches.
    """
    for candidate in candidates:
        for slug in _guard_slugs(candidate):
            if slug in _GUARD_CONFIG_DEFAULTS:
                return _GUARD_CONFIG_DEFAULTS[slug]
    return _DEFAULT_GUARD_CONFIG


@dataclass(repr=False)
class Inspector(
    BaseResource,
    GetResourceMixin[BaseGetParams, "Inspector"],
    SearchResourceMixin[BaseSearchParams, "Inspector"],
):
    """Inspector v2 configuration object.

    An ``Inspector`` is the single type the ``aix.Agent(inspectors=[...])`` slot
    accepts — whether it is hand-built or retrieved from the marketplace via
    :meth:`get` / :meth:`search`. Prebuilt guards are ordinary marketplace assets
    under the ``guardrails`` :class:`~aixplain.v2.enums.Function`; retrieving one
    returns a fully-configured ``Inspector`` whose evaluator points at the guard
    model, so a fetched guard and a custom inspector are indistinguishable to the
    agent.

    Example::

        from aixplain import Aixplain

        aix = Aixplain(api_key="<KEY>")

        # Discover guards like any other asset
        aix.Inspector.search("guard")

        # Retrieve a prebuilt by human-readable path (IDs also accepted)
        guard = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")
        redactor = aix.Inspector.get("aws/sensitive-information-guardrail/aws")
        redactor.targets = ["output"]            # config as an inspectable attribute

        team = aix.Agent(name="team", agents=[...], inspectors=[guard, redactor])
    """

    # Guards are marketplace models under function=guardrails, so retrieval is
    # backed by the models endpoint and filtered to that function.
    RESOURCE_PATH = "v2/models"

    # ``name`` / ``description`` / ``id`` / ``path`` are inherited from BaseResource.
    action: Optional[InspectorActionConfig] = None
    evaluator: Optional[EvaluatorConfig] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[str] = field(default_factory=list)
    editor: Optional[EditorConfig] = None

    def __post_init__(self) -> None:
        """Validate inspector configuration after initialization."""
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        if self.action is None:
            raise ValueError("action is required")
        if self.evaluator is None:
            raise ValueError("evaluator is required")
        self.targets = [t for t in (self.targets or []) if t and str(t).strip()]
        if self.action.type == InspectorAction.EDIT and self.editor is None:
            raise ValueError("editor is required when action type is 'edit'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the inspector to a dictionary for API serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "targets": list(self.targets),
            "action": self.action.to_dict(),
            "evaluator": self.evaluator.to_dict(),
        }
        if self.description is not None:
            d["description"] = self.description
        if self.severity is not None:
            d["severity"] = self.severity.value
        if self.editor is not None:
            d["editor"] = self.editor.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Create an Inspector from an inspector-shaped dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Inspector data must be a dict")

        severity = data.get("severity")
        editor_data = data.get("editor")
        return cls(
            name=data["name"],
            description=data.get("description"),
            severity=InspectorSeverity(severity) if severity else None,
            targets=data.get("targets") or [],
            action=InspectorActionConfig.from_dict(data.get("action") or {}),
            evaluator=EvaluatorConfig.from_dict(data["evaluator"]),
            editor=EditorConfig.from_dict(editor_data) if editor_data else None,
        )

    # ------------------------------------------------------------------
    # Marketplace retrieval
    # ------------------------------------------------------------------
    @classmethod
    def from_guard_model(cls, payload: Dict[str, Any], requested_path: Optional[str] = None) -> "Inspector":
        """Adapt a ``guardrails`` marketplace model payload into a configured Inspector.

        The guard model becomes the inspector's evaluator (``asset`` type), and
        sensible default ``action`` / ``targets`` are applied based on the guard's
        canonical path slug (see :data:`_GUARD_CONFIG_DEFAULTS`). Unknown guards
        fall back to a safe ``abort`` on ``input`` default, so future guards need
        no SDK change.

        Args:
            payload: The guard-model dict returned by the marketplace.
            requested_path: The path/id the caller passed to :meth:`get`, used to
                resolve default config when the payload omits a path.

        Returns:
            A fully-configured Inspector ready to attach to an agent.
        """
        if not isinstance(payload, dict):
            raise ValueError("guard model payload must be a dict")

        payload = _flatten_asset_info(dict(payload))
        model_id = payload.get("id")
        asset_name = (payload.get("assetInfo") or {}).get("assetName")
        defaults = _resolve_guard_defaults(asset_name, requested_path, payload.get("path"))

        action = InspectorActionConfig.from_dict(defaults["action"])
        editor = None
        if action.type == InspectorAction.EDIT:
            # The guard model performs the edit/redaction itself.
            editor = EditorConfig(type=EvaluatorType.ASSET, asset_id=model_id)

        inspector = cls(
            id=model_id,
            name=payload.get("name") or "Guardrail",
            description=payload.get("description"),
            evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=model_id),
            action=action,
            targets=list(defaults["targets"]),
            editor=editor,
        )
        inspector.path = payload.get("path") or requested_path
        return inspector

    @classmethod
    def get(cls, id: Any, **kwargs: Any) -> "Inspector":
        """Retrieve a prebuilt guard by human-readable path (IDs also accepted).

        Args:
            id: The guard's marketplace path (e.g.
                ``"aws/sensitive-information-guardrail/aws"``) or its asset id.
            **kwargs: Additional request parameters (e.g. ``resource_path``)
                forwarded to the underlying client call.

        Returns:
            A fully-configured Inspector backed by the guard model.
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for resource operations")

        resource_path = kwargs.pop("resource_path", None) or getattr(cls, "RESOURCE_PATH", "")
        encoded_id = encode_resource_id(id)
        payload = context.client.get(f"{resource_path}/{encoded_id}", **kwargs)

        inspector = cls.from_guard_model(payload, requested_path=str(id))
        setattr(inspector, "context", context)
        inspector._update_saved_state()
        return inspector

    @classmethod
    def search(cls, query: Optional[str] = None, **kwargs: Any) -> Page["Inspector"]:
        """Search available guards, returning the standard paginated shape.

        Args:
            query: Optional free-text query (e.g. ``"guard"``).
            **kwargs: Additional pagination/search parameters.

        Returns:
            A ``Page`` of configured Inspectors.
        """
        if query is not None:
            kwargs["query"] = query
        return super().search(**kwargs)

    @classmethod
    def _populate_filters(cls, params: Dict[str, Any]) -> dict:
        """Pin the search to the ``guardrails`` function (guards are models).

        NOTE: the ``v2/models/paginate`` ``functions`` filter is currently a
        no-op on the backend — ``[{"id": <fn>}]`` returns zero results for every
        function (verified against ``text-generation`` too), so this search
        returns an empty page until the backend implements function filtering on
        that endpoint. Tracked as a backend bug; the get-by-path flow is
        unaffected. See ``Inspector.get``.
        """
        filters = super()._populate_filters(params)
        filters["functions"] = [{"id": Function.GUARDRAILS.value}]
        # The v2/models/paginate endpoint requires a sort array.
        filters.setdefault("sort", [{}])
        return filters

    @classmethod
    def _build_resources(cls, items: List[dict], context: Any) -> List["Inspector"]:
        """Adapt each guard-model item into a configured Inspector."""
        resources: List["Inspector"] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                inspector = cls.from_guard_model(item)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("Skipping guard during Inspector deserialization: %s", e)
                continue
            setattr(inspector, "context", context)
            inspector._update_saved_state()
            resources.append(inspector)
        return resources


__all__ = [
    "Inspector",
    "InspectorTarget",
    "InspectorAction",
    "InspectorOnExhaust",
    "InspectorSeverity",
    "InspectorActionConfig",
    "EvaluatorType",
    "EvaluatorConfig",
    "EditorConfig",
]
