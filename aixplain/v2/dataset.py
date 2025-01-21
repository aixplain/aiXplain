from .resource import (
    BaseResource,
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    CreateResourceMixin,
    BareCreateParams,
)
from aixplain.factories import DatasetFactory
from aixplain.modules.metadata import MetaData
from .enums import DataType, Function, Language, License, Privacy, ErrorHandler
from pathlib import Path
from typing_extensions import Unpack
from typing import Any, Dict, List, Optional, Text, Union


class DatasetListParams(BaseListParams):
    """Parameters for listing corpora.

    Attributes:
        query: Optional[Text]: A search query.
        function: Optional[Function]: The function of the model.
        suppliers: Union[Supplier, List[Supplier]: The suppliers of the model.
        source_languages: Union[Language, List[Language]: The source languages of the model.
        target_languages: Union[Language, List[Language]: The target languages of the model.
        is_finetunable: bool: Whether the model is finetunable.
    """

    query: Optional[Text] = None
    function: Optional[Function] = None
    language: Optional[Union[Language, List[Language]]] = None
    data_type: Optional[DataType] = None
    license: Optional[License] = None
    page_number: int = 0
    page_size: int = 20


class Dataset(
    BaseResource,
    ListResourceMixin[DatasetListParams, "Dataset"],
    GetResourceMixin[BareGetParams, "Dataset"],
    CreateResourceMixin[Dict, "Dataset"],
):
    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Dataset":
        return DatasetFactory.get(dataset_id=kwargs["id"])

    @classmethod
    def list(cls, **kwargs: Unpack[DatasetListParams]) -> List["Dataset"]:
        return DatasetFactory.list(**kwargs)["results"]

    @classmethod
    def create(cls, **kwargs: Unpack[BareCreateParams]) -> "Dataset":

        return Dataset(DatasetFactory.init(**kwargs))