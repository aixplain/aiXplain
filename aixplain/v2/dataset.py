from .resource import (
    BaseResource,
    BaseCreateParams,
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    CreateResourceMixin,
)
from aixplain.factories import DatasetFactory
from aixplain.modules.metadata import MetaData
from .enums import DataType, Function, Language, License, Privacy, ErrorHandler
from pathlib import Path
from typing_extensions import Unpack, NotRequired
from typing import Any, Dict, List, Text, Union


class DatasetCreateParams(BaseCreateParams):
    name: Text
    description: Text
    license: License
    function: Function
    input_schema: List[Union[Dict, MetaData]]
    output_schema: List[Union[Dict, MetaData]] = []
    hypotheses_schema: List[Union[Dict, MetaData]] = []
    metadata_schema: List[Union[Dict, MetaData]] = []
    content_path: Union[Union[Text, Path], List[Union[Text, Path]]] = []
    input_ref_data: Dict[Text, Any] = {}
    output_ref_data: Dict[Text, List[Any]] = {}
    hypotheses_ref_data: Dict[Text, Any] = {}
    meta_ref_data: Dict[Text, Any] = {}
    tags: List[Text] = []
    privacy: Privacy = Privacy.PRIVATE
    split_labels: NotRequired[List[Text]]
    split_rate: NotRequired[List[float]]
    error_handler: ErrorHandler = ErrorHandler.SKIP
    s3_link: NotRequired[Text] = None
    aws_credentials: Dict[Text, Text] = {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None}
    api_key: NotRequired[Text]


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

    query: NotRequired[Text]
    function: NotRequired[Function]
    language: NotRequired[Union[Language, List[Language]]]
    data_type: NotRequired[DataType]
    license: NotRequired[License]
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
        kwargs.setdefault("page_number", 0)
        kwargs.setdefault("page_size", 20)
        return DatasetFactory.list(**kwargs)["results"]

    @classmethod
    def create(cls, **kwargs: Unpack[DatasetCreateParams]) -> Dict:
        kwargs.setdefault("output_schema", [])
        kwargs.setdefault("hypotheses_schema", [])
        kwargs.setdefault("metadata_schema", [])
        kwargs.setdefault("input_ref_data", {})
        kwargs.setdefault("output_ref_data", {})
        kwargs.setdefault("hypotheses_ref_data", {})
        kwargs.setdefault("meta_ref_data", {})
        kwargs.setdefault("tags", [])
        kwargs.setdefault("privacy", Privacy.PRIVATE)
        kwargs.setdefault("error_handler", ErrorHandler.SKIP)
        kwargs.setdefault("aws_credentials", {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None})
        return DatasetFactory.create(**kwargs)
