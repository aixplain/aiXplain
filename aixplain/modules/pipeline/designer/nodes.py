from dataclasses import dataclass, field, InitVar
from typing import List, Union, TYPE_CHECKING

from aixplain.enums.function import FunctionInputOutput
from aixplain.modules.asset import Asset as AssetInstance

from .enums import (
    NodeType,
    DataType,
    AssetType,
    FunctionType,
    RouteType,
    Operation,
)
from .base import Node, Link, Param
from .mixins import LinkableMixin, RoutableMixin, OutputableMixin

if TYPE_CHECKING:
    from aixplain.modules.pipeline import Pipeline


@dataclass
class NodeAsset(Node, LinkableMixin, OutputableMixin):
    """
    Asset node class, this node will be used to fetch the asset from the
    aixplain platform and use it in the pipeline.

    `assetId` is required and will be used to fetch the asset from the
    aixplain platform.

    Input and output parameters will be automatically added based on the
    asset function spec.
    """

    assetId: Union[AssetInstance, str] = None
    function: str = None
    supplier: str = None
    version: str = None
    assetType: AssetType = AssetType.MODEL
    functionType: FunctionType = FunctionType.AI

    type: NodeType = NodeType.ASSET

    def __post_init__(self, pipeline: "Pipeline" = None, instance: any = None):
        from aixplain.factories import ModelFactory

        super().__post_init__(pipeline=pipeline)

        if isinstance(self.assetId, str):
            self.asset = ModelFactory.get(self.assetId)
        elif isinstance(self.assetId, AssetInstance):
            self.asset = self.assetId
            self.assetId = self.assetId.id
        else:
            raise ValueError("assetId should be a string or an AssetInstance")

        function = FunctionInputOutput[self.asset.function.value]["spec"]
        self.function_spec = function
        self.function = self.asset.function.value
        try:
            self.supplier = self.asset.supplier.value["code"]
        except Exception:
            self.supplier = self.asset.supplier
        self.version = self.asset.version

        for item in function["params"]:
            self.add_input_param(
                code=item["code"],
                dataType=item["dataType"],
                is_required=item["required"],
                value=self.asset.additional_info["parameters"].get(item["code"]),
            )

        for item in function["output"]:
            self.add_output_param(code=item["code"], dataType=item["dataType"])


@dataclass
class Input(Node, LinkableMixin, RoutableMixin):
    """
    Input node class, this node will be used to input the data to the
    pipeline.

    Input nodes has only one output parameter called `input`.

    `data` is a special convenient parameter that will be uploaded to the
    aixplain platform and the link will be passed as the input to the node.
    """

    dataType: List[DataType] = field(default_factory=list)
    data: str = None
    type: NodeType = NodeType.INPUT

    def __post_init__(self, pipeline: "Pipeline" = None):
        super().__post_init__(pipeline=pipeline)
        self.add_output_param("input", None)

        if self.data:
            from aixplain.factories.file_factory import FileFactory

            self.data = FileFactory.to_link(self.data, is_temp=True)


@dataclass
class Output(Node):
    """
    Output node class, this node will be used to output the result of the
    pipeline.

    Output nodes has only one input parameter called `output`.
    """

    dataType: List[DataType] = field(default_factory=list)
    type: NodeType = NodeType.OUTPUT

    def __post_init__(self, pipeline: "Pipeline" = None):
        super().__post_init__(pipeline=pipeline)
        self.add_input_param("output", None)


@dataclass
class Script(Node, LinkableMixin, OutputableMixin):
    """
    Script node class, this node will be used to run a script on the input
    data.

    `script_path` is a special convenient parameter that will be uploaded to
    the aixplain platform and the link will be passed as the input to the node.
    """

    fileId: str = None
    script_path: InitVar[str] = None
    type: NodeType = NodeType.SCRIPT

    def __post_init__(self, pipeline: "Pipeline" = None, script_path: str = None):
        super().__post_init__(pipeline=pipeline)
        if script_path:
            from aixplain.factories.script_factory import ScriptFactory

            self.fileId, _ = ScriptFactory.upload_script(script_path)
        if not self.fileId:
            raise ValueError("fileId is required")


@dataclass
class Route:
    """
    Route class, this class will be used to route the input data to different
    nodes based on the input data type.
    """

    value: DataType
    path: List[Union[Node, int]] = field(default_factory=list)
    operation: Operation = None
    type: RouteType = None

    def __post_init__(self):
        """
        Post init method to convert the nodes to node numbers if they are
        nodes.
        """
        # convert nodes to node numbers if they are nodes
        self.path = [node.number if isinstance(node, Node) else node for node in self.path]


@dataclass
class Router(Node, LinkableMixin):
    """
    Router node class, this node will be used to route the input data to
    different nodes based on the input data type.
    """

    routes: List[Route] = field(default_factory=list)
    type: NodeType = NodeType.ROUTER

    def __post_init__(self, pipeline: "Pipeline" = None):
        super().__post_init__(pipeline=pipeline)
        self.add_input_param("input", None)
        self.add_output_param("input", None)


@dataclass
class Decision(Router):
    """
    Decision node class, this node will be used to make decisions based on
    the input data.
    """

    type: NodeType = NodeType.DECISION

    def __post_init__(self, pipeline: "Pipeline" = None):
        super().__post_init__(pipeline=pipeline)
        self.add_input_param("comparison", None)
        self.add_input_param("passthrough", None)

    def link(
        self,
        to_node: Node,
        from_param: Union[str, Param],
        to_param: Union[str, Param],
    ) -> Link:
        link = super().link(to_node, from_param, to_param)
        self.outputs.input.dataType = self.inputs.passthrough.dataType
        return link


@dataclass
class Segmentor(NodeAsset):
    """
    Segmentor node class, this node will be used to segment the input data
    into smaller fragments for much easier and efficient processing.
    """

    type: NodeType = NodeType.SEGMENTOR
    functionType: FunctionType = FunctionType.SEGMENTOR

    def __post_init__(self, pipeline: "Pipeline" = None):
        super().__post_init__(pipeline=pipeline)
        self.add_output_param("audio", DataType.AUDIO)


@dataclass
class Reconstructor(NodeAsset):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.RECONSTRUCTOR
    functionType: FunctionType = FunctionType.RECONSTRUCTOR
