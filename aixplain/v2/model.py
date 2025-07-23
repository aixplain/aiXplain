from typing import Union, List, Optional, Any
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field

from .resource import (
    BaseListParams,
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    Page,
    RunnableResourceMixin,
    BareRunParams,
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
    """Parameters for listing models.

    Attributes:
        function: Function: The function of the model.
        suppliers: Union[Supplier, List[Supplier]: The suppliers of the model.
        source_languages: Union[Language, List[Language]: The source languages
            of the model.
        target_languages: Union[Language, List[Language]: The target languages
            of the model.
        is_finetunable: bool: Whether the model is finetunable.
    """

    function: NotRequired[Function]
    suppliers: NotRequired[Union[Supplier, List[Supplier]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]


class ModelRunParams(BareRunParams):
    """Parameters for running models.

    Attributes:
        data: Union[str, dict]: The input data for the model.
        context: str: System message or context.
        prompt: str: Prompt message.
        history: List[dict]: Conversation history.
        temperature: float: Model temperature.
        max_tokens: int: Maximum tokens to generate.
        top_p: float: Top-p sampling parameter.
        parameters: dict: Additional model parameters.
    """

    data: Union[str, dict]
    context: NotRequired[str]
    prompt: NotRequired[str]
    history: NotRequired[List[dict]]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    parameters: NotRequired[dict]


@dataclass_json
@dataclass
class Model(
    BaseResource,
    PagedListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
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
        return f"{self.context.MODELS_RUN_URL}/{self.id}"

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> Result:
        return super().run(**kwargs)
