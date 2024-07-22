import uuid

from enum import Enum
from dataclasses import dataclass, field, asdict, InitVar
from typing import Any, List, Tuple, Union

# these are commented out because of circular imports, please fix it
# "any" is used to avoid circular imports, should be replaced with the correct
# type once the circular imports are fixed

# from aixplain.modules import Model
# from aixplain.modules import Dataset
# from aixplain.modules import Pipeline

from aixplain.factories import ModelFactory
from aixplain.factories import PipelineFactory
from aixplain.factories.file_factory import FileFactory
from aixplain.factories.script_factory import ScriptFactory
from aixplain.enums.function import FunctionInputOutput


class DataType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    LABEL = "label"


class RouteType(str, Enum):
    CHECK_TYPE = "checkType"
    CHECK_VALUE = "checkValue"


class Operation(str, Enum):
    GREATER_THAN = "greaterThan"
    GREATER_THAN_OR_EQUAL = "greaterThanOrEqual"
    LESS_THAN = "lessThan"
    LESS_THAN_OR_EQUAL = "lessThanOrEqual"
    EQUAL = "equal"
    DIFFERENT = "different"


class NodeType(str, Enum):
    ASSET = "ASSET"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    SCRIPT = "SCRIPT"
    SEGMENTOR = "SEGMENTOR"
    RECONSTRUCTOR = "RECONSTRUCTOR"
    ROUTER = "ROUTER"
    DECISION = "DECISION"


class AssetType(str, Enum):
    MODEL = "MODEL"


class FunctionType(str, Enum):
    AI = "AI"
    SEGMENTOR = "SEGMENTOR"
    RECONSTRUCTOR = "RECONSTRUCTOR"


@dataclass
class Param:
    """
    Param class, this class will be used to create the parameters of the node.
    """

    code: str
    dataType: DataType
    value: str
    node: InitVar["Node"] = None

    def __post_init__(self, node: "Node" = None):
        """
        Post init method to set the node of the param.
        """
        self.node = node

    def link(self, to_param: "Param") -> "Param":
        """
        Link the output of the param to the input of another param.
        :param to_param: the input param
        :return: the param
        """
        assert self.node, "Param not added to a node"
        to_param.back_link(self)

    def back_link(self, from_param: "Param") -> "Param":
        """
        Link the input of the param to the output of another param.
        :param from_param: the output param
        :return: the param
        """
        assert self.node, "Param not added to a node"
        from_param.node.link(self.node, from_param.code, self.code)


@dataclass
class ParamMapping:
    """
    Param mapping class, this class will be used to map the output of the
    node to the input of another node.
    """

    from_param: Union[str, Param]
    to_param: Union[str, Param]

    def __post_init__(self):
        """
        Post init method to convert the params to param codes if they are
        params.
        """
        if isinstance(self.from_param, Param):
            self.from_param = self.from_param.code
        if isinstance(self.to_param, Param):
            self.to_param = self.to_param.code


@dataclass
class Link:
    """
    Link class, this class will be used to link the output of the node to the
    input of another node.
    """

    from_node: int
    to_node: int
    paramMapping: List[ParamMapping] = field(default_factory=list)


@dataclass
class Route:
    """
    Route class, this class will be used to route the input data to different
    nodes based on the input data type.
    """

    value: DataType
    path: List[Union["Node", int]] = field(default_factory=list)
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


class ParamProxy:
    """
    Param proxy class, this class will be used to get and set the parameters
    of the node.
    """

    def __init__(self, params: List[Param]):
        """
        Initialize the param proxy with the parameters of the node.
        :param params: the parameters of the node
        """
        self.params = params

    def get_param(self, code: str) -> Param:
        """
        Get the parameter by code. This method will get the parameter by code.
        :param code: the code of the parameter
        :return: the parameter
        """
        for param in self.params:
            if param.code == code:
                return param
        raise ValueError(f"Param {code} not found")

    def set_param(self, code: str, value: any) -> None:
        """
        Set the parameter value by code. This method will set the parameter
        value by code.
        :param code: the code of the parameter
        :param value: the value of the parameter
        """
        param = self.get_param(code)
        param.value = value

    def __call__(self, code: str) -> Param:
        """
        This is a convenience callable method to get the parameter by code.
        """
        return self.get_param(code)

    def __getitem__(self, code: str) -> Param:
        """
        This is a convenience getitem method to get the parameter
        """
        return self.get_param(code)

    def __getattr__(self, name: str) -> Any:
        """
        This is a convenience getattr method to get the parameter.
        """
        return self.get_param(name)


@dataclass
class Node:
    """
    Node class is the base class for all the nodes in the pipeline. This class
    will be used to create the nodes and link them together.
    """

    pipeline: InitVar["Pipeline"] = None
    number: int = field(default=None, init=False)
    label: str = field(default=None, init=False)
    type: NodeType = field(default=None, init=False)
    inputValues: List[Param] = field(default_factory=list, init=False)
    outputValues: List[Param] = field(default_factory=list, init=False)

    def __post_init__(self, pipeline=None):
        """
        Post init method to set the pipeline and input/output proxies.
        :param pipeline: the pipeline
        """
        if pipeline:
            pipeline.add_node(self)
        self.pipeline = pipeline
        self.inputs = ParamProxy(self.inputValues)
        self.outputs = ParamProxy(self.outputValues)

    def asdict(self) -> dict:
        """
        Convert the node to a dictionary. This method will convert the node to
        a dictionary.
        :return: the node as a dictionary
        """
        return asdict(self)

    def add_input_param(
        self, code: str, dataType: DataType, value: any = None
    ) -> "Node":
        """
        Add an input parameter to the node. This method will add an input
        parameter to the node.
        :param code: the code of the parameter
        :param dataType: the data type of the parameter
        :param value: the value of the parameter
        :return: the node
        """
        self.inputValues.append(
            Param(code=code, dataType=dataType, value=value, node=self)
        )
        return self

    def add_output_param(
        self, code: str, dataType: DataType, value: any = None
    ) -> "Node":
        """
        Add an output parameter to the node. This method will add an output
        parameter to the node.
        :param code: the code of the parameter
        :param dataType: the data type of the parameter
        :param value: the value of the parameter
        :return: the node
        """
        self.outputValues.append(
            Param(code=code, dataType=dataType, value=value, node=self)
        )
        return self


class LinkableMixin:
    """
    Linkable mixin class, this class will be used to link the output of the
    node to the input of another node.

    This class will be used to link the output of the node to the input of
    another node.
    """

    def validate(
        self,
        to_node: "Node",
        from_param: Union[str, Param] = None,
        to_param: Union[str, Param] = None,
    ) -> None:
        """
        Validate the link between the nodes. This method will validate if the
        link between the nodes is valid.

        :param to_node: the node to link to
        :param from_param: the output parameter or the code of the output
        parameter
        :param to_param: the input parameter or the code of the input parameter
        :raises ValueError: if the link is not valid
        """
        if from_param:
            if isinstance(from_param, str):
                from_param = self.outputs[from_param]
            assert from_param, "From param not found"

        if to_param:
            if isinstance(to_param, str):
                to_param = to_node.inputs[to_param]
            assert to_param, "To param not found"

        # if from_param and to_param:
        #     # validate if both params has the same data type
        #     # if they're not none
        #     if from_param.dataType and to_param.dataType:
        #         if from_param.dataType != to_param.dataType:
        #             raise ValueError(
        #                 f"Param {from_param.code} and {to_param.code} "
        #                 "have different data types"
        #             )

    def link(
        self,
        to_node: "Node",
        from_param: Union[str, Param] = None,
        to_param: Union[str, Param] = None,
    ) -> "Link":
        """
        Link the output of the node to the input of another node. This method
        will link the output of the node to the input of another node.

        :param to_node: the node to link to the output
        :param from_param: the output parameter or the code of the output
        parameter
        :param to_param: the input parameter or the code of the input parameter
        :return: the link
        """

        pipeline = self.pipeline or to_node.pipeline
        assert pipeline, "Node not added to a pipeline"

        self.pipeline = pipeline
        to_node.pipeline = pipeline

        self.validate(to_node, from_param, to_param)

        param_mapping = []
        if from_param and to_param:
            param_mapping = [
                ParamMapping(from_param=from_param, to_param=to_param)
            ]

        link = Link(
            from_node=self.number,
            to_node=to_node.number,
            paramMapping=param_mapping,
        )

        return self.pipeline.add_link(link)


class RoutableMixin:
    """
    Routable mixin class, this class will be used to route the input data to
    different nodes based on the input data type.
    """

    def route(self, *params: Param) -> "Node":
        """
        Route the input data to different nodes based on the input data type.
        This method will automatically link the input data to the output data
        of the node.

        :param params: the output parameters
        :return: the router node
        """
        assert self.pipeline, "Node not added to a pipeline"

        router = self.pipeline.router(
            *[(param.dataType, param.node) for param in params]
        )
        self.link(router)
        for param in params:
            router.outputs.input.link(param)
        return router


class OutputableMixin:
    """
    Outputable mixin class, this class will be used to link the output of the
    node to the output node of the pipeline.
    """

    def use_output(self, param: Union[str, Param]) -> "Node":
        """
        Use the output of the node as the output of the pipeline.
        This method will automatically link the output of the node to the
        output node of the pipeline.

        :param param: the output parameter or the code of the output parameter
        :return: the output node
        """
        assert self.pipeline, "Node not added to a pipeline"
        output = self.pipeline.node(Output)
        param = param if isinstance(param, Param) else self.outputs[param]
        param.link(output.inputs.output)
        return output


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

    def __post_init__(self, pipeline: any = None, instance: any = None):
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

    def __post_init__(self, pipeline: any = None):
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

    def __post_init__(self, pipeline: any = None):
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

    def __post_init__(self, pipeline: any = None, script_path: str = None):
        super().__post_init__(pipeline=pipeline)
        if script_path:
            self.fileId, _ = ScriptFactory.upload_script(script_path)
        if not self.fileId:
            raise ValueError("fileId is required")


@dataclass
class Router(Node, LinkableMixin):
    """
    Router node class, this node will be used to route the input data to
    different nodes based on the input data type.
    """

    routes: List[Route] = field(default_factory=list)
    type: NodeType = NodeType.ROUTER

    def __post_init__(self, pipeline):
        super().__post_init__(pipeline)
        self.add_output_param("input", None)


@dataclass
class Decision(Router):
    """
    Decision node class, this node will be used to make decisions based on
    the input data.
    """

    type: NodeType = NodeType.DECISION

    def __post_init__(self, pipeline):
        super().__post_init__(pipeline)
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

    def __post_init__(self, pipeline: any = None, instance: any = None):
        super().__post_init__(pipeline, instance)
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
    number_of_nodes: InitVar[int] = 0
    instance: InitVar[any] = None

    def add_node(self, node: Node):
        """
        Add a node to the current pipeline.

        This method will take care of setting the pipeline instance to the
        node and setting the node number if it's not set.

        :param node: the node
        :return: the node
        """
        node.pipeline = self
        if not node.number:
            node.number = self.number_of_nodes
            self.number_of_nodes += 1

        if not node.label:
            node.label = f"{node.type.value}(ID={node.number})"

        self.nodes.append(node)
        return node

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
        self.links.append(link)
        return link

    def node(self, node_cls, *args, **kwargs) -> Node:
        """
        Shortcut to create a node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param node_cls: the node class
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return self.add_node(node_cls(*args, **kwargs))

    def input(self, data: str = None, **kwargs) -> Node:
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
        return self.node(Input, data=data, **kwargs)

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
        return self.node(Asset, assetId=assetId, **kwargs)

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
        return self.node(Segmentor, assetId=assetId, **kwargs)

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
        return self.node(Reconstructor, assetId=assetId, **kwargs)

    def script(self, *args, **kwargs) -> Script:
        """
        Shortcut to create an script node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return self.node(Script, *args, **kwargs)

    def output(self, *args, **kwargs) -> Output:
        """
        Shortcut to create an output node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return self.node(Output, *args, **kwargs)

    def decision(self, *args, **kwargs) -> Node:
        """
        Shortcut to create an decision node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.
        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the node
        """
        return self.node(Decision, *args, **kwargs)

    def router(self, *routes: Tuple[DataType, Node], **kwargs) -> Node:
        """
        Shortcut to create an decision node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor. The routes will be handled specially and will be
        converted to Route instances in a convenient way.

        :param routes: the routes
        :param kwargs: keyword arguments
        :return: the node
        """
        return self.node(
            Router,
            routes=[
                Route(
                    value=route[0],
                    path=[route[1]],
                    type=RouteType.CHECK_TYPE,
                    operation=Operation.EQUAL,
                )
                for route in routes
            ],
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
