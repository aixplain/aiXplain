from typing import Optional, Union, List

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
        function: Optional[Function]: The function of the model.
        suppliers: Optional[Union[Supplier, List[Supplier]]]: The suppliers of the model.
        source_languages: Optional[Union[Language, List[Language]]]: The source languages of the model.
        target_languages: Optional[Union[Language, List[Language]]]: The target languages of the model.
        is_finetunable: Optional[bool]: Whether the model is finetunable.
    """

    function: Optional[Function] = None
    suppliers: Optional[Union[Supplier, List[Supplier]]] = None
    source_languages: Optional[Union[Language, List[Language]]] = None
    target_languages: Optional[Union[Language, List[Language]]] = None
    is_finetunable: Optional[bool] = None


class Model(
    BaseResource, ListResourceMixin[ModelListParams], GetResourceMixin[BareGetParams]
):
    """Resource for models.

    Attributes:
        RESOURCE_PATH: str: The resource path.
    """

    RESOURCE_PATH = "sdk/models"

    @classmethod
    def list(cls, **kwargs):
        from aixplain.factories import ModelFactory

        return ModelFactory.list(**kwargs)["results"]

    @classmethod
    def get(cls, **kwargs):
        from aixplain.factories import ModelFactory

        return ModelFactory.get(model_id=kwargs["id"])
