from .resource import (
    BaseResource,
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
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
):
    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Dataset":
        return DatasetFactory.get(dataset_id=kwargs["id"])

    @classmethod
    def list(cls, **kwargs: Unpack[DatasetListParams]) -> List["Dataset"]:
        return DatasetFactory.list(**kwargs)["results"]

    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        license: License,
        function: Function,
        input_schema: List[Union[Dict, MetaData]],
        output_schema: List[Union[Dict, MetaData]] = [],
        hypotheses_schema: List[Union[Dict, MetaData]] = [],
        metadata_schema: List[Union[Dict, MetaData]] = [],
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]] = [],
        input_ref_data: Dict[Text, Any] = {},
        output_ref_data: Dict[Text, List[Any]] = {},
        hypotheses_ref_data: Dict[Text, Any] = {},
        meta_ref_data: Dict[Text, Any] = {},
        tags: List[Text] = [],
        privacy: Privacy = Privacy.PRIVATE,
        split_labels: Optional[List[Text]] = None,
        split_rate: Optional[List[float]] = None,
        error_handler: ErrorHandler = ErrorHandler.SKIP,
        s3_link: Optional[Text] = None,
        aws_credentials: Optional[Dict[Text, Text]] = {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None},
        api_key: Optional[Text] = None,
    ) -> Dict:
        return DatasetFactory.create(
            name=name,
            description=description,
            license=license,
            function=function,
            input_schema=input_schema,
            output_schema=output_schema,
            hypotheses_schema=hypotheses_schema,
            metadata_schema=metadata_schema,
            content_path=content_path,
            input_ref_data=input_ref_data,
            output_ref_data=output_ref_data,
            hypotheses_ref_data=hypotheses_ref_data,
            meta_ref_data=meta_ref_data,
            tags=tags,
            privacy=privacy,
            split_labels=split_labels,
            split_rate=split_rate,
            error_handler=error_handler,
            s3_link=s3_link,
            aws_credentials=aws_credentials,
            api_key=api_key,
        )
