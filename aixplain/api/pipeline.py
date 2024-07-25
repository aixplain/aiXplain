import uuid
from dataclasses import dataclass, field, InitVar, asdict
from typing import List, Tuple

from aixplain.factories.pipeline_factory import PipelineFactory

from .enums import (
    NodeType,
    DataType,
    RouteType,
    Operation,
)
from .base import Node, Link
from .nodes import (
    Asset,
    Decision,
    Script,
    Input,
    Output,
    Route,
    Router,
    Reconstructor,
    Segmentor,
)


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

    def validate_nodes(self):
        """
        Validate the linkage of the pipeline. This method will validate the
        linkage of the pipeline by applying the following checks:
        - All input nodes are linked out
        - All output nodes are linked in
        - All other nodes are linked in and out

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

    def is_param_linked(self, node, param):
        """
        Check if the param is linked to another node. This method will check
        if the param is linked to another node.
        :param node: the node
        :param param: the param
        :return: True if the param is linked, False otherwise
        """
        link_to_map = {link.to_node: link for link in self.links}
        link = link_to_map.get(node.number)
        if link and param.code in [p.to_param for p in link.paramMapping]:
            return True
        return False

    def is_param_set(self, node, param):
        """
        Check if the param is set. This method will check if the param is set
        or linked to another node.
        :param node: the node
        :param param: the param
        :return: True if the param is set, False otherwise
        """
        return param.value or self.is_param_linked(node, param)

    def validate_params(self):
        """
        This method will check if all required params are either set or linked

        :raises ValueError: if the pipeline is not valid
        """
        for node in self.nodes:
            for param in node.inputValues:
                if param.is_required and not self.is_param_set(node, param):
                    raise ValueError(
                        f"Param {param.code} of node {node.label} is required"
                    )

    def validate_links(self):
        """
        This method will check whether all links pointing to the correct
        nodes and corresponding params.

        :raises ValueError: if the pipeline is not valid
        """
        for link in self.links:
            from_node = next(
                (node for node in self.nodes if node.number == link.from_node),
                None,
            )
            to_node = next(
                (node for node in self.nodes if node.number == link.to_node),
                None,
            )
            if not from_node:
                raise ValueError(f"Node {link.from_node} not found")
            if not to_node:
                raise ValueError(f"Node {link.to_node} not found")
            for param in link.paramMapping:
                if param.from_param not in from_node.outputs:
                    raise ValueError(
                        f"Param {param.from_param} not found in node {from_node.label}"
                    )
                if param.to_param not in to_node.inputs:
                    raise ValueError(
                        f"Param {param.to_param} not found in node {to_node.label}"
                    )

                # Here do we need to check the output and input params together
                # to make sure they have the same data type?

    def validate(self):
        """
        Validate the pipeline. This method will validate the pipeline by
        series of checks:
        - Validate all nodes are linked correctly
        - Validate all links are pointing to the correct nodes and params
        - Validate all required params are set or linked

        Any other validation checks can be added here.

        :raises ValueError: if the pipeline is not valid
        """
        self.validate_nodes()
        self.validate_links()
        self.validate_params()

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
