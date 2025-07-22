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
        """
        Build the URL for running the model.

        Uses the model execution URL structure:
        https://models.aixplain.com/api/v1/execute/{model_id}
        """
        if not self.id:
            raise ValueError("Run call requires an 'id' attribute")

        # Use the model execution URL from the context
        model_url = getattr(
            self.context, "model_url", "https://models.aixplain.com/api/v1/execute"
        )
        return f"{model_url}/{self.id}"

    def build_run_payload(self, **kwargs: Unpack[ModelRunParams]) -> dict:
        """
        Build the payload for running the model.

        Combines the data with additional parameters in the expected format.
        """
        data = kwargs.get("data", "")
        parameters = kwargs.get("parameters", {})

        # Extract model-specific parameters
        model_params = {}
        for key in [
            "context",
            "prompt",
            "history",
            "temperature",
            "max_tokens",
            "top_p",
        ]:
            if key in kwargs:
                model_params[key] = kwargs[key]

        # Combine all parameters
        all_params = {**model_params, **parameters}

        # If data is a dict, merge it with parameters
        if isinstance(data, dict):
            all_params = {**data, **all_params}
            data = data.get("data", "")

        return {"data": data, **all_params}

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> Result:
        return super().run(**kwargs)
