from typing import (
    List,
    Union,
    TYPE_CHECKING,
    Generic,
    TypeVar,
    Type,
    Optional,
    Iterator,
)

from aixplain.enums import DataType
from .enums import NodeType, ParamType
from .utils import find_prompt_params

if TYPE_CHECKING:
    from .pipeline import DesignerPipeline

TI = TypeVar("TI", bound="Inputs")
TO = TypeVar("TO", bound="Outputs")


class Serializable:
    def serialize(self) -> dict:
        raise NotImplementedError()


class Param(Serializable):
    """
    Param class, this class will be used to create the parameters of the node.
    """

    code: str
    param_type: ParamType
    data_type: Optional[DataType] = None
    value: Optional[str] = None
    node: Optional["Node"] = None
    link_: Optional["Link"] = None

    def __init__(
        self,
        code: str,
        data_type: Optional[DataType] = None,
        value: Optional[str] = None,
        node: Optional["Node"] = None,
        param_type: Optional[ParamType] = None,
    ):
        self.code = code
        self.data_type = data_type
        self.value = value

        # is subclasses do not set the param type, set it to None
        self.param_type = getattr(self, "param_type", param_type)

        if node:
            self.attach_to(node)

    def attach_to(self, node: "Node") -> "Param":
        """
        Attach the param to the node.
        :param node: the node
        :return: the param
        """
        assert not self.node, "Param already attached to a node"
        assert self.param_type, "Param type not set"
        if self.param_type == ParamType.INPUT:
            node.inputs.add_param(self)
        elif self.param_type == ParamType.OUTPUT:
            node.outputs.add_param(self)
        else:
            raise ValueError("Invalid param type")
        self.node = node
        return self

    def link(self, to_param: "Param") -> "Param":
        """
        Link the output of the param to the input of another param.
        :param to_param: the input param
        :return: the param
        """
        assert self.node, "Param not attached to a node"
        assert to_param.param_type == ParamType.INPUT, "Invalid param type"
        assert self in self.node.outputs, "Param not registered as output"
        return to_param.back_link(self)

    def back_link(self, from_param: "Param") -> "Param":
        """
        Link the input of the param to the output of another param.
        :param from_param: the output param
        :return: the param
        """
        assert self.node, "Param not attached to a node"
        assert from_param.param_type == ParamType.OUTPUT, "Invalid param type"
        assert self.code in self.node.inputs, "Param not registered as input"
        link = from_param.node.link(self.node, from_param, self)
        return link

    def serialize(self) -> dict:
        return {
            "code": self.code,
            "dataType": self.data_type,
            "value": self.value,
        }


class InputParam(Param):

    param_type: ParamType = ParamType.INPUT
    is_required: bool = True

    def __init__(self, *args, is_required: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_required = is_required


class OutputParam(Param):

    param_type: ParamType = ParamType.OUTPUT


class Link(Serializable):
    """
    Link class, this class will be used to link the output of the node to the
    input of another node.
    """

    from_node: "Node"
    to_node: "Node"
    from_param: str
    to_param: str
    data_source_id: Optional[str] = None

    pipeline: Optional["DesignerPipeline"] = None

    def __init__(
        self,
        from_node: "Node",
        to_node: "Node",
        from_param: Union[Param, str],
        to_param: Union[Param, str],
        data_source_id: Optional[str] = None,
        pipeline: "DesignerPipeline" = None,
    ):

        if isinstance(from_param, Param):
            from_param = from_param.code
        if isinstance(to_param, Param):
            to_param = to_param.code

        assert from_param in from_node.outputs, (
            "Invalid from param. " "Make sure all input params are already linked accordingly"
        )

        assert to_param in to_node.inputs, "Invalid to param. " "Make sure all output params are already linked accordingly"

        tp_instance = to_node.inputs[to_param]
        fp_instance = from_node.outputs[from_param]

        assert to_param in to_node.inputs, "Invalid to param"

        tp_instance.link_ = self
        fp_instance.link_ = self

        self.from_node = from_node
        self.to_node = to_node
        self.from_param = from_param
        self.to_param = to_param
        self.data_source_id = data_source_id

        if pipeline:
            self.attach_to(pipeline)

        # self.validate()
        self.auto_infer()

    def auto_infer(self):
        from_param = self.from_node.outputs[self.from_param]
        to_param = self.to_node.inputs[self.to_param]

        # if one of the data types is missing, infer the other one
        data_type = from_param.data_type or to_param.data_type
        from_param.data_type = data_type
        to_param.data_type = data_type

        def infer_data_type(node):
            from .nodes import Input, Output

            if isinstance(node, Input) or isinstance(node, Output):
                if data_type and data_type not in node.data_types:
                    node.data_types.append(data_type)

        infer_data_type(self.from_node)
        infer_data_type(self.to_node)

    def validate(self):
        from_param = self.from_node.outputs[self.from_param]
        to_param = self.to_node.inputs[self.to_param]

        # Should we check for data type mismatch?
        if from_param.data_type and to_param.data_type:
            if from_param.data_type != to_param.data_type:
                raise ValueError(f"Data type mismatch between {from_param.data_type} and {to_param.data_type}")  # noqa

    def attach_to(self, pipeline: "DesignerPipeline"):
        """
        Attach the link to the pipeline.
        :param pipeline: the pipeline
        """
        assert not self.pipeline, "Link already attached to a pipeline"
        if not self.from_node.pipeline or self.from_node not in pipeline.nodes:
            self.from_node.attach_to(pipeline)
        if not self.to_node.pipeline or self.to_node not in pipeline.nodes:
            self.to_node.attach_to(pipeline)

        self.pipeline = pipeline
        self.pipeline.links.append(self)
        return self

    def serialize(self) -> dict:
        assert self.from_node.number is not None, "From node number not set"
        assert self.to_node.number is not None, "To node number not set"
        param_mapping = {
            "from": self.from_param,
            "to": self.to_param,
        }
        if self.data_source_id:
            param_mapping["dataSourceId"] = self.data_source_id

        return {
            "from": self.from_node.number,
            "to": self.to_node.number,
            "paramMapping": [param_mapping],
        }


class ParamProxy(Serializable):

    node: "Node"

    def __init__(self, node: "Node", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node = node
        self._params = []

    def add_param(self, param: Param) -> None:
        # check if param already registered
        if param in self:
            raise ValueError(f"Parameter with code '{param.code}' already exists.")
        self._params.append(param)
        # also set attribute on the node dynamically if there's no
        # any attribute with the same name
        if not hasattr(self, param.code):
            setattr(self, param.code, param)

    def _create_param(self, code: str, data_type: DataType = None, value: any = None) -> Param:
        raise NotImplementedError()

    def create_param(
        self,
        code: str,
        data_type: DataType = None,
        value: any = None,
        is_required: bool = False,
    ) -> Param:
        param = self._create_param(code, data_type, value)
        param.is_required = is_required
        self.add_param(param)
        param.node = self.node
        return param

    def __getattr__(self, code: str) -> Param:
        if code == "_params":
            raise AttributeError("Attribute '_params' is not accessible")
        for param in self._params:
            if param.code == code:
                return param
        raise AttributeError(f"Attribute with code '{code}' not found.")

    def __getitem__(self, code: str) -> Param:
        try:
            return getattr(self, code)
        except AttributeError:
            raise KeyError(f"Parameter with code '{code}' not found.")

    def special_prompt_handling(self, code: str, value: str) -> None:
        """
        This method will handle the special prompt handling for asset nodes
        having `text-generation` function type.
        """
        prompt_param = getattr(self, "prompt", None)
        if prompt_param:
            raise ValueError("Prompt param already exists")

        from .nodes import AssetNode

        if not isinstance(self.node, AssetNode):
            return

        if not hasattr(self.node, "asset") or self.node.asset.function != "text-generation":
            return

        matches = find_prompt_params(value)
        for match in matches:
            if match in self:
                raise ValueError(f"Prompt param with code '{match}' already exists")

            self.node.inputs.create_param(match, DataType.TEXT, is_required=True)

    def __setitem__(self, code: str, value: str) -> None:
        setattr(self, code, value)

    def __setattr__(self, name: str, value: any) -> None:
        if name == "prompt":
            self.special_prompt_handling(name, value)

        param = getattr(self, name, None)
        if param and isinstance(param, Param):
            param.value = value
        else:
            super().__setattr__(name, value)

    def __contains__(self, param: Union[str, Param]) -> bool:
        code = param if isinstance(param, str) else param.code
        return any(param.code == code for param in self._params)

    def __iter__(self) -> Iterator[Param]:
        return iter(self._params)

    def __len__(self) -> int:
        return len(self._params)

    def serialize(self) -> List[dict]:
        return [param.serialize() for param in self._params]


class Inputs(ParamProxy):
    def _create_param(
        self,
        code: str,
        data_type: DataType = None,
        value: any = None,
        is_required: bool = False,
    ) -> InputParam:
        return InputParam(
            code=code,
            data_type=data_type,
            value=value,
            is_required=is_required,
        )


class Outputs(ParamProxy):
    def _create_param(self, code: str, data_type: DataType = None, value: any = None) -> OutputParam:
        return OutputParam(code=code, data_type=data_type, value=value)


class Node(Generic[TI, TO], Serializable):
    """
    Node class is the base class for all the nodes in the pipeline. This class
    will be used to create the nodes and link them together.
    """

    number: Optional[int] = None
    label: Optional[str] = None
    type: Optional[NodeType] = None

    inputs: Optional[TI] = None
    outputs: Optional[TO] = None
    inputs_class: Optional[Type[TI]] = Inputs
    outputs_class: Optional[Type[TO]] = Outputs
    pipeline: Optional["DesignerPipeline"] = None

    def __init__(
        self,
        pipeline: "DesignerPipeline" = None,
        number: Optional[int] = None,
        label: Optional[str] = None,
    ):
        self.inputs = self.inputs_class(node=self)
        self.outputs = self.outputs_class(node=self)
        self.number = number
        self.label = label

        if pipeline:
            self.attach_to(pipeline)

    def build_label(self):
        return f"{self.type.value}(ID={self.number})"

    def attach_to(self, pipeline: "DesignerPipeline"):
        """
        Attach the node to the pipeline.
        :param pipeline: the pipeline
        """
        assert not self.pipeline, "Node already attached to a pipeline"
        assert self not in pipeline.nodes, "Node already attached to a pipeline"
        assert self.type, "Node type not set"

        self.pipeline = pipeline
        if self.number is None:
            self.number = len(pipeline.nodes)
        if self.label is None:
            self.label = self.build_label()

        assert not pipeline.get_node(self.number), "Node number already exists"
        pipeline.nodes.append(self)
        return self

    def serialize(self) -> dict:
        return {
            "number": self.number,
            "label": self.label,
            "type": self.type.value,
            "inputValues": self.inputs.serialize(),
            "outputValues": self.outputs.serialize(),
        }
