"""Model resource for v2 API."""

from __future__ import annotations

from typing import Union, List, Optional, Any
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field

from .resource import (
    BaseSearchParams,
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    BaseGetParams,
    Page,
    RunnableResourceMixin,
    BaseRunParams,
    Result,
)
from .enums import Function, Supplier, Language, AssetStatus
from .mixins import ToolableMixin, ToolDict


@dataclass_json
@dataclass
class Message:
    """Message structure from the API response."""

    role: str
    content: str
    refusal: Optional[str] = None
    annotations: List[Any] = field(default_factory=list)


@dataclass_json
@dataclass
class Detail:
    """Detail structure from the API response."""

    index: int
    message: Message
    logprobs: Optional[Any] = None
    finish_reason: Optional[str] = field(default=None, metadata=config(field_name="finish_reason"))


@dataclass_json
@dataclass
class Usage:
    """Usage structure from the API response."""

    prompt_tokens: int = field(metadata=config(field_name="prompt_tokens"))
    completion_tokens: int = field(metadata=config(field_name="completion_tokens"))
    total_tokens: int = field(metadata=config(field_name="total_tokens"))


@dataclass_json
@dataclass
class ModelResult(Result):
    """Result for model runs with specific fields from the backend response."""

    details: Optional[List[Detail]] = None
    run_time: Optional[float] = field(default=None, metadata=config(field_name="runTime"))
    used_credits: Optional[float] = field(default=None, metadata=config(field_name="usedCredits"))
    usage: Optional[Usage] = None


class InputsProxy:
    """Proxy object that provides both dict-like and dot notation access to model parameters."""

    def __init__(self, model):
        """Initialize InputsProxy with a model instance."""
        self._model = model
        self._dynamic_attrs = {}
        self._setup_dynamic_attributes()

    def _setup_dynamic_attributes(self):
        """Create dynamic attributes for all model parameters."""
        if self._model.params:
            for param in self._model.params:
                # Create a dynamic attribute for each parameter
                attr_name = param.name

                # Set initial value from backend defaults if available
                initial_value = None
                if param.default_values:
                    initial_value = param.default_values[0].get("value")

                # Store the parameter metadata and value
                self._dynamic_attrs[attr_name] = {
                    "value": initial_value,
                    "param": param,
                    "required": param.required,
                    "data_type": param.data_type,
                    "data_sub_type": param.data_sub_type,
                }

    def __getitem__(self, key: str):
        """Dict-like access: inputs['temperature']."""
        if key in self._dynamic_attrs:
            return self._dynamic_attrs[key]["value"]
        raise KeyError(f"Parameter '{key}' not found")

    def __setitem__(self, key: str, value):
        """Dict-like assignment: inputs['temperature'] = 0.7."""
        if key in self._dynamic_attrs:
            # Validate the value against the parameter definition
            param_info = self._dynamic_attrs[key]
            param = param_info["param"]

            if not self._validate_param_type(param, value):
                raise ValueError(
                    f"Invalid value type for parameter '{key}'. Expected {param.data_type}, got {type(value).__name__}"
                )

            # Store the value
            self._dynamic_attrs[key]["value"] = value
        else:
            raise KeyError(f"Parameter '{key}' not found")

    def __getattr__(self, name: str):
        """Dot notation access: inputs.temperature."""
        if name in self._dynamic_attrs:
            return self._dynamic_attrs[name]["value"]
        raise AttributeError(f"Parameter '{name}' not found")

    def __setattr__(self, name: str, value):
        """Dot notation assignment: inputs.temperature = 0.7."""
        if name == "_model" or name == "_dynamic_attrs":
            super().__setattr__(name, value)
        elif name in self._dynamic_attrs:
            # Validate the value against the parameter definition
            param_info = self._dynamic_attrs[name]
            param = param_info["param"]

            if not self._validate_param_type(param, value):
                raise ValueError(
                    f"Invalid value type for parameter '{name}'. Expected {param.data_type}, got {type(value).__name__}"
                )

            # Store the value
            self._dynamic_attrs[name]["value"] = value
        else:
            raise AttributeError(f"Parameter '{name}' not found")

    def __contains__(self, key: str) -> bool:
        """Check if parameter exists: 'temperature' in inputs."""
        return key in self._dynamic_attrs

    def __len__(self) -> int:
        """Number of parameters."""
        return len(self._dynamic_attrs)

    def __iter__(self):
        """Iterate over parameter names."""
        return iter(self._dynamic_attrs.keys())

    def keys(self):
        """Get parameter names."""
        return list(self._dynamic_attrs.keys())

    def values(self):
        """Get parameter values."""
        return [info["value"] for info in self._dynamic_attrs.values()]

    def items(self):
        """Get parameter name-value pairs."""
        return [(name, info["value"]) for name, info in self._dynamic_attrs.items()]

    def get(self, key: str, default=None):
        """Get parameter value with default."""
        if key in self._dynamic_attrs:
            return self._dynamic_attrs[key]["value"]
        return default

    def update(self, **kwargs):
        """Update multiple parameters at once."""
        for key, value in kwargs.items():
            if key in self._dynamic_attrs:
                self[key] = value  # This will trigger validation
            else:
                raise KeyError(f"Parameter '{key}' not found")

    def clear(self):
        """Reset all parameters to backend defaults."""
        for param_name in self._dynamic_attrs:
            self.reset_parameter(param_name)

    def copy(self):
        """Get a copy of current parameter values."""
        return {name: info["value"] for name, info in self._dynamic_attrs.items()}

    def has_parameter(self, param_name: str) -> bool:
        """Check if a parameter exists."""
        return param_name in self._dynamic_attrs

    def get_parameter_names(self) -> list:
        """Get a list of all available parameter names."""
        return list(self._dynamic_attrs.keys())

    def get_required_parameters(self) -> list:
        """Get a list of required parameter names."""
        return [name for name, info in self._dynamic_attrs.items() if info["required"]]

    def get_parameter_info(self, param_name: str):
        """Get information about a specific parameter."""
        if param_name in self._dynamic_attrs:
            return self._dynamic_attrs[param_name].copy()
        return None

    def get_all_parameters(self) -> dict:
        """Get all current parameter values."""
        return {name: info["value"] for name, info in self._dynamic_attrs.items()}

    def reset_parameter(self, param_name: str):
        """Reset a parameter to its backend default value."""
        if param_name in self._dynamic_attrs:
            param_info = self._dynamic_attrs[param_name]
            param = param_info["param"]

            if param.default_values:
                self._dynamic_attrs[param_name]["value"] = param.default_values[0].get("value")
            else:
                self._dynamic_attrs[param_name]["value"] = None

    def reset_all_parameters(self):
        """Reset all parameters to their backend default values."""
        for param_name in self._dynamic_attrs:
            self.reset_parameter(param_name)

    def _validate_param_type(self, param, value) -> bool:
        """Validate parameter type based on the parameter definition."""
        # Allow None values for all parameters
        if value is None:
            return True

        # If data_type is not specified, accept any value
        if param.data_type is None:
            return True

        # Check data_type first
        if param.data_type == "text":
            # For text type, check data_sub_type for more specific validation
            if param.data_sub_type == "json":
                # text/json should accept dict, list, or string
                return isinstance(value, (dict, list, str))
            elif param.data_sub_type == "number":
                # text/number should accept int, float, or string
                return isinstance(value, (int, float, str))
            else:
                # text/other should accept only string
                return isinstance(value, str)
        elif param.data_type == "json":
            return isinstance(value, (dict, list, str))
        elif param.data_type == "number":
            return isinstance(value, (int, float))
        elif param.data_type == "boolean":
            return isinstance(value, bool)
        elif param.data_type == "array":
            return isinstance(value, list)
        elif param.data_type == "label":
            # label type should accept string or None
            return isinstance(value, (str, type(None)))
        elif param.data_type == "audio":
            # audio type should accept string or None
            return isinstance(value, (str, type(None)))
        else:
            # For unknown types, accept any value
            return True

    def __repr__(self):
        """Return string representation of InputsProxy."""
        params = self.get_all_parameters()
        return f"InputsProxy({params})"


def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]:
    """Find supplier enum by ID."""
    supplier_id_str = str(supplier_id)
    return next(
        (supplier for supplier in Supplier if supplier.value.get("id") == supplier_id_str),
        None,
    )


def find_function_by_id(function_id: str) -> Optional[Function]:
    """Find function enum by ID."""
    try:
        return Function(function_id)
    except ValueError:
        return None


@dataclass_json
@dataclass
class Attribute:
    """Common attribute structure from the API response."""

    name: str
    code: Optional[Any] = None
    value: Optional[Any] = None


@dataclass_json
@dataclass
class Parameter:
    """Common parameter structure from the API response."""

    name: str
    required: bool = False
    multiple_values: bool = field(default=False, metadata=config(field_name="multipleValues"))
    is_fixed: bool = field(default=False, metadata=config(field_name="isFixed"))
    data_type: Optional[str] = field(default=None, metadata=config(field_name="dataType"))
    data_sub_type: Optional[str] = field(default=None, metadata=config(field_name="dataSubType"))
    values: List[Any] = field(default_factory=list)
    default_values: List[Any] = field(default_factory=list, metadata=config(field_name="defaultValues"))
    available_options: List[Any] = field(default_factory=list, metadata=config(field_name="availableOptions"))


@dataclass_json
@dataclass
class Version:
    """Version structure from the API response."""

    name: Optional[str] = None
    id: Optional[str] = None


@dataclass_json
@dataclass
class Pricing:
    """Pricing structure from the API response."""

    price: Optional[float] = None
    unit_type: Optional[str] = field(default=None, metadata=config(field_name="unitType"))
    unit_type_scale: Optional[str] = field(default=None, metadata=config(field_name="unitTypeScale"))


@dataclass_json
@dataclass
class VendorInfo:
    """Supplier information structure from the API response."""

    id: Optional[Union[str, int]] = None
    name: Optional[str] = None
    code: Optional[str] = None


class ModelSearchParams(BaseSearchParams):
    """Search parameters for model queries."""

    functions: NotRequired[List[str]]
    vendors: NotRequired[Union[str, Supplier, List[Union[str, Supplier]]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]
    saved: NotRequired[bool]
    status: NotRequired[List[str]]
    q: NotRequired[str]  # Search query parameter as per Swagger spec
    host: NotRequired[str]  # Filter by host (e.g., "openai", "aiXplain")
    developer: NotRequired[str]  # Filter by developer (e.g., "OpenAI")
    path: NotRequired[str]  # Filter by path prefix (e.g., "openai/gpt-4")


class ModelRunParams(BaseRunParams):
    """Parameters for running models.

    This class is intentionally empty to allow dynamic validation
    based on each model's specific parameters from the backend.
    """

    pass


@dataclass_json
@dataclass(repr=False)
class Model(
    BaseResource,
    SearchResourceMixin[ModelSearchParams, "Model"],
    GetResourceMixin[BaseGetParams, "Model"],
    RunnableResourceMixin[ModelRunParams, ModelResult],
    ToolableMixin,
):
    """Resource for models."""

    RESOURCE_PATH = "v2/models"
    RESPONSE_CLASS = ModelResult

    # Core fields from BaseResource (id, name, description)
    service_name: Optional[str] = field(default=None, metadata=config(field_name="serviceName"))
    status: Optional[AssetStatus] = None
    host: Optional[str] = None
    developer: Optional[str] = None
    vendor: Optional[VendorInfo] = None
    function: Optional[Function] = field(
        default=None,
        metadata=config(decoder=lambda x: (find_function_by_id(x["id"]) if isinstance(x, dict) and "id" in x else x)),
    )

    # Pricing information
    pricing: Optional[Pricing] = None

    # Version information
    version: Optional[Version] = None

    # Function type and model type
    function_type: Optional[str] = field(default=None, metadata=config(field_name="functionType"))
    type: Optional[str] = "model"

    # Timestamps
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))

    # Capabilities
    supports_streaming: Optional[bool] = field(default=None, metadata=config(field_name="supportsStreaming"))
    supports_byoc: Optional[bool] = field(default=None, metadata=config(field_name="supportsBYOC"))

    # Attributes and parameters with proper types
    attributes: Optional[List[Attribute]] = None
    params: Optional[List[Parameter]] = None

    # Dynamic parameter attributes for convenient access
    # _dynamic_attrs: dict = field(default_factory=dict, init=False) # Removed

    def __post_init__(self):
        """Initialize dynamic attributes based on backend parameters."""
        # Initialize the inputs proxy
        self.inputs = InputsProxy(self)

    def __setattr__(self, name: str, value):
        """Handle bulk assignment to inputs."""
        if name == "inputs" and isinstance(value, dict):
            # Handle bulk assignment to inputs
            self.inputs.update(**value)
        else:
            # Handle regular attributes
            super().__setattr__(name, value)

    def build_run_url(self, **kwargs: Unpack[ModelRunParams]) -> str:
        """Build the URL for running the model."""
        self._ensure_valid_state()
        return f"{self.context.model_url}/{self.id}"

    def mark_as_deleted(self) -> None:
        """Mark the model as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

    @classmethod
    def get(
        cls: type["Model"],
        id: str,
        **kwargs: Unpack[BaseGetParams],
    ) -> "Model":
        """Get a model by ID."""
        return super().get(id, **kwargs)

    @classmethod
    def search(
        cls: type["Model"],
        query: Optional[str] = None,
        **kwargs: Unpack[ModelSearchParams],
    ) -> Page["Model"]:
        """Search with optional query and filtering.

        Args:
            query: Optional search query string
            **kwargs: Additional search parameters (functions, suppliers, etc.)

        Returns:
            Page of items matching the search criteria
        """
        # If query is provided, add it to kwargs
        if query is not None:
            kwargs["query"] = query

        # Use v2 endpoint - it uses "results" as the items key (default)
        return super().search(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> ModelResult:
        """Run the model with dynamic parameter validation and default handling."""
        # Merge dynamic attributes with provided kwargs
        effective_params = self._merge_with_dynamic_attrs(**kwargs)

        # Validate all parameters against model's expected inputs
        if self.params:
            param_errors = self._validate_params(**effective_params)
            if param_errors:
                raise ValueError(f"Parameter validation failed: {'; '.join(param_errors)}")

        return super().run(**effective_params)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Merge provided parameters with dynamic attributes.

        Args:
            **kwargs: Parameters provided to the run method

        Returns:
            Dictionary with all parameters, including dynamic attributes
        """
        # Start with current dynamic attribute values
        merged = self.inputs.get_all_parameters()

        # Override with explicitly provided parameters
        merged.update(kwargs)

        # Filter out None values - they represent unset parameters that shouldn't be sent to the API
        filtered_merged = {k: v for k, v in merged.items() if v is not None}

        return filtered_merged

    def _validate_params(self, **kwargs) -> List[str]:
        """Validate all provided parameters against the model's expected parameters."""
        if not self.params:
            return []

        errors = []

        # Validate all parameters (required and optional)
        for param in self.params:
            if param.name in kwargs:
                value = kwargs[param.name]
                # Only validate if the value is not None (None means parameter is not set)
                if value is not None and not self._validate_param_type(param, value):
                    errors.append(
                        f"Parameter '{param.name}' has invalid type. "
                        f"Expected {param.data_type}, "
                        f"got {type(value).__name__}"
                    )
            elif param.required:
                errors.append(f"Required parameter '{param.name}' is missing")

        return errors

    def _validate_param_type(self, param: Parameter, value: Any) -> bool:
        """Validate parameter type based on the parameter definition."""
        # If data_type is not specified, accept any value
        if param.data_type is None:
            return True

        # Check data_type first
        if param.data_type == "text":
            # For text type, check data_sub_type for more specific validation
            if param.data_sub_type == "json":
                # text/json should accept dict, list, or string
                return isinstance(value, (dict, list, str))
            elif param.data_sub_type == "number":
                # text/number should accept int, float, or string
                return isinstance(value, (int, float, str))
            else:
                # text/other should accept only string
                return isinstance(value, str)
        elif param.data_type == "json":
            return isinstance(value, (dict, list, str))
        elif param.data_type == "number":
            return isinstance(value, (int, float))
        elif param.data_type == "boolean":
            return isinstance(value, bool)
        elif param.data_type == "array":
            return isinstance(value, list)
        else:
            # For unknown types, accept any value
            return True

    def as_tool(self) -> ToolDict:
        """Serialize this model as a tool for agent creation.

        This method converts the model into a dictionary format that can be used
        as a tool when creating agents. The format matches what the agent factory
        expects for model tools.

        Returns:
            dict: A dictionary representing this model as a tool with the following structure:
                - id: The model's ID
                - name: The model's name
                - description: The model's description
                - supplier: The supplier code
                - parameters: Current parameter values
                - function: The model's function type
                - type: Always "model"
                - version: The model's version
                - assetId: The model's ID (same as id)

        Example:
            >>> model = aix.Model.get("some-model-id")
            >>> agent = aix.Agent(..., tools=[model.as_tool()])
        """
        # Get current parameter values using get_parameters()
        parameters = self.get_parameters()

        # Get supplier code
        supplier_code = "aixplain"  # Default supplier
        if self.vendor and self.vendor.code:
            supplier_code = self.vendor.code

        # Get function type
        function_type = None
        if self.function:
            function_type = self.function.value if hasattr(self.function, "value") else str(self.function)

        # Get version - handle Version objects properly
        version = None
        if self.version:
            if hasattr(self.version, "id") and self.version.id:
                version = self.version.id
            elif isinstance(self.version, dict) and "id" in self.version:
                version = self.version["id"]
            elif isinstance(self.version, str):
                version = self.version

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "supplier": supplier_code,
            "parameters": parameters,
            "function": function_type,
            "type": "model",
            "version": version,
            "assetId": self.id,
        }

    def get_parameters(self) -> List[dict]:
        """Get current parameter values for this model.

        Returns:
            List[dict]: List of parameter dictionaries with current values
        """
        parameters = []
        if self.params:
            for param in self.params:
                param_value = self.inputs.get(param.name)
                if param_value is not None:
                    parameters.append(
                        {
                            "name": param.name,
                            "value": param_value,
                            "required": param.required,
                            "datatype": param.data_type,
                            "allowMulti": param.multiple_values,
                            "supportsVariables": False,  # Default value
                            "fixed": param.is_fixed,
                            "description": "",  # Default empty description
                        }
                    )
        return parameters

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Override to handle model-specific filter structure."""
        # Call parent's _populate_filters to get basic pagination and common
        # filters
        filters = super()._populate_filters(params)

        # Handle 'q' parameter directly as per Swagger spec
        if params.get("q") is not None:
            filters["q"] = params["q"]

        # Handle saved filter
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]

        # Handle host filter (maps to hostedBy in API)
        if params.get("host") is not None:
            filters["hosts"] = [params["host"]]

        # Handle developer filter (maps to developedBy in API)
        if params.get("developer") is not None:
            filters["developers"] = [params["developer"]]

        # Handle path prefix filter (e.g., "openai/gpt-4")
        if params.get("path") is not None:
            filters["path"] = params["path"]

        # functions - accept list of strings and convert to backend shape
        # Use v2 format: array of objects with "id" key (required by v2/models/paginate endpoint)
        if params.get("functions") is not None:
            functions_param = params["functions"]
            if isinstance(functions_param, list):
                filters["functions"] = [{"id": (f.value if hasattr(f, "value") else str(f))} for f in functions_param]
            else:
                value = functions_param.value if hasattr(functions_param, "value") else str(functions_param)
                filters["functions"] = [{"id": value}]

        # suppliers - should be array of strings
        if params.get("vendors") is not None:
            suppliers = params["vendors"]
            if isinstance(suppliers, list):
                filters["suppliers"] = [
                    (s.value["code"] if hasattr(s, "value") and isinstance(s.value, dict) else str(s))
                    for s in suppliers
                ]
            else:
                supplier_value = (
                    suppliers.value["code"]
                    if (hasattr(suppliers, "value") and isinstance(suppliers.value, dict))
                    else str(suppliers)
                )
                filters["suppliers"] = [supplier_value]

        # status - should be array of strings
        if params.get("status") is not None:
            status = params["status"]
            if isinstance(status, list):
                filters["status"] = [
                    (s.value if (hasattr(s, "value") and isinstance(s.value, str)) else str(s)) for s in status
                ]
            else:
                if hasattr(status, "value") and isinstance(status.value, str):
                    status_value = status.value
                else:
                    status_value = str(status)
                filters["status"] = [status_value]

        # source_languages - should be array of language codes
        if params.get("source_languages") is not None:
            source_langs = params["source_languages"]
            if isinstance(source_langs, list):
                filters["sourceLanguages"] = [
                    (lang.value if hasattr(lang, "value") and isinstance(lang.value, str) else str(lang))
                    for lang in source_langs
                ]
            else:
                lang_value = (
                    source_langs.value
                    if hasattr(source_langs, "value") and isinstance(source_langs.value, str)
                    else str(source_langs)
                )
                filters["sourceLanguages"] = [lang_value]

        # target_languages - should be array of language codes
        if params.get("target_languages") is not None:
            target_langs = params["target_languages"]
            if isinstance(target_langs, list):
                filters["targetLanguages"] = [
                    (lang.value if hasattr(lang, "value") and isinstance(lang.value, str) else str(lang))
                    for lang in target_langs
                ]
            else:
                lang_value = (
                    target_langs.value
                    if hasattr(target_langs, "value") and isinstance(target_langs.value, str)
                    else str(target_langs)
                )
                filters["targetLanguages"] = [lang_value]

        # is_finetunable - boolean filter
        # Note: v1 API uses "isFineTunable" (capital T), v2 API uses "isFinetunable" (lowercase t)
        if params.get("is_finetunable") is not None:
            filters["isFineTunable"] = params["is_finetunable"]

        # sort - should be array of objects with field and dir
        if params.get("sort_by") is not None or params.get("sort_order") is not None:
            sort_field = params.get("sort_by", "name")
            sort_order = params.get("sort_order", "asc")

            # Convert enum to string if needed
            if hasattr(sort_field, "value"):
                sort_field = sort_field.value

            # Convert sort order to integer
            if hasattr(sort_order, "value"):
                sort_dir = sort_order.value
            else:
                sort_dir = 1 if str(sort_order).lower() == "asc" else -1

            filters["sort"] = [{"field": str(sort_field), "dir": sort_dir}]
        else:
            # Always include empty sort array as backend requires it
            filters["sort"] = [{}]

        return filters
