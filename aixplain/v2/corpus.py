from .resource import (
    BaseResource,
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
)
from aixplain.factories import CorpusFactory
from aixplain.modules.metadata import MetaData
from .enums import DataType, Function, Language, License, Privacy, ErrorHandler
from pathlib import Path
from typing_extensions import Unpack
from typing import Any, Dict, List, Optional, Text, Union


class CorpusListParams(BaseListParams):
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


class Corpus(
    BaseResource,
    ListResourceMixin[CorpusListParams, "Corpus"],
    GetResourceMixin[BareGetParams, "Corpus"],
):
    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Corpus":
        return CorpusFactory.get(corpus_id=kwargs["id"])

    @classmethod
    def list(cls, **kwargs: Unpack[CorpusListParams]) -> List["Corpus"]:
        return CorpusFactory.list(**kwargs)["results"]

    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        license: License,
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]],
        schema: List[Union[Dict, MetaData]],
        ref_data: List[Any] = [],
        tags: List[Text] = [],
        functions: List[Function] = [],
        privacy: Privacy = Privacy.PRIVATE,
        error_handler: ErrorHandler = ErrorHandler.SKIP,
        api_key: Optional[Text] = None,
    ) -> Dict:
        return CorpusFactory.create(
            name=name,
            description=description,
            license=license,
            content_path=content_path,
            schema=schema,
            ref_data=ref_data,
            tags=tags,
            functions=functions,
            privacy=privacy,
            error_handler=error_handler,
            api_key=api_key,
        )
