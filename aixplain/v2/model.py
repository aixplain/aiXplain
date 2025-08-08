from __future__ import annotations

from typing import Union, List, Optional, Any
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field

from .resource import (
    BaseListParams,
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BaseGetParams,
    Page,
    RunnableResourceMixin,
    BaseRunParams,
    Result,
)
from .enums import Function, Supplier, Language, AssetStatus


def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]:
    """Find supplier enum by ID."""
    supplier_id_str = str(supplier_id)
    return next(
        (
            supplier
            for supplier in Supplier
            if supplier.value.get("id") == supplier_id_str
        ),
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
    code: str


@dataclass_json
@dataclass
class Parameter:
    """Common parameter structure from the API response."""

    name: str
    required: bool
    multiple_values: bool = field(metadata=config(field_name="multipleValues"))
    is_fixed: bool = field(metadata=config(field_name="isFixed"))
    data_type: Optional[str] = field(
        default=None, metadata=config(field_name="dataType")
    )
    data_sub_type: Optional[str] = field(
        default=None, metadata=config(field_name="dataSubType")
    )
    values: List[Any] = field(default_factory=list)
    default_values: List[Any] = field(
        default_factory=list, metadata=config(field_name="defaultValues")
    )
    available_options: List[Any] = field(
        default_factory=list, metadata=config(field_name="availableOptions")
    )


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
    unit_type: Optional[str] = field(
        default=None, metadata=config(field_name="unitType")
    )
    unit_type_scale: Optional[str] = field(
        default=None, metadata=config(field_name="unitTypeScale")
    )


@dataclass_json
@dataclass
class SupplierInfo:
    """Supplier information structure from the API response."""

    id: Optional[Union[str, int]] = None
    name: Optional[str] = None
    code: Optional[str] = None


class ModelListParams(BaseListParams):
    functions: NotRequired[List[str]]
    suppliers: NotRequired[Union[str, Supplier, List[Union[str, Supplier]]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]
    saved: NotRequired[bool]
    status: NotRequired[List[str]]
    q: NotRequired[str]  # Search query parameter as per Swagger spec


class ModelRunParams(BaseRunParams):
    """Parameters for running models.

    This class is intentionally empty to allow dynamic validation
    based on each model's specific parameters from the backend.
    """

    pass


@dataclass_json
@dataclass
class Model(
    BaseResource,
    PagedListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BaseGetParams, "Model"],
    RunnableResourceMixin[ModelRunParams, Result],
):
    """Resource for models."""

    RESOURCE_PATH = "v2/models"

    # Core fields from BaseResource (id, name, description)
    service_name: Optional[str] = field(
        default=None, metadata=config(field_name="serviceName")
    )
    status: Optional[AssetStatus] = None
    hosted_by: Optional[str] = field(
        default=None, metadata=config(field_name="hostedBy")
    )
    developed_by: Optional[str] = field(
        default=None, metadata=config(field_name="developedBy")
    )

    # Supplier and function fields with proper decoders
    supplier: Optional[SupplierInfo] = None
    function: Optional[Function] = field(
        default=None,
        metadata=config(
            decoder=lambda x: (
                find_function_by_id(x["id"]) if isinstance(x, dict) and "id" in x else x
            )
        ),
    )

    # Pricing information
    pricing: Optional[Pricing] = None

    # Version information
    version: Optional[Version] = None

    # Function type and model type
    function_type: Optional[str] = field(
        default=None, metadata=config(field_name="functionType")
    )
    type: Optional[str] = None

    # Timestamps
    created_at: Optional[str] = field(
        default=None, metadata=config(field_name="createdAt")
    )
    updated_at: Optional[str] = field(
        default=None, metadata=config(field_name="updatedAt")
    )

    # Capabilities
    supports_streaming: Optional[bool] = field(
        default=None, metadata=config(field_name="supportsStreaming")
    )
    supports_byoc: Optional[bool] = field(
        default=None, metadata=config(field_name="supportsBYOC")
    )

    # Attributes and parameters with proper types
    attributes: Optional[List[Attribute]] = None
    params: Optional[List[Parameter]] = None

    def build_run_url(self, **kwargs: Unpack[ModelRunParams]) -> str:
        return f"{self.context.model_url}/{self.id}"

    @classmethod
    def get(
        cls: type["Model"],
        id: str,
        **kwargs: Unpack[BaseGetParams],
    ) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(
        cls: type["Model"],
        **kwargs: Unpack[ModelListParams],
    ) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> Result:
        """Run the model with dynamic parameter validation."""
        # Validate all parameters against model's expected inputs
        if self.params:
            param_errors = self._validate_params(**kwargs)
            if param_errors:
                raise ValueError(
                    f"Parameter validation failed: {'; '.join(param_errors)}"
                )

        return super().run(**kwargs)

    def _validate_params(self, **kwargs) -> List[str]:
        """Validate all provided parameters against the model's expected
        parameters."""
        if not self.params:
            return []

        errors = []

        # Validate all parameters (required and optional)
        for param in self.params:
            if param.name in kwargs:
                value = kwargs[param.name]
                if not self._validate_param_type(param, value):
                    errors.append(
                        (
                            f"Parameter '{param.name}' has invalid type. "
                            f"Expected {param.data_type}, "
                            f"got {type(value).__name__}"
                        )
                    )
            elif param.required:
                # errors.append(f"Required parameter '{param.name}' is missing")
                pass

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

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """
        Override to handle model-specific filter structure.
        """
        # Call parent's _populate_filters to get basic pagination and common
        # filters
        filters = super()._populate_filters(params)

        # Handle 'q' parameter directly as per Swagger spec
        if params.get("q") is not None:
            filters["q"] = params["q"]

        # Handle saved filter
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]

        # functions - accept list of strings and convert to backend shape
        if params.get("functions") is not None:
            functions_param = params["functions"]
            if isinstance(functions_param, list):
                filters["functions"] = [
                    {
                        "field": (f.value if hasattr(f, "value") else str(f)),
                        "dir": 1,
                    }
                    for f in functions_param
                ]
            else:
                value = (
                    functions_param.value
                    if hasattr(functions_param, "value")
                    else str(functions_param)
                )
                filters["functions"] = [{"field": value, "dir": 1}]

        # suppliers - should be array of strings
        if params.get("suppliers") is not None:
            suppliers = params["suppliers"]
            if isinstance(suppliers, list):
                filters["suppliers"] = [
                    (
                        s.value["code"]
                        if hasattr(s, "value") and isinstance(s.value, dict)
                        else str(s)
                    )
                    for s in suppliers
                ]
            else:
                supplier_value = (
                    suppliers.value["code"]
                    if (
                        hasattr(suppliers, "value")
                        and isinstance(suppliers.value, dict)
                    )
                    else str(suppliers)
                )
                filters["suppliers"] = [supplier_value]

        # status - should be array of strings
        if params.get("status") is not None:
            status = params["status"]
            if isinstance(status, list):
                filters["status"] = [
                    (
                        s.value
                        if (hasattr(s, "value") and isinstance(s.value, str))
                        else str(s)
                    )
                    for s in status
                ]
            else:
                if hasattr(status, "value") and isinstance(status.value, str):
                    status_value = status.value
                else:
                    status_value = str(status)
                filters["status"] = [status_value]

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
