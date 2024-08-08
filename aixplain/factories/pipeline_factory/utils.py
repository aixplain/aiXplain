__author__ = "aixplain"

import aixplain.utils.config as config
import logging
from aixplain.modules.pipeline import Pipeline
from aixplain.modules.pipeline.designer import (
    Decision,
    Input,
    Output,
    AssetNode,
    BaseSegmentor,
    BaseReconstructor,
    Router,
    Route,
    Script,
    Link,
)
from typing import Dict, List


def get_typed_nodes(response: Dict, type: str) -> List[Dict]:
    # read "nodes" field from response and return the nodes that are marked by "type": type
    return [
        node
        for node in response["nodes"]
        if node["type"].lower() == type.lower()
    ]


def build_from_response(
    response: Dict, load_architecture: bool = False
) -> Pipeline:
    """Converts response Json to 'Pipeline' object

    Args:
        response (Dict): Json from API
        load_architecture (bool, optional): If True, the architecture will be loaded. Defaults to False.

    Returns:
        Pipeline: Coverted 'Pipeline' object
    """
    if "api_key" not in response:
        response["api_key"] = config.TEAM_API_KEY
    input = get_typed_nodes(response, "input")
    output = get_typed_nodes(response, "output")

    # instantiating pipeline generic info
    print(response)
    pipeline = Pipeline(response["id"], response["name"], response["api_key"])
    if load_architecture is True:
        try:
            # instantiating nodes
            for node_json in response["nodes"]:
                if node_json["type"].lower() == "input":
                    node = Input()
                elif node_json["type"].lower() == "asset":
                    node = AssetNode(asset_id=node_json["assetId"])
                elif node_json["type"].lower() == "segmentor":
                    node = BaseSegmentor()
                elif node_json["type"].lower() == "reconstructor":
                    node = BaseReconstructor()
                elif node_json["type"].lower() == "decision":
                    node = Decision()
                elif node_json["type"].lower() == "router":
                    node = Router(
                        routes=[
                            Route(**route) for route in node_json["routes"]
                        ]
                    )
                elif node_json["type"].lower() == "script":
                    node = Script(fileId=node_json["fileId"])
                elif node_json["type"].lower() == "output":
                    node = Output()
                node.number = node_json["number"]
                node.label = node_json["label"]
                pipeline.add_node(node)

            # instantiating links
            for link_json in response["links"]:
                link = Link(
                    from_node=pipeline.get_node(link_json["from"]),
                    to_node=pipeline.get_node(link_json["to"]),
                    from_param=link_json["paramMapping"][0]["from"],
                    to_param=link_json["paramMapping"][0]["to"],
                    # paramMapping=[ParamMapping(from_param=param["from"], to_param=param["to"]) for param in link_json["paramMapping"]],
                )
                pipeline.add_link(link)
        except Exception:
            logging.warning("Error loading pipeline architecture")
            pipeline.nodes = []
            pipeline.links = []
    return pipeline
