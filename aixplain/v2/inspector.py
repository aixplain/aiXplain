"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

The public surface is intentionally tiny: construct an :class:`Inspector` with
plain strings for ``action`` / ``targets`` / ``severity`` and an ``aix.Metric``
(the universal judge) for ``metric``. No enums or config classes to import.

"""

import inspect
import logging
import textwrap
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

# Allowed string values (replacing the former user-facing enums). Kept as plain
# sets so callers pass strings like action="abort" / targets=["output"] and never
# import an enum.
_ACTION_TYPES = frozenset({"continue", "rerun", "abort", "edit"})
_ON_EXHAUST_VALUES = frozenset({"continue", "abort"})
_TARGET_VALUES = frozenset({"input", "steps", "output"})
_SEVERITY_VALUES = frozenset({"low", "medium", "high", "critical"})


def _callable_to_string(fn) -> str:
    """Convert a callable to its source string representation."""
    try:
        return textwrap.dedent(inspect.getsource(fn)).strip()
    except (OSError, IOError, TypeError):
        return f"{fn.__module__}.{fn.__qualname__}"


@dataclass
class _ActionConfig:
    """Internal, normalized action policy.

    Users never import or construct this — they pass ``action="abort"`` (a string)
    or ``action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}`` (a
    dict) and :meth:`coerce` builds this.
    """

    type: str
    max_retries: Optional[int] = None
    on_exhaust: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize/validate the action policy."""
        self.type = str(self.type).strip().lower()
        if self.type not in _ACTION_TYPES:
            raise ValueError(f"invalid action {self.type!r}; expected one of {sorted(_ACTION_TYPES)}")
        if self.on_exhaust is not None:
            self.on_exhaust = str(self.on_exhaust).strip().lower()
            if self.on_exhaust not in _ON_EXHAUST_VALUES:
                raise ValueError(
                    f"invalid on_exhaust {self.on_exhaust!r}; expected one of {sorted(_ON_EXHAUST_VALUES)}"
                )
        if self.type != "rerun":
            if self.max_retries is not None:
                raise ValueError("max_retries is only valid when action type is 'rerun'")
            if self.on_exhaust is not None:
                raise ValueError("on_exhaust is only valid when action type is 'rerun'")
        if self.max_retries is not None and self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    @classmethod
    def coerce(cls, value: Any) -> "_ActionConfig":
        """Build an action config from a string, dict, or existing config."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(type=value)
        if isinstance(value, dict):
            return cls(
                type=value.get("type"),
                max_retries=value.get("max_retries", value.get("maxRetries")),
                on_exhaust=value.get("on_exhaust", value.get("onExhaust")),
            )
        raise ValueError(f"action must be a string or dict, got {type(value)!r}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the action config to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type}
        if self.max_retries is not None:
            d["maxRetries"] = self.max_retries
        if self.on_exhaust is not None:
            d["onExhaust"] = self.on_exhaust
        return d


@dataclass
class _Judge:
    """Internal, normalized judge (evaluator or editor).

    Users never import or construct this — they pass a Metric, an asset-id string,
    or a Python callable and :meth:`coerce` builds this. It serializes to the same
    backend shape the platform has always accepted (``type`` = ``asset`` |
    ``function``).
    """

    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        """Convert callable functions to source and validate the judge has a target."""
        if callable(self.function):
            self.function = _callable_to_string(self.function)
        if not self.asset_id and not self.function:
            raise ValueError("a judge needs an asset id (or Metric) or a function")

    @property
    def type(self) -> str:
        """``"function"`` for callable judges, otherwise ``"asset"``."""
        return "function" if self.function else "asset"

    @classmethod
    def coerce(cls, value: Any, *, prompt: Optional[str] = None) -> Optional["_Judge"]:
        """Build a judge from a Metric, asset-id string, callable, dict, or judge.

        Accepts:
        - an ``aix.Metric`` (or any asset-backed object exposing ``id``) — the
          universal judge; its id and prompt flow into the evaluator payload;
        - a plain asset-id ``str``;
        - a Python ``callable`` (or its source) — a custom function judge;
        - a ``dict`` in either snake_case or the backend's camelCase.
        """
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.from_dict(value)
        if isinstance(value, str):
            return cls(asset_id=value, prompt=prompt)
        # A Metric (or any asset-backed judge) carries an ``id``.
        asset_id = getattr(value, "id", None)
        if asset_id:
            resolved_prompt = prompt
            if resolved_prompt is None:
                resolved_prompt = getattr(value, "prompt_template", None)
            if resolved_prompt is None:
                cfg = getattr(value, "config", None)
                if isinstance(cfg, dict):
                    resolved_prompt = cfg.get("prompt")
            return cls(asset_id=asset_id, prompt=resolved_prompt)
        if callable(value):
            return cls(function=_callable_to_string(value))
        if hasattr(value, "prompt_template"):
            # A Metric-like object that hasn't been onboarded yet has no id.
            raise ValueError("metric must be created before use as a judge — call Metric.create(...) so it has an id")
        raise ValueError(f"metric must be a Metric, asset-id string, or callable; got {type(value)!r}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type}
        if self.asset_id is not None:
            d["assetId"] = self.asset_id
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.function is not None:
            d["function"] = self.function
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "_Judge":
        """Create a judge from a backend (or user) dict."""
        return cls(
            asset_id=data.get("assetId", data.get("asset_id")),
            prompt=data.get("prompt"),
            function=data.get("function"),
        )


# Default action/targets applied when a guard is fetched by its canonical
# marketplace path. Keyed by the guard's asset name so the SDK never has to
# hardcode a guard's asset id — a new guard ships purely as a marketplace entry
# and inherits the safe default below until/unless it gets a tuned entry here.
_DEFAULT_GUARD_CONFIG: Dict[str, Any] = {
    "targets": ["input"],
    "action": {"type": "abort"},
}

# Keys are the marketplace ``assetName`` (the middle segment of a guard's
# ``host/asset-name/instance`` path), verified against the onboarded AWS guards.
# The underscore-named keys are legacy preset ids persisted by pre-redesign SDK
# builds (``{"presetId": ...}`` references, see :meth:`Inspector.from_dict`);
# they can never collide with path slugs, which are hyphenated.
_GUARD_CONFIG_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "detect-prompt-attacks-guardrail": {
        "targets": ["input"],
        "action": {"type": "abort"},
    },
    "sensitive-information-guardrail": {
        "targets": ["input"],
        "action": {"type": "edit"},
    },
    "contextual-grounding-check-guardrail": {
        "targets": ["output"],
        "action": {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"},
    },
    "prompt_injection_guard": {
        "targets": ["input"],
        "action": {"type": "abort"},
    },
    "pii_redaction": {
        "targets": ["input"],
        "action": {"type": "edit"},
    },
    "hallucination_guard": {
        "targets": ["output"],
        "action": {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"},
    },
}

# Guard asset ids that the legacy preset ids resolved to on the backend
# (pre-redesign ``PrebuiltInspector`` registry). Used to rebuild the judge when
# loading a persisted ``{"presetId": ...}`` reference.
_LEGACY_PRESET_ASSET_IDS: Dict[str, str] = {
    "prompt_injection_guard": "69a9974367d506543103ca18",
    "pii_redaction": "69cbf63cd74e334a6bacfeb1",
    "hallucination_guard": "69a9a38967d506543103ca1d",
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
    returns a fully-configured ``Inspector`` whose ``metric`` points at the guard
    model, so a fetched guard and a custom inspector are indistinguishable to the
    agent.

    Configuration is plain data — no enums or config classes to import:

    - ``action``: a string (``"continue" | "rerun" | "abort" | "edit"``) or, when
      you need retry parameters, a dict
      ``{"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}``.
    - ``targets``: a list of strings (``"input" | "steps" | "output"`` or a
      sub-agent name).
    - ``severity``: a string (``"low" | "medium" | "high" | "critical"``).
    - ``metric``: the universal judge — an ``aix.Metric``, an asset-id string, or
      a Python callable. Required. Note that a plain string is *always* treated
      as an asset id, never as a judge prompt. To pair a judge prompt with an
      asset, pass a dict ``{"asset_id": "<id>", "prompt": "<judge prompt>"}``
      (or a Metric whose ``prompt_template`` carries the prompt); to judge with
      custom logic, pass a Python callable.
    - ``editor``: required when ``action`` is ``"edit"``; same accepted types as
      ``metric``.

    Example::

        from aixplain import Aixplain

        aix = Aixplain(api_key="<KEY>")

        # A custom inspector judged by a Metric (the universal judge)
        inspector = aix.Inspector(
            name="grounded_output",
            severity="high",
            targets=["output"],
            action="abort",
            metric=aix.Metric.create(
                name="grounded",
                llm_path="<LLM_ID>",
                prompt_template="Abort if the answer is not grounded in the context.",
            ),
        )

        # Discover and retrieve prebuilt guards like any other asset
        aix.Inspector.search("guard")
        guard = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")
        redactor = aix.Inspector.get("aws/sensitive-information-guardrail/aws")
        redactor.targets = ["output"]            # config as an inspectable attribute

        team = aix.Agent(name="team", agents=[...], inspectors=[guard, inspector])
    """

    # Guards are marketplace models under function=guardrails, so retrieval is
    # backed by the models endpoint and filtered to that function.
    RESOURCE_PATH = "v2/models"

    # ``name`` / ``description`` / ``id`` / ``path`` are inherited from BaseResource.
    action: Any = None
    metric: Any = None
    severity: Optional[str] = None
    targets: List[str] = field(default_factory=list)
    editor: Any = None

    def __post_init__(self) -> None:
        """Normalize and validate inspector configuration after initialization."""
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        if self.action is None:
            raise ValueError("action is required")
        if self.metric is None:
            raise ValueError("metric is required")

        self.action = _ActionConfig.coerce(self.action)
        self.metric = _Judge.coerce(self.metric)
        self.editor = _Judge.coerce(self.editor)

        if self.severity is not None:
            self.severity = str(self.severity).strip().lower()
            if self.severity not in _SEVERITY_VALUES:
                raise ValueError(f"invalid severity {self.severity!r}; expected one of {sorted(_SEVERITY_VALUES)}")

        # Stage names ("input" / "steps" / "output") are case-insensitive and
        # normalized to lowercase; anything else is a sub-agent name and its
        # case is preserved.
        cleaned = [str(t).strip() for t in (self.targets or []) if t and str(t).strip()]
        self.targets = [t.lower() if t.lower() in _TARGET_VALUES else t for t in cleaned]

        if self.action.type == "edit" and self.editor is None:
            raise ValueError("editor is required when action type is 'edit'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the inspector to a dictionary for API serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "targets": list(self.targets),
            "action": self.action.to_dict(),
            # The judge serializes under the backend's long-standing "evaluator" key.
            "evaluator": self.metric.to_dict(),
        }
        if self.description is not None:
            d["description"] = self.description
        if self.severity is not None:
            d["severity"] = self.severity
        if self.editor is not None:
            d["editor"] = self.editor.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Create an Inspector from an inspector-shaped dictionary.

        Also accepts the legacy ``{"presetId": ...}`` preset references that
        pre-redesign SDK builds (e.g. 0.2.45rc1) persisted for prebuilt
        inspectors, so team agents saved by those builds still load.
        """
        if not isinstance(data, dict):
            raise ValueError("Inspector data must be a dict")

        if "presetId" in data and "evaluator" not in data:
            return cls._from_preset_dict(data)

        def _require(key: str) -> Any:
            if key not in data:
                raise ValueError(f"Inspector payload missing required key '{key}'; got keys: {sorted(data)}")
            return data[key]

        name = _require("name")
        evaluator = _require("evaluator")
        editor_data = data.get("editor")
        return cls(
            name=name,
            description=data.get("description"),
            severity=data.get("severity"),
            targets=data.get("targets") or [],
            action=data.get("action") or {},
            metric=_Judge.from_dict(evaluator),
            editor=_Judge.from_dict(editor_data) if editor_data else None,
        )

    @classmethod
    def _from_preset_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Compat: resolve a legacy ``{"presetId": ...}`` reference into an Inspector.

        The pre-redesign backend expanded these references itself; here the SDK
        rebuilds an equivalent Inspector so persisted team agents keep loading:
        the preset's known guard asset becomes the ``metric`` judge (mirroring
        :meth:`from_guard_model`), and the preset's tuned ``action`` / ``targets``
        defaults apply unless the payload overrides them. Unknown presets fall
        back to the safe abort-on-input default with the preset id as the judge
        asset reference.
        """
        preset_id = str(data["presetId"])
        defaults = _GUARD_CONFIG_DEFAULTS.get(preset_id, _DEFAULT_GUARD_CONFIG)
        asset_id = _LEGACY_PRESET_ASSET_IDS.get(preset_id, preset_id)

        action = _ActionConfig.coerce(data.get("action") or defaults["action"])
        editor = None
        if action.type == "edit":
            # As in from_guard_model: the guard model performs the edit itself.
            editor = _Judge(asset_id=asset_id)

        return cls(
            name=data.get("name") or preset_id,
            description=data.get("description"),
            severity=data.get("severity"),
            targets=data.get("targets") or list(defaults["targets"]),
            action=action,
            metric=_Judge(asset_id=asset_id),
            editor=editor,
        )

    # ------------------------------------------------------------------
    # Marketplace retrieval
    # ------------------------------------------------------------------
    @classmethod
    def from_guard_model(cls, payload: Dict[str, Any], requested_path: Optional[str] = None) -> "Inspector":
        """Adapt a ``guardrails`` marketplace model payload into a configured Inspector.

        The guard model becomes the inspector's ``metric`` (``asset`` judge), and
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

        action = _ActionConfig.coerce(defaults["action"])
        editor = None
        if action.type == "edit":
            # The guard model performs the edit/redaction itself.
            editor = _Judge(asset_id=model_id)

        inspector = cls(
            id=model_id,
            name=payload.get("name") or "Guardrail",
            description=payload.get("description"),
            metric=_Judge(asset_id=model_id),
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

        The ``v2/models/paginate`` ``functions`` filter expects a list of
        function-code strings (the backend matches with ``function: {$in: [...]}``
        and validates each element with ``@IsString({each: true})``). Sending the
        object shape ``[{"id": <fn>}]`` fails validation with
        ``each value in functions must be a string``.
        """
        filters = super()._populate_filters(params)
        filters["functions"] = [Function.GUARDRAILS.value]
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
]
