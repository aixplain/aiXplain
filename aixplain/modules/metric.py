"""Copyright 2022 The aiXplain SDK authors.

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
from aixplain.enums import Supplier


class Metric(Asset):
    """A class representing a metric for evaluating machine learning model outputs.

    This class extends Asset to provide functionality for computing evaluation metrics
    on one or more pieces of data. Each metric is typically associated with a specific
    machine learning task and can require different inputs (e.g., reference text for
    translation metrics).

    Attributes:
        id (Text): ID of the metric.
        name (Text): Name of the metric.
        supplier (Text): Author/provider of the metric.
        is_reference_required (bool): Whether the metric requires reference data.
        is_source_required (bool): Whether the metric requires source data.
        cost (float): Cost per metric computation.
        function (Text): The function identifier for this metric.
        normalization_options (list): List of available normalization options.
        description (Text): Description of the metric.
        version (Text): Version of the metric implementation.
        additional_info (dict): Additional metric-specific information.
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
        """Initialize a new Metric instance.

        Args:
            id (Text): ID of the metric.
            name (Text): Name of the metric.
            supplier (Text): Author/provider of the metric.
            is_reference_required (bool): Whether the metric requires reference data for computation.
            is_source_required (bool): Whether the metric requires source data for computation.
            cost (float): Cost per metric computation.
            function (Text): The function identifier for this metric.
            normalization_options (list, optional): List of available normalization options.
                Defaults to empty list.
            **additional_info: Additional metric-specific information to be stored.
        """
        super().__init__(id, name, description="", supplier=supplier, version="1.0", cost=cost)
        self.is_source_required = is_source_required
        self.is_reference_required = is_reference_required
        self.normalization_options = normalization_options
        self.function = function
        self.additional_info = additional_info

    def __repr__(self) -> str:
        """Return a string representation of the Metric instance.

        Returns:
            str: A string in the format "<Metric name>".
        """
        return f"<Metric {self.name}>"

    def add_normalization_options(self, normalization_options: List[str]) -> None:
        """Add normalization options to be used during metric computation.

        This method appends new normalization options to the existing list of options.
        These options can be used to normalize inputs or outputs during benchmarking.

        Args:
            normalization_options (List[str]): List of normalization options to add.
                Each option should be a valid normalization identifier.
        """
        self.normalization_options.append(normalization_options)

    def run(
        self,
        hypothesis: Optional[Union[str, List[str]]] = None,
        source: Optional[Union[str, List[str]]] = None,
        reference: Optional[Union[str, List[str]]] = None,
    ) -> dict:
        """Run the metric to calculate scores for the provided inputs.

        This method computes metric scores based on the provided hypothesis, and optionally
        source and reference data. The inputs can be either single strings or lists of strings.

        Args:
            hypothesis (Optional[Union[str, List[str]]], optional): The hypothesis/output to evaluate.
                Can be a single string or a list of strings. Defaults to None.
            source (Optional[Union[str, List[str]]], optional): The source data for evaluation.
                Only used if is_source_required is True. Can be a single string or a list
                of strings. Defaults to None.
            reference (Optional[Union[str, List[str]]], optional): The reference data for evaluation.
                Only used if is_reference_required is True. Can be a single string or a list
                of strings. Defaults to None.

        Returns:
            dict: A dictionary containing the computed metric scores and any additional
                computation metadata.

        Note:
            The method automatically handles conversion of single strings to lists and
            proper formatting of references for multi-reference scenarios.
        """
        from aixplain.factories.model_factory import ModelFactory

        model = ModelFactory.get(self.id)
        payload = {
            "function": self.function,
            "supplier": self.supplier.value if isinstance(self.supplier, Supplier) else self.supplier,
            "version": self.name,
        }
        if hypothesis is not None:
            if type(hypothesis) is str:
                hypothesis = [hypothesis]
            payload["hypotheses"] = hypothesis
        if self.is_source_required and source is not None:
            if type(source) is str:
                source = [source]
            payload["sources"] = source
        if self.is_reference_required and reference is not None:
            if type(reference) is str:
                reference = [[reference]]
            elif type(reference[0]) is str:
                reference = [[ref] for ref in reference]
            payload["references"] = reference
        return model.run(payload)
