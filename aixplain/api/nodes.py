from typing import List, Union, Type, TYPE_CHECKING

from aixplain.factories.file_factory import FileFactory
from aixplain.factories.script_factory import ScriptFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules import asset

from .enums import (
    NodeType,
    FunctionType,
    RouteType,
    Operation,
    AssetType,
)
from .base import (
    Node,
    Link,
    Param,
    InputParam,
    OutputParam,
    TI,
    TO,
    Inputs,
    Outputs,
    Serializable,
)
from .mixins import LinkableMixin, OutputableMixin, RoutableMixin

if TYPE_CHECKING:
    from .pipeline_base import BasePipeline as Pipeline
    from .pipeline import DataType


class Asset(Node[TI, TO], LinkableMixin, OutputableMixin):
    """
    Asset node class, this node will be used to fetch the asset from the
    aixplain platform and use it in the pipeline.

    `assetId` is required and will be used to fetch the asset from the
    aixplain platform.

    Input and output parameters will be automatically added based on the
    asset function spec.
    """

    assetId: Union[asset.Asset, str] = None
    function: str = None
    supplier: str = None
    version: str = None
    assetType: AssetType = AssetType.MODEL
    functionType: FunctionType = FunctionType.AI

    type: NodeType = NodeType.ASSET

    def __init__(
        self,
        assetId: Union[asset.Asset, str] = None,
        supplier: str = None,
        version: str = None,
        pipeline: "Pipeline" = None,
    ):
        super().__init__(pipeline=pipeline)
        self.assetId = assetId
        self.supplier = supplier
        self.version = version

        if not self.assetId:
            return

        if isinstance(self.assetId, str):
            self.asset = ModelFactory.get(self.assetId)
        elif isinstance(self.assetId, asset.Asset):
            self.asset = self.assetId
            self.assetId = self.assetId.id
        else:
            raise ValueError("assetId should be a string or an Asset instance")

        self.supplier = self.asset.supplier.value["code"]
        self.version = self.asset.version

        self._auto_set_params()
        self.validate_asset()

    def validate_asset(self):
        if self.asset.function.value != self.function:
            raise ValueError(
                f"Function {self.function} is not supported by asset {self.assetId}"  # noqa
            )

    def _auto_set_params(self):
        for k, v in self.asset.additional_info["parameters"].items():
            if isinstance(v, list):
                self.inputs[k] = v[0]
            else:
                self.inputs[k] = v

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["function"] = self.function
        obj["assetId"] = self.assetId
        obj["supplier"] = self.supplier
        obj["version"] = self.version
        obj["assetType"] = self.assetType
        obj["functionType"] = self.functionType
        obj["type"] = self.type
        return obj


class InputInputs(Inputs):
    pass


class InputOutputs(Outputs):
    input: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.input = self.create_param("input")


class Input(Node[InputInputs, InputOutputs], LinkableMixin, RoutableMixin):
    """
    Input node class, this node will be used to input the data to the
    pipeline.

    Input nodes has only one output parameter called `input`.

    `data` is a special convenient parameter that will be uploaded to the
    aixplain platform and the link will be passed as the input to the node.
    """

    data_types: List["DataType"] = None
    data: str = None
    type: NodeType = NodeType.INPUT
    inputs_class: Type[TI] = InputInputs
    outputs_class: Type[TO] = InputOutputs

    def __init__(self, pipeline: "Pipeline" = None):
        super().__init__(pipeline=pipeline)
        self.data_types = []
        if self.data:
            self.data = FileFactory.to_link(self.data, is_temp=True)

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["data"] = self.data
        obj["dataType"] = self.data_types
        return obj


class OutputInputs(Inputs):
    output: InputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.output = self.create_param("output")


class OutputOutputs(Outputs):
    pass


class Output(Node[OutputInputs, OutputOutputs]):
    """
    Output node class, this node will be used to output the result of the
    pipeline.

    Output nodes has only one input parameter called `output`.
    """

    data_types: List["DataType"] = None
    type: NodeType = NodeType.OUTPUT
    inputs_class: Type[TI] = OutputInputs
    outputs_class: Type[TO] = OutputOutputs

    def __init__(self, pipeline: "Pipeline" = None):
        super().__init__(pipeline=pipeline)
        self.data_types = []

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["dataType"] = self.data_types
        return obj


class Script(Node[TI, TO], LinkableMixin, OutputableMixin):
    """
    Script node class, this node will be used to run a script on the input
    data.

    `script_path` is a special convenient parameter that will be uploaded to
    the aixplain platform and the link will be passed as the input to the node.
    """

    fileId: str = None
    script_path: str = None
    type: NodeType = NodeType.SCRIPT

    def __init__(self, pipeline: "Pipeline" = None, script_path: str = None):
        super().__init__(pipeline=pipeline)
        if script_path:
            self.fileId, _ = ScriptFactory.upload_script(script_path)
        if not self.fileId:
            raise ValueError("fileId is required")

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["fileId"] = self.fileId
        return obj


class Route(Serializable):
    """
    Route class, this class will be used to route the input data to different
    nodes based on the input data type.
    """

    value: "DataType"
    path: List[Union[Node, int]]
    operation: Operation
    type: RouteType

    def __init__(
        self,
        value: "DataType",
        path: List[Union[Node, int]],
        operation: Operation,
        type: RouteType,
    ):
        """
        Post init method to convert the nodes to node numbers if they are
        nodes.
        """
        self.value = value
        self.path = path
        self.operation = operation
        self.type = type

        if not self.path:
            raise ValueError("Path is not valid, should be a list of nodes")

        # convert nodes to node numbers if they are nodes
        self.path = [
            node.number if isinstance(node, Node) else node
            for node in self.path
        ]

    def serialize(self) -> dict:
        return {
            "value": self.value,
            "path": self.path,
            "operation": self.operation,
            "type": self.type,
        }


class RouterInputs(Inputs):
    input: InputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.input = self.create_param("input")


class RouterOutputs(Outputs):
    input: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.input = self.create_param("input")


class Router(Node[RouterInputs, RouterOutputs], LinkableMixin):
    """
    Router node class, this node will be used to route the input data to
    different nodes based on the input data type.
    """

    routes: List[Route] = None
    type: NodeType = NodeType.ROUTER
    inputs_class: Type[TI] = RouterInputs
    outputs_class: Type[TO] = RouterOutputs

    def __init__(self, routes: List[Route], pipeline: "Pipeline" = None):
        super().__init__(pipeline=pipeline)
        self.routes = routes

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["routes"] = [route.serialize() for route in self.routes]
        return obj


class DecisionInputs(Inputs):
    comparison: InputParam = None
    passthrough: InputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.comparison = self.create_param("comparison")
        self.passthrough = self.create_param("passthrough")


class DecisionOutputs(Outputs):
    input: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.input = self.create_param("input")


class Decision(Node[DecisionInputs, DecisionOutputs], LinkableMixin):
    """
    Decision node class, this node will be used to make decisions based on
    the input data.
    """

    routes: List[Route] = None
    type: NodeType = NodeType.DECISION
    inputs_class: Type[TI] = DecisionInputs
    outputs_class: Type[TO] = DecisionOutputs

    def __init__(self, routes: List[Route], pipeline: "Pipeline" = None):
        super().__init__(pipeline=pipeline)
        self.routes = routes

    def link(
        self,
        to_node: Node,
        from_param: Union[str, Param],
        to_param: Union[str, Param],
    ) -> Link:
        link = super().link(to_node, from_param, to_param)
        self.outputs.input.data_type = self.inputs.passthrough.data_type
        return link

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["routes"] = [route.serialize() for route in self.routes]
        return obj


class BaseSegmentor(Asset[TI, TO]):
    """
    Segmentor node class, this node will be used to segment the input data
    into smaller fragments for much easier and efficient processing.
    """

    type: NodeType = NodeType.SEGMENTOR
    functionType: FunctionType = FunctionType.SEGMENTOR


class SegmentorInputs(Inputs):
    pass


class SegmentorOutputs(Outputs):
    audio: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.audio = self.create_param("audio")


class BareSegmentor(BaseSegmentor[SegmentorInputs, SegmentorOutputs]):
    """
    Segmentor node class, this node will be used to segment the input data
    into smaller fragments for much easier and efficient processing.
    """

    type: NodeType = NodeType.SEGMENTOR
    functionType: FunctionType = FunctionType.SEGMENTOR
    inputs_class: Type[TI] = SegmentorInputs
    outputs_class: Type[TO] = SegmentorOutputs


class BaseReconstructor(Asset[TI, TO]):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.RECONSTRUCTOR
    functionType: FunctionType = FunctionType.RECONSTRUCTOR


class ReconstructorInputs(Inputs):
    data: InputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.data = self.create_param("data")


class ReconstructorOutputs(Outputs):
    data: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.data = self.create_param("data")


class BareReconstructor(
    BaseReconstructor[ReconstructorInputs, ReconstructorOutputs]
):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.RECONSTRUCTOR
    functionType: FunctionType = FunctionType.RECONSTRUCTOR
    inputs_class: Type[TI] = ReconstructorInputs
    outputs_class: Type[TO] = ReconstructorOutputs