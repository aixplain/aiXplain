from typing import Union, List
from typing_extensions import Unpack

from .resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    CreateResourceMixin,
    BareCreateParams,
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

    functions: Union[Function, List[Function]] = None
    suppliers: Union[Supplier, List[Supplier]] = None
    models: Union[Model, List[Model]] = None
    input_data_types: Union[DataType, List[DataType]] = None
    output_data_types: Union[DataType, List[DataType]] = None
    drafts_only: bool = False


class Pipeline(
    BaseResource,
    ListResourceMixin[PipelineListParams, "Pipeline"],
    GetResourceMixin[BareGetParams, "Pipeline"],
    CreateResourceMixin[BareCreateParams, "Pipeline"],
):
    """Resource for pipelines.

    Attributes:
        RESOURCE_PATH: str: The resource path.
    """

    RESOURCE_PATH = "sdk/pipelines"

    @classmethod
    def list(cls, **kwargs: Unpack[PipelineListParams]) -> List["Pipeline"]:
        from aixplain.factories import PipelineFactory

        return [Pipeline(obj) for obj in PipelineFactory.list(**kwargs)["results"]]

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Pipeline":
        from aixplain.factories import PipelineFactory

        return Pipeline(PipelineFactory.get(pipeline_id=kwargs["id"]))

    @classmethod
    def create(cls, **kwargs: Unpack[BareCreateParams]) -> "Pipeline":
        from aixplain.factories import PipelineFactory

        return Pipeline(PipelineFactory.init(**kwargs))
