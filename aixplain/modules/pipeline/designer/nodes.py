from typing import List, Union, Type, TYPE_CHECKING, Optional
from enum import Enum

from aixplain.modules import Model
from aixplain.enums import DataType, Function

from .enums import NodeType, FunctionType, RouteType, Operation, AssetType
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
    from .pipeline import DesignerPipeline


class AssetNode(Node[TI, TO], LinkableMixin, OutputableMixin):
    """
    Asset node class, this node will be used to fetch the asset from the
    aixplain platform and use it in the pipeline.

    `assetId` is required and will be used to fetch the asset from the
    aixplain platform.

    Input and output parameters will be automatically added based on the
    asset function spec.
    """

    asset_id: Union[Model, str] = None
    function: str = None
    supplier: str = None
    version: str = None
    assetType: AssetType = AssetType.MODEL
    functionType: FunctionType = FunctionType.AI

    type: NodeType = NodeType.ASSET

    def __init__(
        self,
        asset_id: Union[Model, str] = None,
        supplier: str = None,
        version: str = None,
        pipeline: "DesignerPipeline" = None,
        **kwargs,
    ):
        super().__init__(pipeline=pipeline, **kwargs)
        self.asset_id = asset_id
        self.supplier = supplier
        self.version = version

        if self.asset_id:
            self.populate_asset()

    def populate_asset(self):
        from aixplain.factories.model_factory import ModelFactory

        if isinstance(self.asset_id, str):
            self.asset = ModelFactory.get(self.asset_id)
        elif isinstance(self.asset_id, Model):
            self.asset = self.asset_id
            self.asset_id = self.asset_id.id
        else:
            raise ValueError("assetId should be a string or an Asset instance")

        try:
            self.supplier = self.asset.supplier.value["code"]
        except Exception:
            self.supplier = str(self.asset.supplier)

        self.version = self.asset.version

        if self.function:
            if self.asset.function.value != self.function:
                raise ValueError(f"Function {self.function} is not supported by asset {self.asset_id}")
        else:
            self.function = self.asset.function.value

        self._auto_populate_params()
        self._auto_set_params()

    def _auto_populate_params(self):
        from aixplain.enums.function import FunctionInputOutput

        spec = FunctionInputOutput[self.function]["spec"]

        # When the node is a utility, we need to create it's input parameters
        # dynamically by referring the node data.
        if self.function == Function.UTILITIES:
            for param in self.asset.input_params.values():
                self.inputs.create_param(
                    code=param["name"],
                    data_type=param["dataType"],
                    is_required=param["required"],
                )
        else:
            for item in spec["params"]:
                if item["code"] not in self.inputs:
                    self.inputs.create_param(
                        code=item["code"],
                        data_type=item["dataType"],
                        is_required=item["required"],
                    )

            if self.asset.model_params:
                for code, param in self.asset.model_params.parameters.items():
                    if code not in self.inputs:
                        self.inputs.create_param(
                            code=code,
                            is_required=param.required,
                            value=param.value,
                        )

        for item in spec["output"]:
            if item["code"] not in self.outputs:
                self.outputs.create_param(
                    code=item["code"],
                    data_type=item["dataType"],
                )

    def _auto_set_params(self):
        for k, v in self.asset.additional_info["parameters"].items():
            if k not in self.inputs:
                continue

            if isinstance(v, list):
                self.inputs[k] = v[0]
            else:
                self.inputs[k] = v

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["function"] = self.function
        obj["assetId"] = self.asset_id
        obj["supplier"] = self.supplier
        obj["version"] = self.version
        obj["assetType"] = self.assetType
        # Handle functionType as enum or string
        if isinstance(self.functionType, Enum):
            obj["functionType"] = self.functionType.value
        else:
            obj["functionType"] = self.functionType
        obj["type"] = self.type
        return obj


class BareAssetInputs(Inputs):
    pass


class BareAssetOutputs(Outputs):
    pass


class BareAsset(AssetNode[BareAssetInputs, BareAssetOutputs]):
    pass


class Utility(AssetNode[BareAssetInputs, BareAssetOutputs]):

    function = "utilities"


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

    data_types: Optional[List[DataType]] = None
    data: Optional[str] = None
    type: NodeType = NodeType.INPUT
    inputs_class: Type[TI] = InputInputs
    outputs_class: Type[TO] = InputOutputs

    def __init__(
        self,
        data: Optional[str] = None,
        data_types: Optional[List[DataType]] = None,
        pipeline: "DesignerPipeline" = None,
        **kwargs,
    ):
        from aixplain.factories.file_factory import FileFactory

        super().__init__(pipeline=pipeline, **kwargs)
        self.data_types = data_types or []
        self.data = data

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

    data_types: Optional[List[DataType]] = None
    type: NodeType = NodeType.OUTPUT
    inputs_class: Type[TI] = OutputInputs
    outputs_class: Type[TO] = OutputOutputs

    def __init__(self, data_types: Optional[List[DataType]] = None, pipeline: "DesignerPipeline" = None, **kwargs):
        super().__init__(pipeline=pipeline, **kwargs)
        self.data_types = data_types or []

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

    fileId: Optional[str] = None
    script_path: Optional[str] = None
    type: NodeType = NodeType.SCRIPT

    def __init__(
        self,
        pipeline: "DesignerPipeline" = None,
        script_path: Optional[str] = None,
        fileId: Optional[str] = None,
        fileMetadata: Optional[str] = None,
        **kwargs,
    ):
        from aixplain.factories.script_factory import ScriptFactory

        super().__init__(pipeline=pipeline, **kwargs)

        assert script_path or fileId, "script_path or fileId is required"

        if not fileId:
            self.fileId, self.fileMetadata = ScriptFactory.upload_script(script_path)
        else:
            self.fileId = fileId
            self.fileMetadata = fileMetadata

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["fileId"] = self.fileId
        obj["fileMetadata"] = self.fileMetadata
        return obj


class Route(Serializable):
    """
    Route class, this class will be used to route the input data to different
    nodes based on the input data type.
    """

    value: DataType
    path: List[Union[Node, int]]
    operation: Operation
    type: RouteType

    def __init__(self, value: DataType, path: List[Union[Node, int]], operation: Operation, type: RouteType, **kwargs):
        """
        Post init method to convert the nodes to node numbers if they are
        nodes.
        """
        self.value = value
        self.path = path
        self.operation = operation
        self.type = type

        # Path can be an empty list in case the user has a valid case
        # if not self.path:
        #     raise ValueError("Path is not valid, should be a list of nodes")

        # convert nodes to node numbers if they are nodes
        self.path = [node.number if isinstance(node, Node) else node for node in self.path]

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

    routes: List[Route]
    type: NodeType = NodeType.ROUTER
    inputs_class: Type[TI] = RouterInputs
    outputs_class: Type[TO] = RouterOutputs

    def __init__(self, routes: List[Route], pipeline: "DesignerPipeline" = None, **kwargs):
        super().__init__(pipeline=pipeline, **kwargs)
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
    data: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.data = self.create_param("data")


class Decision(Node[DecisionInputs, DecisionOutputs], LinkableMixin):
    """
    Decision node class, this node will be used to make decisions based on
    the input data.
    """

    routes: List[Route]
    type: NodeType = NodeType.DECISION
    inputs_class: Type[TI] = DecisionInputs
    outputs_class: Type[TO] = DecisionOutputs

    def __init__(self, routes: List[Route], pipeline: "DesignerPipeline" = None, **kwargs):
        super().__init__(pipeline=pipeline, **kwargs)
        self.routes = routes

    def link(
        self,
        to_node: Node,
        from_param: Union[str, Param],
        to_param: Union[str, Param],
    ) -> Link:
        link = super().link(to_node, from_param, to_param)

        if isinstance(from_param, str):
            assert (
                from_param in self.outputs
            ), f"Decision node has no input param called {from_param}, node linking validation is broken, please report this issue."
            from_param = self.outputs[from_param]

        if from_param.code == "data":
            if not self.inputs.passthrough.link_:
                raise ValueError("To able to infer data source, " "passthrough input param should be linked first.")

            # Infer data source from the passthrough node
            link.data_source_id = self.inputs.passthrough.link_.from_node.number

            # Infer data type from the passthrough node
            ref_param_code = self.inputs.passthrough.link_.from_param
            ref_node = self.inputs.passthrough.link_.from_node
            ref_param = ref_node.outputs[ref_param_code]
            from_param.data_type = ref_param.data_type

        return link

    def serialize(self) -> dict:
        obj = super().serialize()
        obj["routes"] = [route.serialize() for route in self.routes]
        return obj


class BaseSegmentor(AssetNode[TI, TO]):
    """
    Segmentor node class, this node will be used to segment the input data
    into smaller fragments for much easier and efficient processing.
    """

    type: NodeType = NodeType.ASSET
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

    type: NodeType = NodeType.ASSET
    functionType: FunctionType = FunctionType.SEGMENTOR
    inputs_class: Type[TI] = SegmentorInputs
    outputs_class: Type[TO] = SegmentorOutputs


class BaseReconstructor(AssetNode[TI, TO]):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.ASSET
    functionType: FunctionType = FunctionType.RECONSTRUCTOR


class ReconstructorInputs(Inputs):
    pass


class ReconstructorOutputs(Outputs):
    pass


class BareReconstructor(BaseReconstructor[ReconstructorInputs, ReconstructorOutputs]):
    """
    Reconstructor node class, this node will be used to reconstruct the
    output of the segmented lines of execution.
    """

    type: NodeType = NodeType.ASSET
    functionType: FunctionType = FunctionType.RECONSTRUCTOR
    inputs_class: Type[TI] = ReconstructorInputs
    outputs_class: Type[TO] = ReconstructorOutputs


class BaseMetric(AssetNode[TI, TO]):
    functionType: FunctionType = FunctionType.METRIC

    def build_label(self):
        return f"METRIC({self.number})"


class MetricInputs(Inputs):

    hypotheses: InputParam = None
    references: InputParam = None
    sources: InputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.hypotheses = self.create_param("hypotheses")
        self.references = self.create_param("references")
        self.sources = self.create_param("sources")


class MetricOutputs(Outputs):

    data: OutputParam = None

    def __init__(self, node: Node):
        super().__init__(node)
        self.data = self.create_param("data")


class BareMetric(BaseMetric[MetricInputs, MetricOutputs]):
    pass
