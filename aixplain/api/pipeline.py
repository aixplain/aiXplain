import uuid
from dataclasses import dataclass, field, InitVar, asdict
from typing import List, Tuple, Union

from aixplain.factories import ModelFactory
from aixplain.factories.pipeline_factory import PipelineFactory
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
from .base import Node, Link
from .mixins import LinkableMixin, RoutableMixin, OutputableMixin


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


@dataclass
class Pipeline:
    nodes: List[Node] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    instance: InitVar[any] = None

    def add_node(self, node: Node):
        """
        Add a node to the current pipeline.

        This method will take care of setting the pipeline instance to the
        node and setting the node number if it's not set.

        :param node: the node
        :return: the node
        """
        return node.attach(self)

    def add_nodes(self, *nodes: Node) -> List[Node]:
        """
        Add multiple nodes to the current pipeline.

        :param nodes: the nodes
        :return: the nodes
        """
        return [self.add_node(node) for node in nodes]

    def add_link(self, link: Link) -> Link:
        """
        Add a link to the current pipeline.
        :param link: the link
        :return: the link
        """
        return link.attach(self)

    def input(self, data: str = None, *args, **kwargs) -> Node:
        """
        Shortcut to create an input node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        `data` is a special convenient parameter that will be uploaded to the
        aixplain platform and the link will be passed as the input to the node.

        :param data: the data to be uploaded
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        kwargs["data"] = data
        return Input(self, *args, **kwargs)

    def asset(self, assetId: str, *args, **kwargs) -> Node:
        """
        Shortcut to create an asset node for the current pipeline.
        The asset id is required and will be passed as a keyword argument
        to the node constructor. All other params will be passed as keyword
        arguments to the node constructor.

        assetId will be used to fetch the asset from the aixplain platform.

        :example:
        >>> my_asset = pipeline.asset("60ddefae8d38c51c5885eff7")
        >>> print(my_asset.supplier)
        "openai"

        :param assetId: the asset id
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        kwargs["assetId"] = assetId
        return Asset(self, *args, **kwargs)

    def segmentor(self, assetId: str, *args, **kwargs) -> Node:
        """
        Shortcut to create an segmentor node for the current pipeline.
        The asset id is required and will be passed as a keyword argument
        to the node constructor. All other params will be passed as keyword
        arguments to the node constructor.

        assetId will be used to fetch the segmentor asset from the aixplain
        platform.

        :param assetId: the asset id
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        kwargs["assetId"] = assetId
        return Segmentor(self, *args, **kwargs)

    def reconstructor(self, assetId: str, *args, **kwargs) -> Node:
        """
        Shortcut to create an reconstructor node for the current pipeline.
        The asset id is required and will be passed as a keyword argument
        to the node constructor. All other params will be passed as keyword
        arguments to the node constructor.

        assetId will be used to fetch the reconstructor asset from the aixplain
        platform.

        :param assetId: the asset id
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        kwargs["assetId"] = assetId
        return Reconstructor(self, *args, **kwargs)

    def script(self, *args, **kwargs) -> Script:
        """
        Shortcut to create an script node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return Script(self, *args, **kwargs)

    def output(self, *args, **kwargs) -> Output:
        """
        Shortcut to create an output node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return Output(self, *args, **kwargs)

    def decision(self, *args, **kwargs) -> Node:
        """
        Shortcut to create an decision node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return Decision(self, *args, **kwargs)

    def router(self, routes: Tuple[DataType, Node], *args, **kwargs) -> Node:
        """
        Shortcut to create an decision node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor. The routes will be handled specially and will be
        converted to Route instances in a convenient way.

        :param routes: the routes
        :param kwargs: keyword arguments
        :return: the node
        """
        kwargs["routes"] = [
            Route(
                value=route[0],
                path=[route[1]],
                type=RouteType.CHECK_TYPE,
                operation=Operation.EQUAL,
            )
            for route in routes
        ]
        return Router(
            self,
            *args,
            **kwargs,
        )

    def to_dict(self) -> dict:
        """
        Convert the pipeline to a dictionary. This method will convert the
        pipeline to a dictionary and will replace the node instances with
        their numbers.

        :return: the pipeline as a dictionary
        """
        obj = asdict(self)
        for link in obj["links"]:
            link["from"] = link.pop("from_node")
            link["to"] = link.pop("to_node")
            params = link.get("paramMapping", []) or []
            for param in params:
                param["from"] = param.pop("from_param")
                param["to"] = param.pop("to_param")
        return obj

    def validate(self) -> bool:
        """
        Validate the pipeline. This method will check if all input nodes are
        linked to output nodes and all output nodes are linked to input nodes.

        :raises ValueError: if the pipeline is not valid
        """
        link_from_map = {link.from_node: link for link in self.links}
        link_to_map = {link.to_node: link for link in self.links}
        for node in self.nodes:
            # validate every input node is linked out
            if node.type == NodeType.INPUT:
                if node.number not in link_from_map:
                    raise ValueError(f"Input node {node.label} not linked out")
            # validate every output node is linked in
            elif node.type == NodeType.OUTPUT:
                if node.number not in link_to_map:
                    raise ValueError(f"Output node {node.label} not linked in")
            # validate rest of the nodes are linked in and out
            else:
                if node.number not in link_from_map:
                    raise ValueError(f"Node {node.label} not linked in")
                if node.number not in link_to_map:
                    raise ValueError(f"Node {node.label} not linked out")

    def save(self) -> "Pipeline":
        """
        Save the pipeline to able to run it later. This method will first
        validate the pipeline and then save it to the aixplain platform.

        :return: the pipeline instance
        """
        self.validate()

        name = f"pipeline-{uuid.uuid4()}"
        self.instance = PipelineFactory.create(name, self.to_dict())
        return self

    def run(self, *args, **kwargs) -> any:
        """
        Run the pipeline with the given inputs
        All params will be passed as keyword arguments to the pipeline
        model run method created by the pipeline factory.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the output of the pipeline
        """
        if not self.instance:
            raise ValueError("Pipeline not saved")

        return self.instance.run(*args, **kwargs)
