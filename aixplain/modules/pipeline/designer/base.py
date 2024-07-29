from dataclasses import dataclass, field, asdict, InitVar
from typing import Any, List, Union, TYPE_CHECKING

from .enums import NodeType, ParamType, DataType

if TYPE_CHECKING:
    from aixplain.modules.pipeline import Pipeline


@dataclass
class Param:
    """
    Param class, this class will be used to create the parameters of the node.
    """

    code: str
    dataType: DataType
    value: str
    param_type: InitVar[ParamType] = None
    node: InitVar["Node"] = None

    def __post_init__(self, node: "Node" = None):
        """
        Post init method to set the node of the param.
        """
        if node:
            self.attach(node)
        self._link = None

    def attach(self, node: "Node"):
        """
        Attach the param to the node.
        :param node: the node
        """
        assert not self.node, "Param already attached to a node"
        self.node = node
        if self.param_type == ParamType.INPUT:
            node.inputValues.append(self)
        elif self.param_type == ParamType.OUTPUT:
            node.outputValues.append(self)
        else:
            raise ValueError(f"Invalid param type: {self.param_type}")

    def link(self, to_param: "Param") -> "Param":
        """
        Link the output of the param to the input of another param.
        :param to_param: the input param
        :return: the param
        """
        assert to_param.param_type == ParamType.INPUT, "Invalid param type"
        assert self.node and self in self.node.outputValues, "Param not attached to a node"
        return to_param.back_link(self)

    def back_link(self, from_param: "Param") -> "Param":
        """
        Link the input of the param to the output of another param.
        :param from_param: the output param
        :return: the param
        """
        assert from_param.param_type == ParamType.OUTPUT, "Invalid param type"
        assert self.node and self in self.node.inputValues, "Param not attached to a node"
        link = from_param.node.link(self.node, from_param.code, self.code)
        self._link = link
        from_param._link = link
        return link


@dataclass
class InputParam(Param):

    param_type: ParamType = ParamType.INPUT
    is_required: InitVar[bool] = True

    def __post_init__(self, node: "Node" = None, is_required: bool = False):
        """
        Post init method to set the required flag.
        """
        super().__post_init__(node=node)
        self.is_required = is_required


@dataclass
class OutputParam(Param):

    param_type: ParamType = ParamType.OUTPUT


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

    from_node: Union[int, "Node"]
    to_node: Union[int, "Node"]
    paramMapping: List[ParamMapping] = field(default_factory=list)
    pipeline: InitVar["Pipeline"] = None

    def __post_init__(self, pipeline: "Pipeline" = None):
        if pipeline:
            self.attach(pipeline)
        if isinstance(self.from_node, Node):
            self.from_node = self.from_node.number
        if isinstance(self.to_node, Node):
            self.to_node = self.to_node.number

    def attach(self, pipeline: "Pipeline"):
        """
        Attach the link to the pipeline.
        :param pipeline: the pipeline
        """
        assert not self.pipeline, "Link already attached to a pipeline"

        self.pipeline = pipeline
        pipeline.links.append(self)
        return self


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
        raise AttributeError(f"Param '{code}' not found")

    def set_param(self, code: str, value: any) -> None:
        """
        Set the parameter value by code. This method will set the parameter
        value by code.
        :param code: the code of the parameter
        :param value: the value of the parameter
        """
        param = self.get_param(code)
        param.value = value

    def __call__(self, code: str, value: any = None) -> Param:
        """
        This is a convenience callable method to get the parameter by code.
        """
        if value:
            self.set_param(code, value)
        return self.get_param(code)

    def __getitem__(self, code: str) -> Param:
        """
        This is a convenience getitem method to get the parameter
        """
        return self.get_param(code)

    def __setitem__(self, code: str, value: any) -> None:
        """
        This is a convenience setitem method to set the parameter value.
        """
        self.set_param(code, value)

    def __getattr__(self, name: str) -> Any:
        """
        This is a convenience getattr method to get the parameter.
        """
        return self.get_param(name)

    def __hasattr__(self, name: str) -> bool:
        """
        This is a convenience hasattr method to check if the parameter exists.
        """
        return self.has_param(name)

    def has_param(self, code: str) -> bool:
        """
        Check if the parameter exists.
        :param code: the code of the parameter
        :return: True if the parameter exists, False otherwise
        """
        return any(param.code == code for param in self.params)

    def __contains__(self, code: str) -> bool:
        """
        Check if the parameter exists.
        :param code: the code of the parameter
        :return: True if the parameter exists, False otherwise
        """
        return self.has_param(code)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        This is a convenience setattr method to set the parameter value.
        """
        if name in ["params"]:
            super().__setattr__(name, value)
        else:
            self.set_param(name, value)


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
        self.inputs = ParamProxy(self.inputValues)
        self.outputs = ParamProxy(self.outputValues)
        if pipeline:
            self.attach(pipeline)

    def attach(self, pipeline: "Pipeline"):
        """
        Attach the node to the pipeline.
        :param pipeline: the pipeline
        """
        assert not self.pipeline, "Node already attached to a pipeline"
        assert not self.number, "Node number already set"
        assert not self.label, "Node label already set"
        assert self.type, "Node type not set"

        self.pipeline = pipeline
        self.number = len(pipeline.nodes)
        self.label = f"{self.type.value}(ID={self.number})"
        pipeline.nodes.append(self)
        return self

    def to_dict(self) -> dict:
        """
        Convert the node to a dictionary. This method will convert the node to
        a dictionary.
        :return: the node as a dictionary
        """
        return asdict(self)

    def add_param(self, param: Param) -> Param:
        """
        Add a parameter to the node. This method will add a parameter to the
        node.
        :param param: the parameter
        :return: the parameter
        """
        return param.attach(self)

    def add_input_param(
        self,
        code: str,
        dataType: DataType,
        value: any = None,
        is_required: bool = False,
    ) -> InputParam:
        """
        Add an input parameter to the node. This method will add an input
        parameter to the node.
        :param code: the code of the parameter
        :param dataType: the data type of the parameter
        :param value: the value of the parameter
        :return: the node
        """
        return InputParam(
            code=code,
            dataType=dataType,
            value=value,
            node=self,
            is_required=is_required,
        )

    def add_output_param(self, code: str, dataType: DataType, value: any = None) -> "Node":
        """
        Add an output parameter to the node. This method will add an output
        parameter to the node.
        :param code: the code of the parameter
        :param dataType: the data type of the parameter
        :param value: the value of the parameter
        :return: the node
        """
        return OutputParam(code=code, dataType=dataType, value=value, node=self)
