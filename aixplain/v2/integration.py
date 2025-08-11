from typing import Optional, List, Any, Dict, TYPE_CHECKING
import json
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from .resource import BaseListParams, BaseResult
from .model import Model
from .enums import AuthenticationScheme

if TYPE_CHECKING:
    from .tool import Tool


@dataclass_json
@dataclass
class Input:
    """Input parameter for an action."""

    name: str
    code: Optional[str] = None
    value: List[Any] = field(default_factory=list)
    availableOptions: List[Any] = field(default_factory=list)
    datatype: str = "string"
    allowMulti: bool = False
    supportsVariables: bool = False
    defaultValue: List[Any] = field(default_factory=list)
    required: bool = False
    fixed: bool = False
    description: str = ""


@dataclass_json
@dataclass
class Action:
    """Container for tool action information and inputs."""

    name: Optional[str] = None
    description: Optional[str] = None
    displayName: Optional[str] = None
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
    inputs: Optional[List[Input]] = None


@dataclass_json
@dataclass
class ToolId:
    """Result for tool operations."""

    id: str


class IntegrationResult(BaseResult):
    """Result for connection operations.

    The backend returns the connection ID in data.id.
    """

    data: ToolId


class IntegrationListParams(BaseListParams):
    """Parameters for listing integrations."""

    pass


class Integration(Model):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    RESOURCE_PATH = "v2/integrations"
    RESPONSE_CLASS = IntegrationResult

    # Make AuthenticationScheme accessible
    AuthenticationScheme = AuthenticationScheme

    # Integration-specific properties
    @property
    def auth_schemes(self) -> List[str]:
        """Get authentication schemes for integrations."""
        if not self.attributes:
            return []

        auth_schemes_attr = next(
            (attr for attr in self.attributes if attr.name == "auth_schemes"), None
        )

        if not auth_schemes_attr:
            return []

        try:
            return json.loads(auth_schemes_attr.code)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_auth_inputs(
        self, auth_scheme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get authentication inputs for a specific auth scheme."""
        if not self.attributes or not auth_scheme:
            return []

        inputs_attr = next(
            (attr for attr in self.attributes if attr.name == f"{auth_scheme}-inputs"),
            None,
        )

        if not inputs_attr:
            return []

        try:
            return json.loads(inputs_attr.code)
        except (json.JSONDecodeError, TypeError):
            return []

    def _validate_params(self, **kwargs) -> List[str]:
        """Validate all provided parameters against the model's expected
        parameters and integration-specific auth requirements."""
        # Call parent validation first
        errors = super()._validate_params(**kwargs)

        auth_scheme = kwargs["authScheme"]
        if auth_scheme not in self.auth_schemes:
            errors.append(
                f"Invalid auth_scheme '{auth_scheme}'. "
                f"Available schemes: {self.auth_schemes}"
            )

        data = kwargs["data"]
        data_errors = self._validate_data_params(data, auth_scheme)

        if data_errors:
            errors.extend(data_errors)

        return errors

    def _validate_data_params(
        self, data: Optional[Dict[str, Any]], auth_scheme: Optional[str] = None
    ) -> List[str]:
        """Validate data parameter against expected auth inputs for the auth
        scheme."""
        errors = []

        # Handle None data
        if data is None:
            data = {}

        # Get expected auth inputs for the auth scheme
        expected_inputs = self.get_auth_inputs(auth_scheme)
        if not expected_inputs:
            return errors

        # Validate each required input
        for expected_input in expected_inputs:
            input_name = expected_input.get("name")
            required = expected_input.get("required", False)

            if required and input_name not in data:
                errors.append(
                    f"Required auth input '{input_name}' is missing for "
                    f"auth scheme '{auth_scheme}'"
                )

            # Validate input type if specified
            if input_name in data and "type" in expected_input:
                expected_type = expected_input["type"]
                actual_value = data[input_name]

                if not self._validate_input_type(actual_value, expected_type):
                    errors.append(
                        f"Auth input '{input_name}' has invalid type. "
                        f"Expected {expected_type}, got "
                        f"{type(actual_value).__name__}"
                    )

        return errors

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

    def list_actions(self) -> List[Action]:
        """List available actions for the integration."""
        run_url = self.build_run_url()
        response = self.context.client.request(
            "post", run_url, json={"action": "LIST_ACTIONS", "data": {}}
        )

        # Handle the response data
        if "data" not in response:
            return []

        actions = []
        for action_data in response["data"]:
            try:
                # Handle case where action_data might be a string or other format
                if isinstance(action_data, dict):
                    actions.append(Action.from_dict(action_data))
                else:
                    # Skip invalid action data
                    continue
            except Exception:
                # Skip invalid action data
                continue

        return actions

    def list_inputs(self, *actions: str) -> List[Action]:
        """List available inputs for the integration."""
        run_url = self.build_run_url()
        response = self.context.client.request(
            "post",
            run_url,
            json={"action": "LIST_INPUTS", "data": {"actions": actions}},
        )

        # Handle the response data
        if "data" not in response:
            return []

        actions = []
        for input_data in response["data"]:
            actions.append(Action.from_dict(input_data))

        return actions

    def connect(self, **kwargs: Any) -> "Tool":
        """Connect the integration."""
        response = self.run(**kwargs)
        tool_id = response.data.id
        return self.context.Tool.get(tool_id)
