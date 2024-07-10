import uuid

from enum import Enum
from dataclasses import dataclass, field, asdict, InitVar
from typing import List, Union, Tuple

# these are commented out because of circular imports, please fix it
# "any" is used to avoid circular imports, should be replaced with the correct
# type once the circular imports are fixed

# from aixplain.modules import Model
# from aixplain.modules import Dataset
# from aixplain.modules import Pipeline

from aixplain.factories import ModelFactory
from aixplain.factories import PipelineFactory
from aixplain.factories import DatasetFactory
from aixplain.factories.file_factory import FileFactory


class DataType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    LABEL = 'label'


class NodeType(str, Enum):
    ASSET = 'ASSET'
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    SCRIPT = 'SCRIPT'
    SEGMENTOR = 'SEGMENTOR'
    RECONSTRUCTOR = 'RECONSTRUCTOR'
    ROUTER = 'ROUTER'


class AssetType(str, Enum):
    MODEL = 'MODEL'


class FunctionType(str, Enum):
    AI = 'AI'
    SEGMENTOR = 'SEGMENTOR'
    RECONSTRUCTOR = 'RECONSTRUCTOR'


@dataclass
class ParamMapping:
    from_param: str
    to_param: str


@dataclass
class Link:
    from_node: int
    to_node: int
    paramMapping: List[ParamMapping] = field(default_factory=list)


@dataclass
class Param:
    code: str
    value: str


@dataclass
class Value:
    code: str
    dataType: str


@dataclass
class Route:
    value: DataType
    path: List[int] = field(default_factory=list)
    operation: str = 'equal'
    type: str = 'checkType'


@dataclass
class Node:
    pipeline: InitVar['Pipeline']
    number: int = field(default=None, init=False)
    label: str = field(default=None, init=False)
    type: NodeType = field(default=None, init=False)
    inputValues: List[Value] = field(default_factory=list, init=False)
    outputValues: List[Value] = field(default_factory=list, init=False)

    def __post_init__(self, pipeline):
        self.pipeline = pipeline

    def link(self, to_node: any, from_param: str = None,
             to_param: str = None) -> 'Node':
        self.pipeline.link(self, to_node, from_param=from_param,
                           to_param=to_param)
        return to_node

    def route(self, conditions: List[Tuple[DataType, 'Node']]) -> 'Node':
        return self.pipeline.route(self, conditions)


@dataclass
class Asset(Node):
    assetId: str
    function: str
    supplier: str = None
    version: str = None
    assetType: AssetType = AssetType.MODEL
    functionType: FunctionType = FunctionType.AI
    params: List[Param] = field(default_factory=list)


@dataclass
class Input(Node):
    dataType: List[DataType] = field(default_factory=list)
    data: str = None


@dataclass
class Output(Node):
    dataType: List[DataType] = field(default_factory=list)


@dataclass
class Script(Node):
    fileUrl: str


@dataclass
class Router(Node):
    routes: List[Route] = field(default_factory=list)


@dataclass
class DecisionNode(Node):
    pass


@dataclass
class Segmentor(Asset):
    pass


@dataclass
class Reconstructor(Asset):
    pass


@dataclass
class Pipeline:

    nodes: List[Node] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    number_of_nodes: InitVar[int] = 0
    instance: InitVar[any] = None

    def add(self, node: Node):
        if not node.number:
            node.number = self.number_of_nodes
            self.number_of_nodes += 1

        if isinstance(node, Asset):
            node.type = NodeType.ASSET
        elif isinstance(node, Input):
            node.type = NodeType.INPUT
            if not node.dataType:
                node.dataType = [DataType.TEXT]
        elif isinstance(node, Output):
            node.type = NodeType.OUTPUT
            if not node.dataType:
                node.dataType = [DataType.TEXT]
        elif isinstance(node, Router):
            node.type = NodeType.ROUTER
        elif isinstance(node, Script):
            node.type = NodeType.SCRIPT
            if not node.inputValues:
                node.inputValues = [Value(code='data', dataType='text')]
            if not node.outputValues:
                node.outputValues = [Value(code='data', dataType='text')]
        elif isinstance(node, Segmentor):
            node.type = NodeType.SEGMENTOR
            node.functionType = FunctionType.SEGMENTOR
        elif isinstance(node, Reconstructor):
            node.type = NodeType.RECONSTRUCTOR
            node.functionType = FunctionType.RECONSTRUCTOR

        if not node.label:
            node.label = f'{node.type.value}-{node.number}'

        self.nodes.append(node)
        return node

    def add_asset(self, asset: Union[str, any]) -> Asset:
        asset = self.ensure_model(asset)
        return self.add(Asset(self,
                              asset.id,
                              asset.function.value,
                              asset.supplier.value['code'],
                              asset.version))

    def add_segmentor(self, asset: Union[str, any]) -> Segmentor:
        asset = self.ensure_model(asset)
        return self.add(Segmentor(self,
                                  asset.id,
                                  asset.function.value,
                                  asset.supplier.value['code'],
                                  asset.version))

    def add_reconstructor(self, asset: Union[str, any]) -> Reconstructor:
        asset = self.ensure_model(asset)
        return self.add(Reconstructor(self,
                                      asset.id,
                                      asset.function.value,
                                      asset.supplier.value['code'],
                                      asset.version))

    def add_router(self, **kwargs) -> Router:
        return self.add(Router(self, **kwargs))

    def ensure_model(self, model: Union[str, any]) -> any:
        if isinstance(model, str):
            try:
                return ModelFactory.get(model)
            except Exception as e:
                raise ValueError(f'Model {model} not found') from e
        return model

    def ensure_dataset(self, dataset: Union[str, any]) -> any:
        if isinstance(dataset, str):
            try:
                return DatasetFactory.get(dataset)
            except Exception as e:
                raise ValueError(f'Dataset {dataset} not found') from e
        return dataset

    def add_input(self, **kwargs) -> Input:
        if 'data' in kwargs:
            kwargs['data'] = FileFactory.to_link(kwargs['data'])
        return self.add(Input(self, **kwargs))

    def add_output(self, **kwargs) -> Output:
        return self.add(Output(self, **kwargs))

    def add_script(self, script_path: str = None, **kwargs) -> Script:
        if script_path:
            if 'fileUrl' in kwargs:
                raise ValueError('fileUrl should not be provided')
            try:
                kwargs['fileUrl'] = FileFactory.create(local_path=script_path)
            except Exception as e:
                raise ValueError(
                    f'Error uploading script {script_path}') from e
        return self.add(Script(self, **kwargs))

    def link(self, from_node: Node, to_node: Node, from_param: str = None,
             to_param: str = None) -> Node:
        param_mapping = []

        if from_param and not to_param:
            raise ValueError('to_param is required')
        if to_param and not from_param:
            raise ValueError('from_param is required')

        if from_param and to_param:
            param_mapping = [
                ParamMapping(from_param=from_param, to_param=to_param)
            ]
        link = Link(from_node.number, to_node.number,
                    paramMapping=param_mapping)
        self.links.append(link)
        return to_node

    def route(self, from_node: Node,
              conditions: Tuple[DataType, Node]) -> Node:
        routes = []
        for data_type, to_node in conditions:
            routes.append(Route(value=data_type, path=[to_node.number]))
        router = self.add_router(routes=routes)
        self.link(from_node, router)
        for data_type, to_node in conditions:
            # Here, what we supposed to do while determining the parameters?
            self.link(router, to_node, 'input', data_type.value)
        return from_node

    def to_dict(self) -> dict:
        obj = asdict(self)
        for link in obj['links']:
            link['from'] = link.pop('from_node')
            link['to'] = link.pop('to_node')
            params = link.get('paramMapping', []) or []
            for param in params:
                param['from'] = param.pop('from_param')
                param['to'] = param.pop('to_param')
        return obj

    def save(self) -> 'Pipeline':
        name = f'pipeline-{uuid.uuid4()}'
        self.instance = PipelineFactory.create(name, self.to_dict())
        return self

    def run(self, *args, **kwargs) -> any:
        if not self.instance:
            raise ValueError('Pipeline not saved')

        return self.instance.run(*args, **kwargs)
