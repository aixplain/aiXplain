__author__ = "aiXplain"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: November 25th 2024
Description:
    Pipeline Asset Class
"""

import time
import json
import os
import logging
from aixplain.enums import AssetStatus, ResponseStatus
from aixplain.modules import Asset
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from typing import Dict, Optional, Text, Union
from urllib.parse import urljoin
from aixplain.modules.pipeline.response import PipelineResponse
from aixplain.modules.mixins import DeployableMixin
from aixplain.exceptions import get_error_from_status_code


class Pipeline(Asset, DeployableMixin):
    """Representing a custom pipeline that was created on the aiXplain Platform

    Attributes:
        id (Text): ID of the Pipeline
        name (Text): Name of the Pipeline
        api_key (Text): Team API Key to run the Pipeline.
        url (Text, optional): running URL of platform. Defaults to config.BACKEND_URL.
        supplier (Text, optional): Pipeline supplier. Defaults to "aiXplain".
        version (Text, optional): version of the pipeline. Defaults to "1.0".
        status (AssetStatus, optional): Pipeline status. Defaults to AssetStatus.DRAFT.
        **additional_info: Any additional Pipeline info to be saved
    """

    VERSION_3_0 = "3.0"
    VERSION_2_0 = "2.0"

    def __init__(
        self,
        id: Text,
        name: Text,
        api_key: Text,
        url: Text = config.BACKEND_URL,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        status: AssetStatus = AssetStatus.DRAFT,
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
            status (AssetStatus, optional): Pipeline status. Defaults to AssetStatus.DRAFT.
            **additional_info: Any additional Pipeline info to be saved
        """
        if not name:
            raise ValueError("Pipeline name is required")

        super().__init__(id, name, "", supplier, version)
        self.api_key = api_key
        self.url = f"{url}/assets/pipeline/execution/run"
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status
        self.additional_info = additional_info

    def __polling(
        self,
        poll_url: Text,
        name: Text = "pipeline_process",
        wait_time: float = 1.0,
        timeout: float = 20000.0,
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
        response_body = {"status": ResponseStatus.FAILED, "completed": False}

        while not response_body["completed"] and (end - start) < timeout:
            try:
                response_body = self.poll(poll_url, name=name)
                logging.debug(f"Polling for Pipeline: Status of polling for {name} : {response_body}")
                end = time.time()
                if not response_body["completed"]:
                    time.sleep(wait_time)
                    if wait_time < 60:
                        wait_time *= 1.1
            except Exception:
                logging.error(f"Polling for Pipeline '{self.id}': polling for {name} ({poll_url}): Continue")
                break
        if response_body["status"] == ResponseStatus.SUCCESS:
            try:
                logging.debug(
                    f"Polling for Pipeline '{self.id}' - Final status of polling for {name} ({poll_url}): SUCCESS - {response_body}"
                )
            except Exception:
                logging.error(
                    f"Polling for Pipeline '{self.id}' - Final status of polling for {name} ({poll_url}): ERROR - {response_body}"
                )
        else:
            logging.error(
                f"Polling for Pipeline '{self.id}' - Final status of polling for {name} ({poll_url}): No response in {timeout} seconds - {response_body}"
            )
        return response_body

    def poll(
        self, poll_url: Text, name: Text = "pipeline_process", response_version: Text = "v2"
    ) -> Union[Dict, PipelineResponse]:
        """Poll the platform to check whether an asynchronous call is done.

        Args:
            poll_url (Text): polling URL
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".

        Returns:
            Dict: response obtained by polling call
        """

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        r = _request_with_retry("get", poll_url, headers=headers)
        try:
            resp = r.json()
            if "data" in resp and isinstance(resp["data"], str):
                try:
                    resp["data"] = json.loads(resp["data"])["response"]
                except Exception:
                    resp = r.json()
            logging.info(f"Single Poll for Pipeline '{self.id}' - Status of polling for {name} ({poll_url}): {resp}")
            if response_version == "v1":
                return resp
            status = ResponseStatus(resp.pop("status", "failed"))
            response = PipelineResponse(
                status=status,
                error=resp.pop("error", None),
                elapsed_time=resp.pop("elapsed_time", 0),
                **resp,
            )
            return response

        except Exception:
            return PipelineResponse(
                status=ResponseStatus.FAILED,
                error=resp.pop("error", None),
                elapsed_time=resp.pop("elapsed_time", 0),
                **resp,
            )

    def run(
        self,
        data: Union[Text, Dict],
        data_asset: Optional[Union[Text, Dict]] = None,
        name: Text = "pipeline_process",
        timeout: float = 20000.0,
        wait_time: float = 1.0,
        version: Optional[Text] = None,
        response_version: Text = "v2",
        **kwargs,
    ) -> Union[Dict, PipelineResponse]:
        """Run the pipeline synchronously and wait for results.

        This method executes the pipeline with the provided input data and waits
        for completion. It handles both direct data input and data assets, with
        support for polling and timeout.

        Args:
            data (Union[Text, Dict]): The input data for the pipeline. Can be:
                - A string (file path, URL, or raw data)
                - A dictionary mapping node labels to input data
            data_asset (Optional[Union[Text, Dict]], optional): Data asset(s) to
                process. Can be a single asset ID or a dict mapping node labels
                to asset IDs. Defaults to None.
            name (Text, optional): Identifier for this pipeline run. Used for
                logging. Defaults to "pipeline_process".
            timeout (float, optional): Maximum time in seconds to wait for
                completion. Defaults to 20000.0.
            wait_time (float, optional): Initial time in seconds between polling
                attempts. May increase over time. Defaults to 1.0.
            version (Optional[Text], optional): Specific pipeline version to run.
                Defaults to None.
            response_version (Text, optional): Response format version ("v1" or
                "v2"). Defaults to "v2".
            **kwargs: Additional keyword arguments passed to the pipeline.

        Returns:
            Union[Dict, PipelineResponse]: If response_version is:
                - "v1": Dictionary with status, error (if any), and elapsed time
                - "v2": PipelineResponse object with structured response data

        Raises:
            Exception: If the pipeline execution fails, times out, or encounters
                errors during polling.

        Note:
            - The method starts with run_async and then polls for completion
            - wait_time may increase up to 60 seconds between polling attempts
            - For v2 responses, use PipelineResponse methods to access results
        """
        start = time.time()
        try:
            response = self.run_async(data, data_asset=data_asset, name=name, version=version, **kwargs)
            if response["status"] == ResponseStatus.FAILED:
                end = time.time()
                if response_version == "v1":
                    return {
                        "status": "failed",
                        "error": response.get("error", "ERROR"),
                        "elapsed_time": end - start,
                        **kwargs,
                    }
                return PipelineResponse(
                    status=ResponseStatus.FAILED,
                    error={"error": response.get("error", "ERROR"), "status": "ERROR"},
                    elapsed_time=end - start,
                    **kwargs,
                )
            poll_url = response["url"]
            polling_response = self.__polling(poll_url, name=name, timeout=timeout, wait_time=wait_time)
            end = time.time()
            status = ResponseStatus(polling_response["status"])
            completed = polling_response["completed"]
            if response_version == "v1":
                polling_response["elapsed_time"] = end - start
                return polling_response
            status = ResponseStatus(polling_response.status)
            return PipelineResponse(
                status=status,
                completed=completed,
                error=polling_response.error,
                elapsed_time=end - start,
                data=getattr(polling_response, "data", {}),
                **kwargs,
            )

        except Exception as e:
            error_message = f"Error in request for {name}: {str(e)}"
            logging.error(error_message)
            logging.exception(error_message)
            end = time.time()
            if response_version == "v1":
                return {
                    "status": "failed",
                    "error": error_message,
                    "elapsed_time": end - start,
                    **kwargs,
                }
            return PipelineResponse(
                status=ResponseStatus.FAILED,
                error={"error": error_message, "status": "ERROR"},
                elapsed_time=end - start,
                **kwargs,
            )

    def __prepare_payload(
        self,
        data: Union[Text, Dict],
        data_asset: Optional[Union[Text, Dict]] = None,
    ) -> Dict:
        """Prepare and validate the pipeline execution payload.

        This internal method processes input data and data assets into a format
        suitable for pipeline execution. It handles various input formats and
        performs validation of data assets.

        Args:
            data (Union[Text, Dict]): The input data to process. Can be:
                - A string (file path, URL, or raw data)
                - A dictionary mapping node labels to input data
            data_asset (Optional[Union[Text, Dict]], optional): Data asset(s) to
                process. Can be:
                - A single asset ID (string)
                - A dictionary mapping node labels to asset IDs
                Defaults to None.

        Returns:
            Dict: A formatted payload containing:
                - data: List of node inputs with values and IDs
                - dataAsset (if applicable): Asset references with corpus/dataset IDs

        Raises:
            Exception: In various cases:
                - If data and data_asset format mismatch
                - If specified data asset doesn't exist
                - If specified data isn't found in the data asset
                - If data format is invalid

        Note:
            - For data assets, validates both asset existence and data presence
            - Handles both single-input and multi-input scenarios
            - Automatically uploads local files to temporary storage
        """
        from aixplain.factories import (
            CorpusFactory,
            DatasetFactory,
            FileFactory,
        )

        # if an input data asset is provided, just handle the data
        if data_asset is None:
            # upload the data when a local path is provided
            data = FileFactory.to_link(data)
            if isinstance(data, dict):
                payload = data
                for key in payload:
                    payload[key] = {"value": payload[key]}

                for node_label in payload:
                    payload[node_label]["nodeId"] = node_label

                payload = {"data": list(payload.values())}
            else:
                try:
                    payload = json.loads(data)
                    if isinstance(payload, dict) is False:
                        if isinstance(payload, int) is True or isinstance(payload, float) is True:
                            payload = str(payload)
                        payload = {"data": payload}
                except Exception:
                    payload = {"data": data}
        else:
            payload = {}
            if isinstance(data_asset, str) is True:
                data_asset = {"1": data_asset}

                # make sure data asset and data are provided in the same format,
                # mostly when in a multi-input scenario, where a dictionary should be provided.
                if isinstance(data, dict) is True:
                    raise Exception(
                        'Pipeline Run Error: Similar to "data", please specify the node input label where the data asset should be set in "data_asset".'
                    )
                else:
                    data = {"1": data}
            elif isinstance(data, str) is True:
                raise Exception(
                    'Pipeline Run Error: Similar to "data_asset", please specify the node input label where the data should be set in "data".'
                )

            # validate the existence of data asset and data
            for node_label in data_asset:
                asset_payload = {"dataAsset": {}}
                data_asset_found, data_found = True, False
                try:
                    dasset = CorpusFactory.get(str(data_asset[node_label]))
                    asset_payload["dataAsset"]["corpus_id"] = dasset.id
                    if len([d for d in dasset.data if d.id == data[node_label]]) > 0:
                        data_found = True
                except Exception:
                    try:
                        dasset = DatasetFactory.get(str(data_asset[node_label]))
                        asset_payload["dataAsset"]["dataset_id"] = dasset.id

                        source_data_list = [
                            dfield for dfield in dasset.source_data if dasset.source_data[dfield].id == data[node_label]
                        ]

                        if len(source_data_list) > 0:
                            data_found = True
                        else:
                            for target in dasset.target_data:
                                for target_row in dasset.target_data[target]:
                                    if target_row.id == data[node_label]:
                                        data_found = True
                                        break
                                if data_found is True:
                                    break
                    except Exception:
                        data_asset_found = False
                if data_asset_found is False:
                    raise Exception(
                        f'Pipeline Run Error: Data Asset "{data_asset[node_label]}" not found. Make sure this asset exists or you have access to it.'
                    )
                elif data_found is False:
                    raise Exception(
                        f'Pipeline Run Error: Data "{data[node_label]}" not found in Data Asset "{data_asset[node_label]}" not found.'
                    )

                asset_payload["dataAsset"]["data_id"] = data[node_label]
                payload[node_label] = asset_payload

            if len(payload) > 1:
                for node_label in payload:
                    payload[node_label]["nodeId"] = node_label
            payload = {"data": list(payload.values())}
        return payload

    def run_async(
        self,
        data: Union[Text, Dict],
        data_asset: Optional[Union[Text, Dict]] = None,
        name: Text = "pipeline_process",
        batch_mode: bool = True,
        version: Optional[Text] = None,
        response_version: Text = "v2",
        **kwargs,
    ) -> Dict:
        """Runs asynchronously a pipeline call.

        Args:
            data (Union[Text, Dict]): link to the input data
            data_asset (Optional[Union[Text, Dict]], optional): Data asset to be processed by the pipeline. Defaults to None.
            name (Text, optional): ID given to a call. Defaults to "pipeline_process".
            batch_mode (bool, optional): Whether to run the pipeline in batch mode or online. Defaults to True.
            version (Optional[Text], optional): Version of the pipeline. Defaults to None.
            response_version (Text, optional): Version of the response. Defaults to "v2".
            kwargs: A dictionary of keyword arguments. The keys are the argument names

        Returns:
            Dict: polling URL in response
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = self.__prepare_payload(data=data, data_asset=data_asset)
        payload["batchmode"] = batch_mode
        payload["version"] = version
        payload.update(kwargs)
        payload = json.dumps(payload)
        call_url = f"{self.url}/{self.id}"
        logging.info(f"Start service for {name}  - {call_url} - {payload}")
        r = _request_with_retry("post", call_url, headers=headers, data=payload)
        resp = None
        try:
            if 200 <= r.status_code < 300:
                resp = r.json()
                logging.info(f"Result of request for {name}  - {r.status_code} - {resp}")
                if response_version == "v1":
                    return resp
                res = PipelineResponse(
                    status=ResponseStatus(resp.pop("status", "failed")),
                    url=resp["url"],
                    elapsed_time=None,
                    **kwargs,
                )
                return res

            else:
                status_code = r.status_code
                error = get_error_from_status_code(status_code)

                logging.error(f"Error in request for {name} (Pipeline ID '{self.id}') - {r.status_code}: {error}")
                if response_version == "v1":
                    return {
                        "status": "failed",
                        "error": error.message,
                        "elapsed_time": None,
                        **kwargs,
                    }
                return PipelineResponse(
                    status=ResponseStatus.FAILED,
                    error={"error": error.message, "status": "ERROR"},
                    elapsed_time=None,
                    **kwargs,
                )
        except Exception as e:
            if response_version == "v1":
                return {
                    "status": "failed",
                    "error": str(e),
                    "elapsed_time": None,
                    **kwargs,
                }
            return PipelineResponse(
                status=ResponseStatus.FAILED,
                error={"error": str(e), "status": "ERROR"},
                elapsed_time=None,
                **kwargs,
            )

    def update(
        self,
        pipeline: Union[Text, Dict],
        save_as_asset: bool = False,
        api_key: Optional[Text] = None,
        name: Optional[Text] = None,
    ):
        """Update Pipeline

        Args:
            pipeline (Union[Text, Dict]): Pipeline as a Python dictionary or in a JSON file
            save_as_asset (bool, optional): Save as asset (True) or draft (False). Defaults to False.
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Raises:
            Exception: Make sure the pipeline to be save is in a JSON file.
        """
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. " "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        try:
            if isinstance(pipeline, str) is True:
                _, ext = os.path.splitext(pipeline)
                assert (
                    os.path.exists(pipeline) and ext == ".json"
                ), "Pipeline Update Error: Make sure the pipeline to be saved is in a JSON file."
                with open(pipeline) as f:
                    pipeline = json.load(f)

            for i, node in enumerate(pipeline["nodes"]):
                if "functionType" in node:
                    pipeline["nodes"][i]["functionType"] = pipeline["nodes"][i]["functionType"].lower()
            # prepare payload
            status = "draft"
            if save_as_asset is True:
                status = "onboarded"
            if name:
                self.name = name
            payload = {
                "name": self.name,
                "status": status,
                "architecture": pipeline,
            }
            url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{self.id}")
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for PUT Update Pipeline - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("put", url, headers=headers, json=payload)
            response = r.json()
            logging.info(f"Pipeline {response['id']} Updated.")
        except Exception as e:
            raise Exception(e)

    def delete(self) -> None:
        """Delete this pipeline from the platform.

        This method permanently removes the pipeline from the aiXplain platform.
        The operation cannot be undone.

        Raises:
            Exception: If deletion fails, which can happen if:
                - The pipeline doesn't exist
                - The user doesn't have permission to delete it
                - The API request fails
                - The server returns a non-200 status code

        Note:
            - This operation is permanent and cannot be undone
            - Only the pipeline owner can delete it
            - Uses the team API key for authentication
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{self.id}")
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for DELETE Pipeline  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Pipeline Deletion Error: Make sure the pipeline exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

    def save(
        self,
        pipeline: Optional[Union[Text, Dict]] = None,
        save_as_asset: bool = False,
        api_key: Optional[Text] = None,
    ):
        """Update and Save Pipeline

        Args:
            pipeline (Optional[Union[Text, Dict]]): Pipeline as a Python dictionary or in a JSON file
            save_as_asset (bool, optional): Save as asset (True) or draft (False). Defaults to False.
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Raises:
            Exception: Make sure the pipeline to be save is in a JSON file.
        """
        try:
            if pipeline is None:
                pipeline = self.to_dict()
            else:
                if isinstance(pipeline, str) is True:
                    _, ext = os.path.splitext(pipeline)
                    assert (
                        os.path.exists(pipeline) and ext == ".json"
                    ), "Pipeline Update Error: Make sure the pipeline to be saved is in a JSON file."
                    with open(pipeline) as f:
                        pipeline = json.load(f)
                self.update(pipeline=pipeline, save_as_asset=save_as_asset, api_key=api_key)

            for i, node in enumerate(pipeline["nodes"]):
                if "functionType" in node:
                    pipeline["nodes"][i]["functionType"] = pipeline["nodes"][i]["functionType"].lower()
            # prepare payload
            status = "draft"
            if save_as_asset is True:
                status = "onboarded"
            payload = {
                "name": self.name,
                "status": status,
                "architecture": pipeline,
            }

            url = urljoin(config.BACKEND_URL, "sdk/pipelines")
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for Save Pipeline - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            response = r.json()
            self.id = response["id"]
            logging.info(f"Pipeline {response['id']} Saved.")
        except Exception as e:
            raise Exception(e)

    def deploy(self, api_key: Optional[Text] = None) -> None:
        """Deploy the Pipeline.

        This method overrides the deploy method in DeployableMixin to handle
        Pipeline-specific deployment functionality.

        Args:
            api_key (Optional[Text], optional): Team API Key to deploy the Pipeline. Defaults to None.
        """
        self._validate_deployment_readiness()
        pipeline = self.to_dict()
        previous_status = self.status
        try:
            self.status = AssetStatus.ONBOARDED
            self.update(pipeline=pipeline, save_as_asset=True, api_key=api_key, name=self.name)
        except Exception as e:
            self.status = previous_status
            raise Exception(f"Error deploying because of backend error: {e}") from e

    def __repr__(self):
        """Return a string representation of the Pipeline instance.

        Returns:
            str: A string in the format "Pipeline: <name> (id=<id>)".
        """
        return f"Pipeline: {self.name} (id={self.id})"
