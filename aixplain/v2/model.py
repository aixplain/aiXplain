from __future__ import annotations

from typing import Union, List, Optional, Any, Dict
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
    ToolMixin,
)
from .enums import Function, Supplier, Language, AssetStatus, ToolType


def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]:
    """Find supplier enum by ID."""
    supplier_id_str = str(supplier_id)
    for supplier in Supplier:
        if supplier.value.get("id") == supplier_id_str:
            return supplier
    return None


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
    data_type: str = field(metadata=config(field_name="dataType"))
    data_sub_type: str = field(metadata=config(field_name="dataSubType"))
    multiple_values: bool = field(metadata=config(field_name="multipleValues"))
    is_fixed: bool = field(metadata=config(field_name="isFixed"))
    values: List[Any] = field(default_factory=list)
    default_values: List[Any] = field(
        default_factory=list, metadata=config(field_name="defaultValues")
    )
    available_options: List[Any] = field(
        default_factory=list, metadata=config(field_name="availableOptions")
    )


@dataclass_json
@dataclass
class ModelVersion:
    """Model version structure from the API response."""
    name: Optional[str] = None
    id: Optional[str] = None


@dataclass_json
@dataclass
class ModelPricing:
    """Model pricing structure from the API response."""
    price: Optional[float] = None
    unit_type: Optional[str] = field(
        default=None, metadata=config(field_name="unitType")
    )
    unit_type_scale: Optional[str] = field(
        default=None, metadata=config(field_name="unitTypeScale")
    )


@dataclass_json
@dataclass
class ModelSupplier:
    """Model supplier structure from the API response."""
    id: Optional[Union[str, int]] = None
    name: Optional[str] = None
    code: Optional[str] = None


class ModelListParams(BaseListParams):
    function: NotRequired[Function]
    suppliers: NotRequired[Union[Supplier, List[Supplier]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]


class ModelRunParams(BaseRunParams):
    data: Union[str, dict]
    context: NotRequired[str]
    prompt: NotRequired[str]
    history: NotRequired[List[dict]]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]


@dataclass_json
@dataclass
class Model(
    BaseResource,
    PagedListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BaseGetParams, "Model"],
    RunnableResourceMixin[ModelRunParams, Result],
    ToolMixin,
):
    """Resource for models."""

    RESOURCE_PATH = "v2/models"
    TOOL_TYPE = ToolType.MODEL

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
    subscriptions: Optional[List[str]] = None
    
    # Supplier and function fields with proper decoders
    supplier: Optional[ModelSupplier] = None
    function: Optional[Function] = field(
        default=None,
        metadata=config(
            decoder=lambda x: (
                find_function_by_id(x["id"]) 
                if isinstance(x, dict) and "id" in x 
                else x
            )
        ),
    )
    
    # Pricing information
    pricing: Optional[ModelPricing] = None
    
    # Version information
    version: Optional[ModelVersion] = None
    
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
        **kwargs: Unpack[BaseGetParams]
    ) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(
        cls: type["Model"], 
        **kwargs: Unpack[ModelListParams]
    ) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> Result:
        return super().run(**kwargs)

    def as_tool(self) -> Dict[str, Any]:
        """
        Override as_tool to include model-specific information and
        parameters.
        """
        base_tool = super().as_tool()

        # Add parameters if available
        if self.params:
            base_tool["parameters"] = self.params

        # Add model-specific information
        base_tool["name"] = self.name
        base_tool["description"] = self.description
        base_tool["supplier"] = (
            (
                self.supplier.code
                if hasattr(self.supplier, "code")
                else str(self.supplier)
            )
            if self.supplier
            else None
        )
        base_tool["function"] = (
            (
                self.function.value
                if hasattr(self.function, "value")
                else str(self.function)
            )
            if self.function
            else None
        )
        base_tool["version"] = self.version
        base_tool["function_type"] = self.function_type
        base_tool["type"] = self.type

        return base_tool

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """
        Override to handle model-specific filter structure.
        Matches the Swagger specification:
        {
          "pageSize": 20,
          "pageNumber": 0,
          "q": "string",
          "saved": true,
          "functions": [
            {
              "field": "string",
              "dir": 1
            }
          ],
          "suppliers": [
            "string"
          ],
          "sort": [
            {
              "field": "string",
              "dir": 1
            }
          ],
          "status": [
            "onboarded"
          ]
        }
        """
        # Call parent's _populate_filters to get basic pagination and common 
        # filters
        filters = super()._populate_filters(params)
        
        # Handle saved filter
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]
        
        # Handle functions - should be array of objects with field and dir
        if params.get("function") is not None:
            function = params["function"]
            if isinstance(function, Function):
                # Function inherits from str, so function.value is already a 
                # string
                filters["functions"] = [{"field": function.value, "dir": 1}]
        
        # Handle suppliers - should be array of strings
        if params.get("suppliers") is not None:
            suppliers = params["suppliers"]
            if isinstance(suppliers, list):
                filters["suppliers"] = [
                    s.value["code"] 
                    if hasattr(s, 'value') and isinstance(s.value, dict) 
                    else str(s) 
                    for s in suppliers
                ]
            else:
                supplier_value = (
                    suppliers.value["code"] 
                    if (hasattr(suppliers, 'value') and 
                        isinstance(suppliers.value, dict))
                    else str(suppliers)
                )
                filters["suppliers"] = [supplier_value]
        
        # Handle status - should be array of strings
        if params.get("status") is not None:
            status = params["status"]
            if isinstance(status, list):
                filters["status"] = [
                    s.value if (hasattr(s, 'value') and 
                                isinstance(s.value, str)) 
                    else str(s) 
                    for s in status
                ]
            else:
                if (hasattr(status, 'value') and
                        isinstance(status.value, str)):
                    status_value = status.value
                else:
                    status_value = str(status)
                filters["status"] = [status_value]
        
        # Handle sort - should be array of objects with field and dir
        if (
            params.get("sort_by") is not None or
            params.get("sort_order") is not None
        ):
            sort_field = params.get("sort_by", "name")
            sort_order = params.get("sort_order", "asc")
            
            # Convert enum to string if needed
            if hasattr(sort_field, 'value'):
                sort_field = sort_field.value
            
            # Convert sort order to integer
            if hasattr(sort_order, 'value'):
                sort_dir = sort_order.value
            else:
                sort_dir = 1 if str(sort_order).lower() == "asc" else -1
            
            filters["sort"] = [{"field": str(sort_field), "dir": sort_dir}]
        else:
            # Always include empty sort array as backend requires it
            filters["sort"] = [{}]
        
        return filters
