import time
import json
import os
import logging
from dataclasses import asdict

from aixplain.modules.pipeline.designer.enums import (
    NodeType,
    DataType,
    RouteType,
    Operation,
)
from aixplain.modules.pipeline.designer.base import Node, Link
from aixplain.modules.pipeline.designer.nodes import (
    NodeAsset,
    Decision,
    Script,
    Input,
    Output,
    Route,
    Router,
    Reconstructor,
    Segmentor,
)
from aixplain.modules.asset import Asset
from aixplain.modules.pipeline.utils import prepare_payload
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from typing import Any, Dict, Optional, List, Text, Tuple, Union
from urllib.parse import urljoin


class Pipeline(Asset):
    """Representing a custom pipeline that was created on the aiXplain Platform

    Attributes:
        id (Text): ID of the Pipeline
        name (Text): Name of the Pipeline
        api_key (Text): Team API Key to run the Pipeline.
        url (Text, optional): running URL of platform. Defaults to config.BACKEND_URL.
        supplier (Text, optional): Pipeline supplier. Defaults to "aiXplain".
        version (Text, optional): version of the pipeline. Defaults to "1.0".
        **additional_info: Any additional Pipeline info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        api_key: Text,
        url: Text = config.BACKEND_URL,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        nodes: List[Node] = [],
        links: List[Link] = [],
        instance: Any = None,
        **additional_info,
    ) -> None:
        """Create a Pipeline with the necessary information

        Args:
            id (Text): ID of the Pipeline
            name (Text): Name of the Pipeline
            api_key (Text): Team API Key to run the Pipeline.
            url (Text, optional): running URL of platform. Defaults to config.BACKEND_URL.
            supplier (Text, optional): Pipeline supplier. Defaults to "aiXplain".
            version (Text, optional): version of the pipeline. Defaults to "1.0".
            **additional_info: Any additional Pipeline info to be saved
        """
        super().__init__(id, name, "", supplier, version)
        self.api_key = api_key
        self.url = f"{url}/assets/pipeline/execution/run"
        self.nodes = nodes
        self.links = links
        self.instance = instance
        self.additional_info = additional_info

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
        return NodeAsset(self, *args, **kwargs)

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
        kwargs["pipeline"] = self
        return Router(
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
        obj = {"nodes": [asdict(node) for node in self.nodes], "links": [asdict(link) for link in self.links]}
        for link in obj["links"]:
            link["from"] = link.pop("from_node")
            link["to"] = link.pop("to_node")
            params = link.get("paramMapping", []) or []
            for param in params:
                param["from"] = param.pop("from_param")
                param["to"] = param.pop("to_param")
        return obj

    def __polling(
        self, poll_url: Text, name: Text = "pipeline_process", wait_time: float = 1.0, timeout: float = 20000.0
    ) -> Dict:
        """Keeps polling the platform to check whether an asynchronous call is done.

        Args:
            poll_url (str): polling URL
            name (str, optional): ID given to a call. Defaults to "pipeline_process".
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 1.0.
            timeout (float, optional): total polling time. Defaults to 20000.0.

        Returns:
            dict: response obtained by polling call
        """
        # TO DO: wait_time = to the longest path of the pipeline * minimum waiting time
        logging.debug(f"Polling for Pipeline: Start polling for {name} ")
        start, end = time.time(), time.time()
        completed = False
        response_body = {"status": "FAILED"}
        while not completed and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                logging.debug(f"Polling for Pipeline: Status of polling for {name} : {response_body}")
                completed = response_body["completed"]

                end = time.time()
                if completed is False:
                    time.sleep(wait_time)
                    if wait_time < 60:
                        wait_time *= 1.1
            except Exception:
                logging.error(f"Polling for Pipeline: polling for {name} : Continue")
        if response_body and response_body["status"] == "SUCCESS":
            try:
                logging.debug(f"Polling for Pipeline: Final status of polling for {name} : SUCCESS - {response_body}")
            except Exception:
                logging.error(f"Polling for Pipeline: Final status of polling for {name} : ERROR - {response_body}")
        else:
            logging.error(
                f"Polling for Pipeline: Final status of polling for {name} : No response in {timeout} seconds - {response_body}"
            )
        return response_body

    def poll(self, poll_url: Text, name: Text = "pipeline_process") -> Dict:
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (Text): polling URL
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            Dict: response obtained by polling call
        """

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            logging.info(f"Single Poll for Pipeline: Status of polling for {name} : {resp}")
        except Exception:
            resp = {"status": "FAILED"}
        return resp

    def run(
        self,
        data: Union[Text, Dict],
        data_asset: Optional[Union[Text, Dict]] = None,
        name: Text = "pipeline_process",
        timeout: float = 20000.0,
        wait_time: float = 1.0,
        **kwargs,
    ) -> Dict:
        """Runs a pipeline call.

        Args:
            data (Union[Text, Dict]): link to the input data
            data_asset (Optional[Union[Text, Dict]], optional): Data asset to be processed by the pipeline. Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".
            timeout (float, optional): total polling time. Defaults to 20000.0.
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 1.0.
            kwargs: A dictionary of keyword arguments. The keys are the argument names

        Returns:
            Dict: parsed output from pipeline
        """
        start = time.time()
        try:
            response = self.run_async(data, data_asset=data_asset, name=name, **kwargs)
            if response["status"] == "FAILED":
                end = time.time()
                response["elapsed_time"] = end - start
                return response
            poll_url = response["url"]
            end = time.time()
            response = self.__polling(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            return response
        except Exception as e:
            error_message = f"Error in request for {name}: {str(e)}"
            logging.error(error_message)
            logging.exception(error_message)
            end = time.time()
            return {"status": "FAILED", "error": error_message, "elapsed_time": end - start}

    def run_async(
        self, data: Union[Text, Dict], data_asset: Optional[Union[Text, Dict]] = None, name: Text = "pipeline_process", **kwargs
    ) -> Dict:
        """Runs asynchronously a pipeline call.

        Args:
            data (Union[Text, Dict]): link to the input data
            data_asset (Optional[Union[Text, Dict]], optional): Data asset to be processed by the pipeline. Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".
            kwargs: A dictionary of keyword arguments. The keys are the argument names

        Returns:
            Dict: polling URL in response
        """
        assert self.id != "", "Make sure the pipeline is saved."
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        payload = prepare_payload(data=data, data_asset=data_asset)
        payload.update(kwargs)
        payload = json.dumps(payload)
        call_url = f"{self.url}/{self.id}"
        logging.info(f"Start service for {name}  - {call_url} - {payload}")
        r = _request_with_retry("post", call_url, headers=headers, data=payload)

        resp = None
        try:
            resp = r.json()
            logging.info(f"Result of request for {name}  - {r.status_code} - {resp}")

            poll_url = resp["url"]
            response = {"status": "IN_PROGRESS", "url": poll_url}
        except Exception:
            response = {"status": "FAILED"}
            if resp is not None:
                response["error"] = resp
        return response

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
                if isinstance(node, NodeAsset):
                    contains_asset = True
                if node.number not in link_from_map:
                    raise ValueError(f"Node {node.label} not linked in")
                if node.number not in link_to_map:
                    raise ValueError(f"Node {node.label} not linked out")

        if not contains_input or not contains_output or not contains_asset:
            raise ValueError("Pipeline must contain at least one input, output and asset node")  # noqa

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
                    raise ValueError(f"Param {param.code} of node {node.label} is required")

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
                    raise ValueError(f"Param {param.from_param} not found in node {from_node.label}")  # noqa
                if param.to_param not in to_node.inputs:
                    raise ValueError(f"Param {param.to_param} not found in node {to_node.label}")  # noqa

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

    def auto_infer(self):
        """
        Automatically infer the data types of the nodes in the pipeline.
        This method will automatically infer the data types of the nodes in the
        pipeline by traversing the pipeline and setting the data types of the
        nodes based on the data types of the connected nodes.
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
            if not from_node or not to_node:
                continue  # will be handled by the validation
            for param in link.paramMapping:
                from_param = from_node.outputs[param.from_param]
                to_param = to_node.inputs[param.to_param]
                if not from_param or not to_param:
                    continue  # will be handled by the validation
                # if one of the data types is missing, infer the other one
                dataType = from_param.dataType or to_param.dataType
                from_param.dataType = dataType
                to_param.dataType = dataType

            def infer_data_type(node):
                from aixplain.modules.pipeline.designer.nodes import Input, Output

                if isinstance(node, Input) or isinstance(node, Output):
                    if dataType and dataType not in node.dataType:
                        node.dataType.append(dataType)

            infer_data_type(self)
            infer_data_type(to_node)

    def save(self, save_as_asset: bool = False, api_key: Optional[Text] = None):
        """Save Pipeline

        Args:
            save_as_asset (bool, optional): Save as asset (True) or draft (False). Defaults to False.
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Raises:
            Exception: Make sure the pipeline to be save is in a JSON file.
        """
        self.auto_infer()
        self.validate()
        try:
            pipeline = self.to_dict()

            for i, node in enumerate(pipeline["nodes"]):
                if "functionType" in node and node["functionType"] == "AI":
                    pipeline["nodes"][i]["functionType"] = pipeline["nodes"][i]["functionType"].lower()
            # prepare payload
            status = "draft"
            if save_as_asset is True:
                status = "onboarded"
            payload = {"name": self.name, "status": status, "architecture": pipeline}

            if self.id != "":
                method = "put"
                url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{self.id}")
            else:
                method = "post"
                url = urljoin(config.BACKEND_URL, "sdk/pipelines")
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for Save Pipeline - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry(method, url, headers=headers, json=payload)
            response = r.json()
            self.id = response["id"]
            logging.info(f"Pipeline {response['id']} Saved.")
        except Exception as e:
            raise Exception(e)

    def update(self, pipeline: Union[Text, Dict], save_as_asset: bool = False, api_key: Optional[Text] = None):
        """Update Pipeline

        Args:
            pipeline (Union[Text, Dict]): Pipeline as a Python dictionary or in a JSON file
            save_as_asset (bool, optional): Save as asset (True) or draft (False). Defaults to False.
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Raises:
            Exception: Make sure the pipeline to be save is in a JSON file.
        """
        try:
            if isinstance(pipeline, str) is True:
                _, ext = os.path.splitext(pipeline)
                assert (
                    os.path.exists(pipeline) and ext == ".json"
                ), "Pipeline Update Error: Make sure the pipeline to be saved is in a JSON file."
                with open(pipeline) as f:
                    pipeline = json.load(f)

            for i, node in enumerate(pipeline["nodes"]):
                if "functionType" in node and node["functionType"] == "AI":
                    pipeline["nodes"][i]["functionType"] = pipeline["nodes"][i]["functionType"].lower()
            # prepare payload
            status = "draft"
            if save_as_asset is True:
                status = "onboarded"
            payload = {"name": self.name, "status": status, "architecture": pipeline}
            url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{self.id}")
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for PUT Update Pipeline - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("put", url, headers=headers, json=payload)
            response = r.json()
            logging.info(f"Pipeline {response['id']} Updated.")
        except Exception as e:
            raise Exception(e)

    def delete(self) -> None:
        """Delete Dataset service"""
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{self.id}")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for DELETE Pipeline  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Pipeline Deletion Error: Make sure the pipeline exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")
