from typing import Union, List
from typing_extensions import Unpack, NotRequired

from .resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    CreateResourceMixin,
    BaseCreateParams,
    Page,
)
from .enums import Function, Supplier, DataType
from .model import Model


class PipelineListParams(BareListParams):
    """Parameters for listing pipelines.

    Attributes:
        functions: Union[Function, List[Function]]: The functions of the pipeline.
        suppliers: Union[Supplier, List[Supplier]]: The suppliers of the pipeline.
        models: Union[Model, List[Model]]: The models of the pipeline.
        input_data_types: Union[DataType, List[DataType]]: The input data types of the pipeline.
        output_data_types: Union[DataType, List[DataType]]: The output data types of the pipeline.
        drafts_only: bool: Whether to list only drafts.
    """

    functions: NotRequired[Union[Function, List[Function]]]
    suppliers: NotRequired[Union[Supplier, List[Supplier]]]
    models: NotRequired[Union[Model, List[Model]]]
    input_data_types: NotRequired[Union[DataType, List[DataType]]]
    output_data_types: NotRequired[Union[DataType, List[DataType]]]
    drafts_only: NotRequired[bool]


class PipelineCreateParams(BaseCreateParams):
    name: str
    pipeline: Union[str, dict]
    api_key: NotRequired[str] = None


class Pipeline(
    BaseResource,
    ListResourceMixin[PipelineListParams, "Pipeline"],
    GetResourceMixin[BareGetParams, "Pipeline"],
    CreateResourceMixin[PipelineCreateParams, "Pipeline"],
):
    """Resource for pipelines.

    Attributes:
        RESOURCE_PATH: str: The resource path.
    """

    RESOURCE_PATH = "sdk/pipelines"

    @classmethod
    def list(cls, **kwargs: Unpack[PipelineListParams]) -> Page["Pipeline"]:
        from aixplain.factories import PipelineFactory

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        return PipelineFactory.list(**kwargs)

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Pipeline":
        from aixplain.factories import PipelineFactory

        return PipelineFactory.get(pipeline_id=id)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[PipelineCreateParams]) -> "Pipeline":
        from aixplain.factories import PipelineFactory
        from aixplain.utils import config

        kwargs.setdefault("api_key", config.TEAM_API_KEY)
        return PipelineFactory.create(*args, **kwargs)

    @classmethod
    def init(cls, name: str, api_key: str = None) -> "Pipeline":
        from aixplain.factories import PipelineFactory

        return PipelineFactory.init(name, api_key=api_key)
