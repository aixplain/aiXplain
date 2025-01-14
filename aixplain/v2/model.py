from typing import Union, List
from typing_extensions import Unpack

from .resource import (
    BaseListParams,
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
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

    function: Function
    suppliers: Union[Supplier, List[Supplier]]
    source_languages: Union[Language, List[Language]]
    target_languages: Union[Language, List[Language]]
    is_finetunable: bool


class Model(
    BaseResource,
    ListResourceMixin[ModelListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
):
    """Resource for models."""

    RESOURCE_PATH = "sdk/models"

    @classmethod
    def list(cls, **kwargs: Unpack[ModelListParams]) -> List["Model"]:
        from aixplain.factories import ModelFactory

        return [Model(obj) for obj in ModelFactory.list(**kwargs)["results"]]

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Model":
        from aixplain.factories import ModelFactory

        return Model(ModelFactory.get(model_id=kwargs["id"]))
