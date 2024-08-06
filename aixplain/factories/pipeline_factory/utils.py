__author__ = "aixplain"

import aixplain.utils.config as config

from aixplain.modules.pipeline import Pipeline
from aixplain.modules.pipeline.designer import (
    DataType,
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
    return [node for node in response["nodes"] if node["type"].lower() == type.lower()]


def build_from_response(response: Dict) -> Pipeline:
    """Converts response Json to 'Pipeline' object

    Args:
        response (Dict): Json from API

    Returns:
        Pipeline: Coverted 'Pipeline' object
    """
    if "api_key" not in response:
        response["api_key"] = config.TEAM_API_KEY
    input = get_typed_nodes(response, "input")
    output = get_typed_nodes(response, "output")

    # instantiating pipeline generic info
    pipeline = Pipeline(response["id"], response["name"], response["api_key"], input=input, output=output, nodes=[], links=[])
    # instantiating nodes
    for node_json in response["nodes"]:
        if node_json["type"].lower() == "input":
            node = Input(dataType=[DataType(typ) for typ in node_json["dataType"]])
        elif node_json["type"].lower() == "asset":
            node = AssetNode(assetId=node_json["assetId"])
        elif node_json["type"].lower() == "segmentor":
            node = BaseSegmentor()
        elif node_json["type"].lower() == "reconstructor":
            node = BaseReconstructor()
        elif node_json["type"].lower() == "decision":
            node = Decision()
        elif node_json["type"].lower() == "router":
            node = Router(routes=[Route(**route) for route in node_json["routes"]])
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
            from_node=link_json["from"],
            to_node=link_json["to"],
            from_param=link_json["from_param"][0],
            to_param=link_json["to_param"][0],
            # paramMapping=[ParamMapping(from_param=param["from"], to_param=param["to"]) for param in link_json["paramMapping"]],
        )
        pipeline.add_link(link)
    return pipeline
