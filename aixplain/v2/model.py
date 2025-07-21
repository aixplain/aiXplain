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
)
from .enums import Function, Supplier, Language, AssetStatus


def function_decoder(function_data: Union[str, dict]) -> Function:
    """Custom decoder for Function enum.
    
    Handles both string values and dictionary objects from the API.
    """
    if function_data is None:
        return None
    
    if isinstance(function_data, str):
        return Function(function_data)
    elif isinstance(function_data, dict):
        # API sometimes returns function as an object with id and name
        function_id = function_data.get("id")
        if function_id:
            return Function(function_id)
        else:
            raise ValueError(
                f"Function object missing 'id' field: {function_data}"
            )
    else:
        raise ValueError(
            f"Unexpected function data type: {type(function_data)}"
        )


def supplier_encoder(supplier: Supplier) -> str:
    """Custom encoder for Supplier enum."""
    if supplier is None:
        return None
    return supplier.value["code"]


def supplier_decoder(supplier_data: Union[str, dict]) -> Supplier:
    """Custom decoder for Supplier enum.
    
    Handles both string values and dictionary objects from the API.
    """
    if supplier_data is None:
        return None
    
    if isinstance(supplier_data, str):
        for supplier in Supplier:
            if supplier.value["code"] == supplier_data:
                return supplier
        raise ValueError(f"Unknown supplier code: {supplier_data}")
    elif isinstance(supplier_data, dict):
        # API sometimes returns supplier as an object with code, id, and name
        supplier_code = supplier_data.get("code")
        if supplier_code:
            for supplier in Supplier:
                if supplier.value["code"] == supplier_code:
                    return supplier
            raise ValueError(f"Unknown supplier code: {supplier_code}")
        else:
            raise ValueError(
                f"Supplier object missing 'code' field: {supplier_data}"
            )
    else:
        raise ValueError(
            f"Unexpected supplier data type: {type(supplier_data)}"
        )


def language_encoder(language: Language) -> dict:
    """Custom encoder for Language enum."""
    if language is None:
        return None
    return language.value


def language_decoder(language_dict: dict) -> Language:
    """Custom decoder for Language enum."""
    if language_dict is None:
        return None
    for language in Language:
        if (language.value["language"] == language_dict.get("language") and 
            language.value["dialect"] == language_dict.get("dialect", "")):
            return language
    raise ValueError(f"Unknown language: {language_dict}")


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


@dataclass_json
@dataclass
class Model(
    BaseResource,
    PagedListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
    RunnableResourceMixin[BareRunParams, Result],
):
    """Resource for models."""

    RESOURCE_PATH = "sdk/models"

    function: Optional[Function] = field(
        default=None,
        metadata=config(decoder=function_decoder)
    )
    supplier: Optional[Supplier] = field(
        default=None,
        metadata=config(
            encoder=supplier_encoder,
            decoder=supplier_decoder
        )
    )
    type: Optional[str] = None
    version: Optional[str] = None
    asset_id: Optional[str] = field(
        default=None,
        metadata=config(field_name="assetId")
    )
    parameters: Optional[List[Any]] = None
    status: Optional[AssetStatus] = None

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[BareRunParams]) -> Result:
        return super().run(**kwargs)
