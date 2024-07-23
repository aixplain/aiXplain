from dataclasses import dataclass, field, InitVar
from typing import List, Union, TYPE_CHECKING

from aixplain.factories import ModelFactory
from aixplain.factories.file_factory import FileFactory
from aixplain.factories.script_factory import ScriptFactory
from aixplain.enums.function import FunctionInputOutput

from .enums import (
    NodeType,
    DataType,
    AssetType,
    FunctionType,
    RouteType,
    Operation,
)
from .base import Node
from .mixins import LinkableMixin, RoutableMixin, OutputableMixin

if TYPE_CHECKING:
    from .pipeline import Pipeline


@dataclass
class Asset(Node, LinkableMixin, OutputableMixin):
    """
    Asset node class, this node will be used to fetch the asset from the
    aixplain platform and use it in the pipeline.

    `assetId` is required and will be used to fetch the asset from the
    aixplain platform.

    Input and output parameters will be automatically added based on the
    asset function spec.
    """

    assetId: str = None
    function: str = None
    supplier: str = None
    version: str = None
    assetType: AssetType = AssetType.MODEL
    functionType: FunctionType = FunctionType.AI
    instance: InitVar[any] = None

    type: NodeType = NodeType.ASSET

    def __post_init__(self, pipeline: "Pipeline" = None, instance: any = None):
        super().__post_init__(pipeline=pipeline)
        if not self.assetId and not self.instance:
            raise ValueError("assetId or instance is required")

        if not self.instance:
            instance = ModelFactory.get(self.assetId)

        function = FunctionInputOutput[instance.function.value]["spec"]
        self.function_spec = function
        self.function = instance.function.value
        self.supplier = instance.supplier.value["code"]
        self.version = instance.version
        self.instance = instance
        self.assetId = instance.id

        for item in function["params"]:
            self.add_input_param(code=item["code"], dataType=item["dataType"])

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
        if not self.dataType:
            self.dataType = [DataType.TEXT]

        self.add_output_param("input", self.dataType[0])

        if self.data:
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
        if not self.dataType:
            self.dataType = [DataType.TEXT]

        self.add_input_param("output", self.dataType[0])


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

    def __post_init__(
        self, pipeline: "Pipeline" = None, script_path: str = None
    ):
        super().__post_init__(pipeline=pipeline)
        if script_path:
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
        self.path = [
            node.number if isinstance(node, Node) else node
            for node in self.path
        ]


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


@dataclass
class Segmentor(Asset):
    """
    Segmentor node class, this node will be used to segment the input data
    into smaller fragments for much easier and efficient processing.
    """

    type: NodeType = NodeType.SEGMENTOR
    functionType: FunctionType = FunctionType.SEGMENTOR

    def __post_init__(self, pipeline: "Pipeline" = None, instance: any = None):
        super().__post_init__(pipeline=pipeline, instance=instance)
        self.add_output_param("audio", DataType.AUDIO)


@dataclass
class Reconstructor(Asset):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.RECONSTRUCTOR
    functionType: FunctionType = FunctionType.RECONSTRUCTOR
