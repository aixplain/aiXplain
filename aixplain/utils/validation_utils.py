from pathlib import Path
from typing import Optional, Text, Union, Dict, List

from aixplain.modules.metadata import MetaData
from aixplain.enums.function import FunctionInputOutput, Function
from aixplain.enums.data_type import DataType


def dataset_onboarding_validation(
    input_schema: List[Union[Dict, MetaData]],
    output_schema: List[Union[Dict, MetaData]],
    function: Function,
    content_path: Union[Union[Text, Path], List[Union[Text, Path]]] = [],
    split_labels: Optional[List[Text]] = None,
    split_rate: Optional[List[float]] = None,
    s3_link: Optional[str] = None,
) -> None:
    """Dataset Onboard Validation
    Args:
        input_schema (List[Union[Dict, MetaData]]): metadata of inputs
        output_schema (List[Union[Dict, MetaData]]): metadata of outputs
        content_path (Union[Union[Text, Path], List[Union[Text, Path]]]): path to files which contain the data content
        split_labels: (Optional[List[Text]]): The delimiters according which to split the dataset
        split_rate: (Optional[List[float]]): the rate of spliting the dataset
        s3_link (Optional[str]): s3 url to files or directories
    """

    input_dtype = input_schema[0].dtype if isinstance(input_schema[0], MetaData) else input_schema[0]["dtype"]
    if isinstance(input_dtype, DataType):
        input_dtype = input_dtype.value

    assert (
        FunctionInputOutput.get(function) is not None and input_dtype in FunctionInputOutput[function]["input"]
    ), f"Data Asset Onboarding Error: The input data type `{input_dtype}` is not compatible with the `{function}` function.\nThe expected input data type should be one of these data type: `{FunctionInputOutput[function]['input']}`."

    if len(output_schema) > 0:
        output_dtype = output_schema[0].dtype if isinstance(output_schema[0], MetaData) else output_schema[0]["dtype"]
        if isinstance(output_dtype, DataType):
            output_dtype = output_dtype.value

        assert (
            FunctionInputOutput.get(function) is not None and output_dtype in FunctionInputOutput[function]["output"]
        ), f"Data Asset Onboarding Error: The output data type `{output_dtype}` is not compatible with the `{function}` function.\nThe expected output data type should be one of these data type: `{FunctionInputOutput[function]['output']}`."

    assert (
        content_path is not None or s3_link is not None
    ), "Data Asset Onboarding Error: No path to content Data was provided. Please update `context_path` or `s3_link`."

    assert (split_labels is not None and split_rate is not None) or (
        split_labels is None and split_rate is None
    ), "Data Asset Onboarding Error: Make sure you set the split labels values as well as their rates."
