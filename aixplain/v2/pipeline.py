from typing import Optional, Union, List

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
        functions: Optional[Union[Function, List[Function]]]: The functions of the pipeline.
        suppliers: Optional[Union[Supplier, List[Supplier]]]: The suppliers of the pipeline.
        models: Optional[Union[Model, List[Model]]]: The models of the pipeline.
        input_data_types: Optional[Union[DataType, List[DataType]]]: The input data types of the pipeline.
        output_data_types: Optional[Union[DataType, List[DataType]]]: The output data types of the pipeline.
        drafts_only: bool: Whether to list only drafts.
    """

    functions: Optional[Union[Function, List[Function]]] = None
    suppliers: Optional[Union[Supplier, List[Supplier]]] = None
    models: Optional[Union[Model, List[Model]]] = None
    input_data_types: Optional[Union[DataType, List[DataType]]] = None
    output_data_types: Optional[Union[DataType, List[DataType]]] = None
    drafts_only: bool = False


class Pipeline(
    BaseResource,
    ListResourceMixin[PipelineListParams],
    GetResourceMixin[BareGetParams],
    CreateResourceMixin[BareCreateParams],
):
    """Resource for pipelines.

    Attributes:
        RESOURCE_PATH: str: The resource path.
    """

    RESOURCE_PATH = "sdk/pipelines"

    @classmethod
    def list(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.list(**kwargs)["results"]

    @classmethod
    def get(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.get(pipeline_id=kwargs["id"])

    @classmethod
    def create(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.init(**kwargs)
