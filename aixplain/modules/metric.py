__author__ = "shreyassharma"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: October 25th 2022
Description:
    Metric Class
"""

from typing import Optional, Text, List, Union
from aixplain.modules.asset import Asset
from aixplain.utils.file_utils import convert_list_to_s3_link

class Metric(Asset):
    """Represents a metric to be computed on one or more peices of data. It is usually linked to a machine learning task.

    Attributes:
        id (Text): ID of the Metric
        name (Text): Name of the Metric
        description (Text): Description of the Metric
        supplier (Text, optional): author of the Metric. Defaults to "aiXplain".
        version (Text, optional): Metric version. Defaults to "1.0".
        additional_info: Any additional Metric info to be saved

    """

    def __init__(
        self,
        id: Text,
        name: Text,
        supplier: Text,
        is_reference_required: bool,
        is_source_required: bool,
        cost: float,
        function: Text,
        normalization_options: list = [],
        **additional_info,
    ) -> None:
        """Create a Metric with the necessary information

        Args:
            id (Text): ID of the Metric
            name (Text): Name of the Metric
            supplier (Text): author of the Metric
            is_reference_required (bool): does the metric use reference
            is_source_required (bool): does the metric use source
            cost (float): price of the metric
            normalization_options(list, [])
            **additional_info: Any additional Metric info to be saved
        """
        super().__init__(id, name, description="", supplier=supplier, version="1.0", cost=cost)
        self.is_source_required = is_source_required
        self.is_reference_required = is_reference_required
        self.normalization_options = normalization_options
        self.function = function
        self.additional_info = additional_info
        self.override_api_key = None

    def __repr__(self) -> str:
        return f"<Metric {self.name}>"

    def add_normalization_options(self, normalization_options: List[str]):
        """Add a given set of normalization options to be used while benchmarking

        Args:
            normalization_options (List[str]): List of normalization options to be added
        """
        self.normalization_options.append(normalization_options)

    def run(
        self,
        hypothesis: Optional[Union[str, List[str]]] = None,
        source: Optional[Union[str, List[str]]] = None,
        reference: Optional[Union[str, List[str]]] = None,
        timeout: float = 300,
        wait_time: float = 0.5,
        send_payload_as_files: bool = False
    ):
        """Run the metric to calculate the scores.

        Args:
            hypothesis (Optional[Union[str, List[str]]], optional): Can give a single hypothesis or a list of hypothesis for metric calculation. Defaults to None.
            source (Optional[Union[str, List[str]]], optional): Can give a single source or a list of sources for metric calculation. Defaults to None.
            reference (Optional[Union[str, List[str]]], optional): Can give a single reference or a list of references for metric calculation. Defaults to None.
            timeout (float, optional): total polling time. Defaults to 300.
            wait_time (float, optional): wait time in seconds between polling calls. Defaults to 0.5.
            send_payload_as_files (bool, optional): send large payloads as files. Defaults to False
        """
        from aixplain.factories.model_factory import ModelFactory

        model = ModelFactory.get(self.id)
        payload = {
            "function": self.function,
            "supplier": self.supplier,
            "version": self.name,
        }
        if hypothesis is not None:
            if type(hypothesis) is str:
                hypothesis = [hypothesis]
            if send_payload_as_files:
                hypothesis = convert_list_to_s3_link(hypothesis)
            payload["hypotheses"] = hypothesis
        if self.is_source_required and source is not None:
            if type(source) is str:
                source = [source]
            if send_payload_as_files:
                source = convert_list_to_s3_link(source)
            payload["sources"] = source
        if self.is_reference_required and reference is not None:
            if type(reference) is str:
                reference = [[reference]]
            elif type(reference[0]) is str:
                reference = [[ref] for ref in reference]
            if send_payload_as_files:
                reference = convert_list_to_s3_link(reference)
            payload["references"] = reference
        
        if self.override_api_key is not None:
            model.api_key = self.override_api_key
        return model.run(payload, timeout=timeout, wait_time=wait_time)
