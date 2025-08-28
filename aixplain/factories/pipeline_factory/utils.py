__author__ = "aixplain"
import logging

from aixplain.enums import DataType
import aixplain.utils.config as config
from aixplain.modules.pipeline import Pipeline
from aixplain.modules.pipeline.designer import (
    Input,
    Output,
    BareAsset,
    BareMetric,
    Decision,
    Router,
    Route,
    Script,
    Link,
    BareSegmentor,
    BareReconstructor,
)
from typing import Dict


def build_from_response(response: Dict, load_architecture: bool = False) -> Pipeline:
    """Convert API response into a Pipeline object.

    This function creates a Pipeline object from an API response, optionally loading
    its full architecture including nodes and links. The architecture can include
    various node types like Input, Output, BareAsset, BareMetric, Decision, Router,
    Script, BareSegmentor, and BareReconstructor.

    Args:
        response (Dict): API response containing pipeline information including:
            - id: Pipeline identifier
            - name: Pipeline name
            - api_key: Optional API key
            - status: Pipeline status (defaults to "draft")
            - nodes: Optional list of node configurations
            - links: Optional list of link configurations
        load_architecture (bool, optional): Whether to load the full pipeline
            architecture including nodes and links. Defaults to False.

    Returns:
        Pipeline: Instantiated pipeline object. If load_architecture is True,
            includes all configured nodes and links. If architecture loading fails,
            returns a pipeline with empty nodes and links lists.

    Note:
        When loading architecture, decision nodes with passthrough parameters are
        processed first to ensure proper parameter linking.
    """
    if "api_key" not in response:
        response["api_key"] = config.TEAM_API_KEY

    # instantiating pipeline generic info
    pipeline = Pipeline(
        id=response["id"], name=response["name"], api_key=response["api_key"], status=response.get("status", "draft")
    )
    if load_architecture is True:
        try:
            # instantiating nodes
            for node_json in response["nodes"]:
                if node_json["type"].lower() == "input":
                    node = Input(
                        data=node_json["data"] if "data" in node_json else None,
                        data_types=[DataType(dt) for dt in node_json["dataType"]],
                    )
                elif node_json["type"].lower() == "asset":
                    if node_json["functionType"] == "metric":
                        node = BareMetric(asset_id=node_json["assetId"])
                    elif node_json["functionType"] == "reconstructor":
                        node = BareReconstructor(asset_id=node_json["assetId"])
                    elif node_json["functionType"] == "segmentor":
                        node = BareSegmentor(asset_id=node_json["assetId"])
                    else:
                        node = BareAsset(asset_id=node_json["assetId"])
                elif node_json["type"].lower() == "decision":
                    node = Decision(routes=[Route(**route) for route in node_json["routes"]])
                elif node_json["type"].lower() == "router":
                    node = Router(routes=[Route(**route) for route in node_json["routes"]])
                elif node_json["type"].lower() == "script":
                    node = Script(
                        fileId=node_json["fileId"],
                        fileMetadata=node_json["fileMetadata"],
                    )
                elif node_json["type"].lower() == "output":
                    node = Output()

                if "inputValues" in node_json:
                    [
                        node.inputs.create_param(
                            data_type=(DataType(input_param["dataType"]) if "dataType" in input_param else None),
                            code=input_param["code"],
                            value=(input_param["value"] if "value" in input_param else None),
                            is_required=(input_param["isRequired"] if "isRequired" in input_param else False),
                        )
                        for input_param in node_json["inputValues"]
                        if input_param["code"] not in node.inputs
                    ]
                if "outputValues" in node_json:
                    [
                        node.outputs.create_param(
                            data_type=(DataType(output_param["dataType"]) if "dataType" in output_param else None),
                            code=output_param["code"],
                            value=(output_param["value"] if "value" in output_param else None),
                            is_required=(output_param["isRequired"] if "isRequired" in output_param else False),
                        )
                        for output_param in node_json["outputValues"]
                        if output_param["code"] not in node.outputs
                    ]
                if "customInputs" in node_json:
                    for custom_input in node_json["customInputs"]:
                        node.inputs.create_param(
                            data_type=custom_input.get("dataType"),
                            code=custom_input["code"],
                            value=custom_input.get("value"),
                            is_required=custom_input.get("isRequired", True),
                        )
                node.number = node_json["number"]
                node.label = node_json["label"]
                pipeline.add_node(node)

            # Decision nodes' output parameters are defined based on their
            # input parameters linked. So here we have to make sure that
            # decision nodes (having passthrough parameter) should be first
            # linked
            link_jsons = response["links"][:]
            decision_links = []
            for link_json in link_jsons:
                for pm in link_json["paramMapping"]:
                    if pm["to"] == "passthrough":
                        decision_link_index = link_jsons.index(link_json)
                        decision_link = link_jsons.pop(decision_link_index)
                        decision_links.append(decision_link)

            link_jsons = decision_links + link_jsons

            # instantiating links
            for link_json in link_jsons:
                for param_mapping in link_json["paramMapping"]:
                    link = Link(
                        from_node=pipeline.get_node(link_json["from"]),
                        to_node=pipeline.get_node(link_json["to"]),
                        from_param=param_mapping["from"],
                        to_param=param_mapping["to"],
                    )
                    pipeline.add_link(link)
        except Exception as e:
            logging.warning("Error loading pipeline architecture:, error: %s", e)
            pipeline.nodes = []
            pipeline.links = []
    return pipeline
