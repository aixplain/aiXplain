from typing import Union, List
from typing_extensions import NotRequired, Unpack
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
from .enums import Function, Supplier, Language


class ModelListParams(BaseListParams):
    """Parameters for listing models.

    Attributes:
        function: Function: The function of the model.
        suppliers: Union[Supplier, List[Supplier]: The suppliers of the model.
        source_languages: Union[Language, List[Language]: The source languages of the model.
        target_languages: Union[Language, List[Language]: The target languages of the model.
        is_finetunable: bool: Whether the model is finetunable.
    """

    function: NotRequired[Function]
    suppliers: NotRequired[Union[Supplier, List[Supplier]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]


class Model(
    BaseResource,
    PagedListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
    RunnableResourceMixin[BareRunParams, Result],
):
    """Resource for models."""

    RESOURCE_PATH = "sdk/models"

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Model":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> Page["Model"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[BareRunParams]) -> Result:
        return super().run(**kwargs)
