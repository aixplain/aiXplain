"""Tool resource module for managing tools and their integrations."""

import re
import warnings
from typing import Union, List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json, config as dj_config
from dataclasses import dataclass, field
from functools import cached_property

from .resource import (
    Result,
    DeleteResourceMixin,
    BaseDeleteParams,
    DeleteResult,
)
from .model import Model, ModelRunParams
from .integration import Integration, ActionSpec, ActionMixin
from .actions import Actions


@dataclass_json
@dataclass(repr=False)
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass(repr=False)
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult], ActionMixin):
    """Resource for tools.

    This class represents a tool resource that matches the backend structure.
    Tools can be integrations, utilities, or other specialized resources.
    Inherits from Model to reuse shared attributes and functionality.
    """

    RESOURCE_PATH = "v2/tools"
    RESPONSE_CLASS = ToolResult
    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration

    # Tool-specific fields
    asset_id: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    integration_id: Optional[str] = field(default=None, metadata=dj_config(field_name="parentModelId"))
    subscriptions: Optional[Any] = field(default=None)
    integration: Optional[Union[Integration, str]] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    config: Optional[dict] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    code: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    allowed_actions: Optional[List[str]] = field(default_factory=list, metadata=dj_config(field_name="allowedActions"))
    redirect_url: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))

    @property
    def integration_path(self) -> Optional[str]:
        """The path of the integration (e.g. ``"aixplain/python-sandbox"``).

        Available when the ``integration`` has been resolved to an
        :class:`Integration` object that carries a ``path`` attribute.
        Returns ``None`` when the integration has not been resolved yet.
        """
        if isinstance(self.integration, Integration) and self.integration.path:
            return self.integration.path
        return None

    def __post_init__(self) -> None:
        """Initialize tool after dataclass creation."""
        if not self.id:
            if self.integration is None:
                code = self.code or (self.config.pop("code", None) if self.config else None)
                assert code is not None, "Code is required to create a (script) Tool"
                self.integration = self.DEFAULT_INTEGRATION_ID
                self.config = {
                    "code": code,
                }
            else:
                if isinstance(self.integration, str):
                    pass
                elif not isinstance(self.integration, Integration):
                    raise ValueError("Integration must be an Integration object or a string")

    # ------------------------------------------------------------------
    # Override ``actions`` so ActionMixin's multi-action behaviour is used
    # instead of Model's single-"run" property.
    # ------------------------------------------------------------------

    @cached_property
    def actions(self) -> Actions:
        """Collection of actions available on this tool."""
        return ActionMixin.actions.func(self)

    @property
    def inputs(self):
        """Tools have multiple actions — use tool.actions['action_name'].inputs instead."""
        raise AttributeError("Tools have multiple actions — use tool.actions['action_name'].inputs instead")

    @inputs.setter
    def inputs(self, value):
        """Prevent setting inputs directly on tools."""
        raise AttributeError("Tools have multiple actions — use tool.actions['action_name'].inputs instead")

    # ------------------------------------------------------------------
    # Action / Input listing (with integration fallback)
    # ------------------------------------------------------------------

    def _ensure_integration(self, required: bool = False) -> bool:
        """Ensure integration is resolved to an Integration instance."""
        if not self.integration:
            if required:
                raise ValueError("Integration is required")
            return False

        if isinstance(self.integration, str):
            try:
                self.integration = self.context.Integration.get(self.integration)
            except Exception as e:
                if required:
                    raise ValueError(f"Failed to resolve integration: {e}") from e
                return False

        if not isinstance(self.integration, Integration):
            if required:
                raise ValueError("Integration must be an Integration object or a string")
            return False

        return True

    def list_actions(self) -> List[ActionSpec]:
        """List available actions for the tool (with integration fallback)."""
        try:
            actions = super().list_actions()
            return actions
        except Exception as e:
            warnings.warn(f"Error listing actions: {e}. Using integration.list_actions() instead.")
            if self._ensure_integration():
                return self.integration.list_actions()

            return []

    def _list_inputs(self, *actions: str) -> List[ActionSpec]:
        """List available inputs for specified actions (with integration fallback)."""
        try:
            return super()._list_inputs(*actions)
        except Exception as e:
            warnings.warn(f"Error listing inputs: {e}. Using integration._list_inputs() instead.")
            if self._ensure_integration():
                try:
                    return self.integration._list_inputs(*actions)
                except Exception:
                    pass

            return []

    def list_inputs(self, *actions: str) -> List[ActionSpec]:
        """List available inputs for specified actions.

        .. deprecated::
            Use ``tool.actions['action_name'].inputs`` to discover and
            configure action inputs instead.
        """
        warnings.warn(
            "list_inputs() is deprecated. Use tool.actions['action_name'].inputs to "
            "discover and configure action inputs instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._list_inputs(*actions)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the tool by connecting to the integration."""
        self._ensure_integration(required=True)

        payload = {}

        if self.name:
            payload["name"] = self.name
        if self.description:
            payload["description"] = self.description

        if self.config:
            config_copy = dict(self.config)
            data = config_copy.pop("data", {})
            data.update(config_copy)
            payload["data"] = data

        connection = self.integration.connect(**payload)

        self.id = connection.id
        self.config = None
        self.code = None

        for attr_name in self.__dataclass_fields__:
            if not getattr(self, attr_name) and getattr(connection, attr_name, None):
                setattr(self, attr_name, getattr(connection, attr_name))

        if connection.redirect_url:
            self.redirect_url = connection.redirect_url

    def _resolve_integration(self) -> None:
        """Auto-resolve the integration from ``integration_id`` when not explicitly set.

        The backend populates ``parentModelId`` (exposed as ``integration_id``)
        on tools/connections with the ID of the integration that created them.
        Older tools may not have this field, in which case the caller must set
        ``tool.integration`` manually.

        Raises:
            ValueError: If integration cannot be resolved.
        """
        if self.integration:
            return

        if self.integration_id:
            self.integration = self.integration_id
            return

        raise ValueError(
            "Cannot update tool: the integration could not be resolved automatically "
            "(integration_id is not set — this may be an older tool). "
            "Set tool.integration = '<integration_id>' before calling save()."
        )

    _AUTH_SCHEME_RE = re.compile(r"Authentication scheme used for this connections?:\s*(\w+)")

    def _extract_auth_scheme(self) -> Optional[str]:
        """Extract the authentication scheme from the tool's description or attributes.

        The backend embeds ``Authentication scheme used for this connections: <SCHEME>``
        in the description text.  Falls back to the ``auth_schemes`` key in the
        ``attributes`` dict.  Returns ``None`` when neither source is available.
        """
        if self.description:
            m = self._AUTH_SCHEME_RE.search(self.description)
            if m:
                return m.group(1)
        if isinstance(self.attributes, dict):
            auth_schemes_val = self.attributes.get("auth_schemes")
            if auth_schemes_val:
                schemes = re.findall(r"\w+", str(auth_schemes_val))
                if "BEARER_TOKEN" in schemes:
                    return "BEARER_TOKEN"
                if schemes:
                    return schemes[0]
        return None

    def _update(self, resource_path: str, payload: dict) -> None:
        """Update tool metadata and optionally reconnect the integration.

        Metadata (name, description) is updated via ``PUT /sdk/utilities/{id}``.
        Connection-related fields (config, code) trigger a reconnect via
        ``integration.connect()`` with the existing ``assetId``.
        """
        needs_reconnect = bool(self.config or self.code)

        metadata_payload: dict = {"id": self.id}
        if self.name:
            metadata_payload["name"] = self.name
        if self.description:
            metadata_payload["description"] = self.description

        self.context.client.request("put", f"sdk/utilities/{self.id}", json=metadata_payload)

        if needs_reconnect:
            self._resolve_integration()
            self._ensure_integration(required=True)

            connect_payload: dict = {}
            data: dict = {}
            if self.config:
                config_copy = dict(self.config)
                nested_data = config_copy.pop("data", {})
                data.update(nested_data)
                data.update(config_copy)

            if self.code and "code" not in data:
                data["code"] = self.code

            data["assetId"] = self.asset_id or self.id
            connect_payload["data"] = data

            # The metadata PUT above already persists name/description.
            # Send an empty name so the backend's .trim() call succeeds
            # without triggering a "Name already exists" uniqueness check.
            connect_payload["name"] = ""

            auth_scheme = self._extract_auth_scheme()
            if auth_scheme:
                connect_payload["authScheme"] = auth_scheme

            connection = self.integration.connect(**connect_payload)

            self.id = connection.id
            self.config = None
            self.code = None

            for attr_name in self.__dataclass_fields__:
                if not getattr(self, attr_name) and getattr(connection, attr_name, None):
                    setattr(self, attr_name, getattr(connection, attr_name))

            if connection.redirect_url:
                self.redirect_url = connection.redirect_url

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def _is_utility_model_without_integration(self) -> bool:
        """Check if this is a utility model accessed via Tool.get() without real integration."""
        from .enums import Function

        if not (self.function_type == "ai" and self.function == Function.UTILITIES):
            return False
        if hasattr(self, "integration") and self.integration is not None:
            return False
        if not self.id:
            return False

        actions_available = getattr(self, "actions_available", None)
        if hasattr(actions_available, "__class__") and "Field" in str(type(actions_available)):
            actions_available = True

        return bool(actions_available)

    def validate_allowed_actions(self) -> None:
        """Validate that all allowed actions are available for this tool."""
        if self.allowed_actions:
            if not self._ensure_integration():
                return

            available_actions = [action.name for action in self.list_actions()]
            if not available_actions:
                return

            available_lower = [a.lower() for a in available_actions if a]
            assert all(action.lower() in available_lower for action in self.allowed_actions), (
                f"All allowed actions must be available. "
                f"Requested: {self.allowed_actions}, Available: {available_actions}"
            )

    def _get_effective_actions(self) -> List[str]:
        """Return the effective action scope for serialization and defaulting.

        Prefer explicitly scoped ``allowed_actions``. When none are set,
        auto-detect a single available action so serialization and runtime
        defaulting stay aligned for single-action tools.
        """
        if self.allowed_actions:
            return list(self.allowed_actions)

        try:
            action_names = list(self.actions)
        except Exception:
            action_names = []

        if len(action_names) == 1:
            return action_names

        return []

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def get_parameters(self) -> List[dict]:
        """Get parameters for the tool in the format expected by agent saving."""
        self.validate_allowed_actions()

        parameters = []
        effective_actions = self._get_effective_actions()
        action_specs = self._list_inputs(*effective_actions)

        for spec in action_specs:
            action_inputs = {}

            action_name = spec.name or spec.slug or ""
            action_obj = None
            if action_name:
                try:
                    action_obj = self.actions[action_name]
                except (ValueError, KeyError):
                    continue

            for input_param in spec.inputs:
                input_code = input_param.code or input_param.name.lower().replace(" ", "_")

                current_value = None
                if action_obj:
                    inp = action_obj.inputs.get(input_code)
                    current_value = inp.value if inp is not None else None

                if current_value is None and input_param.default_value:
                    current_value = input_param.default_value[0] if input_param.default_value else None

                action_inputs[input_code] = {
                    "name": input_param.name,
                    "value": current_value,
                    "required": input_param.required,
                    "datatype": input_param.datatype,
                    "allow_multi": input_param.allow_multi,
                    "supports_variables": input_param.supports_variables,
                    "fixed": input_param.fixed,
                    "description": input_param.description,
                }

            parameters.append(
                {
                    "code": spec.slug,
                    "name": action_name,
                    "description": spec.description or "",
                    "inputs": action_inputs,
                }
            )

        return parameters

    def as_tool(self) -> dict:
        """Serialize this tool for agent creation."""
        tool_dict = super().as_tool()
        actions_to_serialize = self._get_effective_actions()

        if actions_to_serialize:
            tool_dict["actions"] = actions_to_serialize

        return tool_dict

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_params(self, **kwargs: Any) -> List[str]:
        """Validate parameters for the tool (action-based validation)."""
        errors = []

        if self._is_utility_model_without_integration() and "data" in kwargs and isinstance(kwargs["data"], dict):
            model_kwargs = kwargs["data"]
            errors = super()._validate_params(**model_kwargs)
            return errors

        action = kwargs.get("action")
        if not action:
            errors.append("action is required")
            return errors

        try:
            self.validate_allowed_actions()
        except AssertionError as e:
            errors.append(str(e))
            return errors

        if self.allowed_actions and action not in self.allowed_actions:
            errors.append(f"Action '{action}' is not allowed for this tool. Allowed actions: {self.allowed_actions}")
            return errors

        try:
            action_obj = self.actions[action]
            data = kwargs.get("data", {})
            action_errors = action_obj.inputs.validate(data)
            errors.extend(action_errors)
        except Exception:
            pass

        return errors

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, *args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult:
        """Run the tool."""
        self._ensure_valid_state()

        if len(args) > 0:
            kwargs["data"] = args[0]
            args = args[1:]

        if "action" not in kwargs:
            if self.allowed_actions and len(self.allowed_actions) == 1:
                kwargs["action"] = self.allowed_actions[0]
            else:
                available_actions = list(self.actions)
                if available_actions and len(available_actions) == 1:
                    kwargs["action"] = available_actions[0]
                else:
                    raise ValueError("No action provided")

        if "action" not in kwargs:
            raise ValueError("No action provided")

        return super().run(*args, **kwargs)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Override to handle tool-specific parameter merging."""
        merged = {}
        action_name = kwargs.get("action")
        if not action_name and len(self.allowed_actions) == 1:
            action_name = self.allowed_actions[0]

        if not action_name:
            raise ValueError("No action provided")

        action_obj = self.actions[action_name]

        for input_code in action_obj.inputs.keys():
            inp = action_obj.inputs.get(input_code)
            if inp is not None and inp.value is not None:
                merged[input_code] = inp.value

        kwargs.setdefault("data", {})

        if isinstance(kwargs["data"], str):
            result = {
                "action": action_name,
                "data": kwargs["data"],
            }
            for key, value in kwargs.items():
                if key not in ["data", "action"]:
                    result[key] = value
            return result
        elif isinstance(kwargs["data"], list):
            return {
                "action": action_name,
                "data": kwargs["data"],
            }
        else:
            return {
                "action": action_name,
                "data": {
                    **merged,
                    **kwargs["data"],
                },
            }
