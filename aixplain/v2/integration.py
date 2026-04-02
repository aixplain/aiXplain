"""Integration module for managing external service integrations."""

import warnings
from typing import Optional, List, Any, Dict, TYPE_CHECKING
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from functools import cached_property

from .resource import BaseSearchParams, Result
from .model import Model
from .enums import AuthenticationScheme
from .actions import Actions, Action as ActionView, Inputs

if TYPE_CHECKING:
    from .tool import Tool


@dataclass_json
@dataclass
class ActionInputSpec:
    """Backend input-parameter specification for an action (deserialization only)."""

    name: str
    code: Optional[str] = None
    value: List[Any] = field(default_factory=list)
    available_options: List[Any] = field(default_factory=list, metadata=config(field_name="availableOptions"))
    datatype: str = "string"
    allow_multi: bool = field(default=False, metadata=config(field_name="allowMulti"))
    supports_variables: bool = field(default=False, metadata=config(field_name="supportsVariables"))
    default_value: List[Any] = field(default_factory=list, metadata=config(field_name="defaultValue"))
    required: bool = False
    fixed: bool = False
    description: Optional[str] = ""


@dataclass_json
@dataclass(repr=False)
class ActionSpec:
    """Backend action specification (deserialization only)."""

    name: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = field(default=None, metadata=config(field_name="displayName"))
    slug: Optional[str] = None
    available_versions: Optional[List[str]] = None
    version: Optional[str] = None
    toolkit: Optional[Dict[str, Any]] = None
    input_parameters: Optional[Dict[str, Any]] = None
    output_parameters: Optional[Dict[str, Any]] = None
    scopes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    no_auth: Optional[bool] = None
    deprecated: Optional[Dict[str, Any]] = None
    inputs: Optional[List[ActionInputSpec]] = None

    def __repr__(self) -> str:
        """Return a concise representation of the action spec."""
        name_str = self.name or self.slug or "Unknown"
        parts = [f"name='{name_str}'"]
        if self.inputs:
            input_codes = [inp.code or inp.name for inp in self.inputs if inp.code or inp.name]
            if input_codes:
                parts.append(f"inputs=[{', '.join(input_codes)}]")
        return f"ActionSpec({', '.join(parts)})"


@dataclass_json
@dataclass
class ToolId:
    """Result for tool operations."""

    id: str
    redirect_url: Optional[str] = field(default=None, metadata=config(field_name="redirectURL"))


@dataclass_json
@dataclass
class IntegrationResult(Result):
    """Result for connection operations.

    The backend returns the connection ID in data.id.
    """

    data: ToolId


class IntegrationSearchParams(BaseSearchParams):
    """Parameters for listing integrations."""

    pass


@dataclass
class ActionMixin:
    """Mixin class providing action-related functionality for integrations and tools."""

    actions_available: Optional[bool] = field(default=None, metadata=config(field_name="actionsAvailable"))

    def _poll_for_data(self, response: dict, timeout: float = 30, wait_time: float = 1) -> Any:
        """Poll an async response until completion and return the ``data`` field."""
        import time

        data = response.get("data")
        if response.get("completed", True) or not isinstance(data, str) or not data.startswith("http"):
            return data

        poll_url = data
        start = time.time()
        while (time.time() - start) < timeout:
            time.sleep(wait_time)
            poll_resp = self.context.client.request("get", poll_url)
            if poll_resp.get("completed", False) or poll_resp.get("status") == "SUCCESS":
                return poll_resp.get("data")
        return None

    def list_actions(self) -> List[ActionSpec]:
        """List available actions for the integration.

        Returns:
            List of :class:`ActionSpec` objects from the backend.
        """
        if self.actions_available is False:
            return []

        run_url = self.build_run_url()
        response = self.context.client.request("post", run_url, json={"action": "LIST_ACTIONS", "data": {}})

        data = self._poll_for_data(response)
        if not data or not isinstance(data, list):
            return []

        actions: List[ActionSpec] = []
        for action_data in data:
            try:
                if isinstance(action_data, dict):
                    actions.append(ActionSpec.from_dict(action_data))
                else:
                    continue
            except Exception:
                continue

        return actions

    def _list_inputs(self, *actions: str) -> List[ActionSpec]:
        """List available inputs for the integration (internal).

        This is the internal implementation. Use ``tool.actions['name'].inputs``
        to discover and configure action inputs interactively.
        """
        run_url = self.build_run_url()
        response = self.context.client.request(
            "post",
            run_url,
            json={"action": "LIST_INPUTS", "data": {"actions": actions}},
        )

        data = self._poll_for_data(response)
        if not data or not isinstance(data, list):
            return []

        result: List[ActionSpec] = []
        for input_data in data:
            if isinstance(input_data, dict):
                result.append(ActionSpec.from_dict(input_data))

        return result

    def list_inputs(self, *actions: str) -> List[ActionSpec]:
        """List available inputs for the integration.

        .. deprecated::
            Use ``tool.actions['action_name'].inputs`` to discover and configure
            action inputs instead.
        """
        warnings.warn(
            "list_inputs() is deprecated. Use tool.actions['action_name'].inputs to "
            "discover and configure action inputs instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._list_inputs(*actions)

    @cached_property
    def actions(self) -> Actions:
        """Collection of actions with their inputs.

        Returns:
            :class:`Actions` collection.  Access individual actions via
            ``tool.actions['ACTION_NAME']`` which returns an :class:`Action`
            whose ``.inputs`` property lazily fetches input specs.
        """
        container = self

        def _list_action_names() -> List[tuple[str, Optional[str]]]:
            specs = container.list_actions()
            return [(s.name or s.slug or "", s.description) for s in specs]

        def _action_factory(action_name: str, description: Optional[str] = None) -> ActionView:
            def _load_inputs() -> Inputs:
                specs = container._list_inputs(action_name)
                if not specs:
                    raise ValueError(f"Action '{action_name}' not found or has no input parameters defined.")
                normalized_action_name = action_name.lower()
                spec = next(
                    (
                        candidate
                        for candidate in specs
                        if (candidate.name and candidate.name.lower() == normalized_action_name)
                    ),
                    None,
                )
                if spec is None:
                    raise ValueError(f"Action '{action_name}' not found in LIST_INPUTS response.")
                return Inputs.from_action_input_specs(spec.inputs)

            return ActionView(name=action_name, description=description, _inputs_loader=_load_inputs)

        return Actions(
            _action_factory=_action_factory,
            _actions_lister=_list_action_names,
        )

    def set_inputs(self, inputs_dict: Dict[str, Dict[str, Any]]) -> None:
        """Set multiple action inputs in bulk using a dictionary tree structure.

        Args:
            inputs_dict: ``{"ACTION_NAME": {"input_param": "value", ...}, ...}``

        Raises:
            ValueError: If an action name is not found or invalid.
            KeyError: If an input parameter is not found for an action.
        """
        for action_name, input_values in inputs_dict.items():
            if not isinstance(input_values, dict):
                raise ValueError(
                    f"Input values for action '{action_name}' must be a dictionary, got {type(input_values).__name__}"
                )

            try:
                action_obj = self.actions[action_name]
            except (ValueError, KeyError) as e:
                raise ValueError(f"Action '{action_name}' not found: {e}")

            try:
                action_obj.inputs.update(**input_values)
            except KeyError as e:
                raise KeyError(
                    f"Input parameter {e} not found for action '{action_name}'. "
                    f"Available inputs: {action_obj.inputs.keys()}"
                )
            except Exception as e:
                raise ValueError(f"Error setting inputs for action '{action_name}': {e}")


@dataclass_json
@dataclass
class Integration(Model, ActionMixin):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    RESOURCE_PATH = "v2/integrations"
    RESPONSE_CLASS = IntegrationResult

    AuthenticationScheme = AuthenticationScheme

    def _validate_input_type(self, value: Any, expected_type: str) -> bool:
        """Validate input type based on expected type."""
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "object": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list),
        }

        validator = type_validators.get(expected_type)
        return validator(value) if validator else True

    def run(self, **kwargs: Any) -> IntegrationResult:
        """Run the integration with validation."""
        return super().run(**kwargs)

    def connect(self, **kwargs: Any) -> "Tool":
        """Connect the integration.

        For OAuth-based integrations, the backend may return a redirect URL
        that the user must visit to complete authentication before using the tool.

        Returns:
            Tool: The created tool. If OAuth authentication is required,
                ``tool.redirect_url`` will contain the URL the user must visit.

        Raises:
            ValueError: If the connection fails (e.g., name already exists).
        """
        response = self.run(**kwargs)
        if not response.data or not response.data.id:
            error_msg = (
                getattr(response, "error_message", None) or getattr(response, "supplier_error", None) or "Unknown error"
            )
            raise ValueError(f"Integration connection failed: {error_msg}")
        tool = self.context.Tool.get(response.data.id)
        if response.data.redirect_url:
            tool.redirect_url = response.data.redirect_url
            warnings.warn(
                f"Before using the tool, please visit the following URL to complete the connection: {response.data.redirect_url}"
            )
        return tool

    def handle_run_response(self, response: dict, **kwargs: Any) -> IntegrationResult:
        """Handle the response from the integration."""
        try:
            return super().handle_run_response(response)
        except Exception:
            if "data" in response and isinstance(response["data"], str):
                wrapped_response = response.copy()
                wrapped_response["data"] = {"id": response["data"]}
                return super().handle_run_response(wrapped_response)
            else:
                raise
