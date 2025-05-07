from typing import List, Type, Tuple, TypeVar

from aixplain.enums import DataType

from .base import Serializable, Node, Link
from .nodes import (
    AssetNode,
    Utility,
    Decision,
    Script,
    Input,
    Output,
    Router,
    Route,
    BareReconstructor,
    BareSegmentor,
    BareMetric,
)
from .enums import NodeType, RouteType, Operation
from .mixins import OutputableMixin
from .utils import find_prompt_params

T = TypeVar("T", bound="AssetNode")


class DesignerPipeline(Serializable):
    nodes: List[Node] = None
    links: List[Link] = None
    instance: any = None

    def __init__(self):
        self.nodes = []
        self.links = []

    def add_node(self, node: Node):
        """
        Add a node to the current pipeline.

        This method will take care of setting the pipeline instance to the
        node and setting the node number if it's not set.

        :param node: the node
        :return: the node
        """
        return node.attach_to(self)

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
        return link.attach_to(self)

    def serialize(self) -> dict:
        """
        Serialize the pipeline to a dictionary. This method will serialize the
        pipeline to a dictionary.

        :return: the pipeline as a dictionary
        """
        nodes = [node.serialize() for node in self.nodes]
        links = [link.serialize() for link in self.links]

        # merge the params for links using the key `from_node` and `to_node`
        merged_links = {}
        for link in links:
            key = (link['from'], link['to'])
            if key not in merged_links:
                merged_links[key] = link
            else:
                existing_link = merged_links[key]
                existing_link['paramMapping'] += link['paramMapping']

        return {
            "nodes": nodes,
            "links": list(merged_links.values()),
        }

    def validate_nodes(self):
        """
        Validate the linkage of the pipeline. This method will validate the
        linkage of the pipeline by applying the following checks:
        - All input nodes are linked out
        - All output nodes are linked in
        - All other nodes are linked in and out

        :raises ValueError: if the pipeline is not valid
        """
        link_from_map = {link.from_node.number: link for link in self.links}
        link_to_map = {link.to_node.number: link for link in self.links}
        contains_input = False
        contains_output = False
        contains_asset = False
        for node in self.nodes:
            # validate every input node is linked out
            if node.type == NodeType.INPUT:
                contains_input = True
                if node.number not in link_from_map:
                    raise ValueError(f"Input node {node.label} not linked out")
            # validate every output node is linked in
            elif node.type == NodeType.OUTPUT:
                contains_output = True
                if node.number not in link_to_map:
                    raise ValueError(f"Output node {node.label} not linked in")
            # validate rest of the nodes are linked in and out
            else:
                if isinstance(node, OutputableMixin):
                    contains_asset = True
                if node.number not in link_from_map:
                    raise ValueError(f"Node {node.label} not linked in")
                if node.number not in link_to_map:
                    raise ValueError(f"Node {node.label} not linked out")

        if not contains_input or not contains_output or not contains_asset:
            raise ValueError(
                "The pipeline requires at least one asset or script node, along with both input and output nodes."  # noqa
            )

    def is_param_linked(self, node, param):
        """
        Check if the param is linked to another node. This method will check
        if the param is linked to another node.
        :param node: the node
        :param param: the param
        :return: True if the param is linked, False otherwise
        """
        for link in self.links:
            if link.to_node.number == node.number and param.code == link.to_param:
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

    def special_prompt_validation(self, node: Node):
        """
        This method will handle the special rule for asset nodes having
        `text-generation` function type where if any prompt variable exists
        then the `text` param is not required but the prompt param are.

        :param node: the node
        :raises ValueError: if the pipeline is not valid
        """
        if isinstance(node, AssetNode) and node.asset.function == "text-generation":
            if self.is_param_set(node, node.inputs.prompt):
                matches = find_prompt_params(node.inputs.prompt.value)
                if matches:
                    node.inputs.text.is_required = False
                    for match in matches:
                        if match not in node.inputs:
                            raise ValueError(f"Param {match} of node {node.label} should be defined and set")

    def validate_params(self):
        """
        This method will check if all required params are either set or linked

        :raises ValueError: if the pipeline is not valid
        """
        for node in self.nodes:
            self.special_prompt_validation(node)
            for param in node.inputs:
                if param.is_required and not self.is_param_set(node, param):
                    raise ValueError(f"Param {param.code} of node {node.label} is required")

    def validate(self):
        """
        Validate the pipeline. This method will validate the pipeline by
        series of checks:
        - Validate all nodes are linked correctly
        - Validate all required params are set or linked

        Any other validation checks can be added here.

        :raises ValueError: if the pipeline is not valid
        """
        self.validate_nodes()
        self.validate_params()

    def get_link(self, from_node: int, to_node: int) -> Link:
        """
        Get the link between two nodes. This method will return the link
        between two nodes.

        :param from_node: the from node number
        :param to_node: the to node number
        :return: the link
        """
        return next(
            (link for link in self.links if link.from_node == from_node and link.to_node == to_node),
            None,
        )

    def get_node(self, node_number: int) -> Node:
        """
        Get the node by its number. This method will return the node with the
        given number.

        :param node_number: the node number
        :return: the node
        """
        return next((node for node in self.nodes if node.number == node_number), None)

    def auto_infer(self):
        """
        Automatically infer the data types of the nodes in the pipeline.
        This method will automatically infer the data types of the nodes in the
        pipeline by traversing the pipeline and setting the data types of the
        nodes based on the data types of the connected nodes.
        """
        for link in self.links:
            link.auto_infer()

    def asset(self, asset_id: str, *args, asset_class: Type[T] = AssetNode, **kwargs) -> T:
        """
        Shortcut to create an asset node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return asset_class(asset_id, *args, pipeline=self, **kwargs)

    def utility(self, asset_id: str, *args, asset_class: Type[T] = Utility, **kwargs) -> T:
        """
        Shortcut to create an utility nodes for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        if not issubclass(asset_class, Utility):
            raise ValueError("`asset_class` should be a subclass of `Utility` class")

        return asset_class(asset_id, *args, pipeline=self, **kwargs)

    def decision(self, *args, **kwargs) -> Decision:
        """
        Shortcut to create an decision node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return Decision(*args, pipeline=self, **kwargs)

    def script(self, *args, **kwargs) -> Script:
        """
        Shortcut to create an script node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return Script(*args, pipeline=self, **kwargs)

    def input(self, *args, **kwargs) -> Input:
        """
        Shortcut to create an input node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return Input(*args, pipeline=self, **kwargs)

    def output(self, *args, **kwargs) -> Output:
        """
        Shortcut to create an output node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return Output(*args, pipeline=self, **kwargs)

    def router(self, routes: Tuple[DataType, Node], *args, **kwargs) -> Router:
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
        return Router(*args, pipeline=self, **kwargs)

    def bare_reconstructor(self, *args, **kwargs) -> BareReconstructor:
        """
        Shortcut to create an reconstructor node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return BareReconstructor(*args, pipeline=self, **kwargs)

    def bare_segmentor(self, *args, **kwargs) -> BareSegmentor:
        """
        Shortcut to create an segmentor node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return BareSegmentor(*args, pipeline=self, **kwargs)

    def metric(self, *args, **kwargs) -> BareMetric:
        """
        Shortcut to create an metric node for the current pipeline.
        All params will be passed as keyword arguments to the node
        constructor.

        :param kwargs: keyword arguments
        :return: the node
        """
        return BareMetric(*args, pipeline=self, **kwargs)
