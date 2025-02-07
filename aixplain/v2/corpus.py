from .resource import (
    BaseResource,
    BaseCreateParams,
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    Page,
)

from .enums import DataType, Function, Language, License, Privacy, ErrorHandler
from pathlib import Path
from typing_extensions import Unpack, NotRequired, TYPE_CHECKING
from typing import Any, Dict, List, Text, Union

if TYPE_CHECKING:
    from aixplain.modules.metadata import MetaData


class CorpusCreateParams(BaseCreateParams):
    name: Text
    description: Text
    license: License
    content_path: Union[Union[Text, Path], List[Union[Text, Path]]]
    schema: List[Union[Dict, "MetaData"]]
    ref_data: List[Any]
    tags: List[Text]
    functions: List[Function]
    privacy: Privacy
    error_handler: ErrorHandler
    api_key: NotRequired[Text]


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

    query: NotRequired[Text]
    function: NotRequired[Function]
    language: NotRequired[Union[Language, List[Language]]]
    data_type: NotRequired[DataType]
    license: NotRequired[License]
    page_number: int
    page_size: int


class Corpus(
    BaseResource,
    ListResourceMixin[CorpusListParams, "Corpus"],
    GetResourceMixin[BareGetParams, "Corpus"],
):
    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Corpus":
        from aixplain.factories import CorpusFactory

        return CorpusFactory.get(corpus_id=id)

    @classmethod
    def list(cls, **kwargs: Unpack[CorpusListParams]) -> Page["Corpus"]:
        from aixplain.factories import CorpusFactory

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        return CorpusFactory.list(**kwargs)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[CorpusCreateParams]) -> Dict:
        from aixplain.factories import CorpusFactory

        kwargs.setdefault("ref_data", [])
        kwargs.setdefault("tags", [])
        kwargs.setdefault("functions", [])
        kwargs.setdefault("privacy", Privacy.PRIVATE)
        kwargs.setdefault("error_handler", ErrorHandler.SKIP)
        return CorpusFactory.create(*args, **kwargs)
