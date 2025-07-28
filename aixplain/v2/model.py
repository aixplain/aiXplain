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
    ToolMixin,
)
from .enums import Function, Supplier, Language, AssetStatus, ToolType


def find_supplier_by_id(supplier_id: str) -> Optional[Supplier]:
    """Find supplier enum by ID."""
    for supplier in Supplier:
        if supplier.value.get("id") == supplier_id:
            return supplier
    return None


def find_function_by_id(function_id: str) -> Optional[Function]:
    """Find function enum by ID."""
    try:
        return Function(function_id)
    except ValueError:
        return None


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

    RESOURCE_PATH = "sdk/models"
    TOOL_TYPE = ToolType.MODEL

    function: Optional[Function] = field(
        default=None,
        metadata=config(
            decoder=lambda x: (
                find_function_by_id(x["id"]) if isinstance(x, dict) and "id" in x else x
            )
        ),
    )
    supplier: Optional[Supplier] = field(
        default=None,
        metadata=config(
            decoder=lambda x: (
                find_supplier_by_id(str(x["id"]))
                if isinstance(x, dict) and "id" in x
                else x
            )
        ),
    )
    version: Optional[str] = None
    asset_id: Optional[str] = field(default=None, metadata=config(field_name="assetId"))
    parameters: Optional[List[Any]] = None
    status: Optional[AssetStatus] = None

    def build_run_url(self, **kwargs: Unpack[ModelRunParams]) -> str:
        # Use api/v2/execute instead of api/v1/execute
        url = f"{self.context.model_url}/{self.id}"
        return url.replace("/api/v1/execute", "/api/v2/execute")

    @classmethod
    def get(cls: type["Model"], id: str, **kwargs: Unpack[BaseGetParams]) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls: type["Model"], **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> Result:
        return super().run(**kwargs)
