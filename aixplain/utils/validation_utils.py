from pathlib import Path
from typing import Optional, Text, Union, Dict, List, Any
from enum import Enum

from aixplain.modules.metadata import MetaData
from aixplain.enums.function import FunctionInputOutput, Function
from aixplain.enums.data_type import DataType
from aixplain.enums import DataSubtype


def _is_split(dsubtype: Union[Text, DataSubtype]) -> bool:
    """Check if a data subtype represents a split.

    Args:
        dsubtype (Union[Text, DataSubtype]): The data subtype to check. Can be
            either a string or a DataSubtype enum value.

    Returns:
        bool: True if the subtype represents a split, False otherwise.

    Note:
        The comparison is case-insensitive.
    """
    return str(dsubtype).lower() == "split"


def dataset_onboarding_validation(
    input_schema: List[Union[Dict, MetaData]],
    output_schema: List[Union[Dict, MetaData]],
    function: Function,
    input_ref_data: Dict[Text, Any] = {},
    metadata_schema: List[Union[Dict, MetaData]] = [],
    content_path: Union[Union[Text, Path], List[Union[Text, Path]]] = [],
    split_labels: Optional[List[Text]] = None,
    split_rate: Optional[List[float]] = None,
    s3_link: Optional[str] = None,
) -> None:
    """Validate dataset parameters before onboarding.

    This function performs comprehensive validation of dataset parameters to ensure
    they meet the requirements for onboarding. It checks:
    - Input/output data type compatibility with the specified function
    - Presence of required input data
    - Validity of dataset splitting configuration
    - Presence of content data source

    Args:
        input_schema (List[Union[Dict, MetaData]]): Metadata describing the input
            data structure and types.
        output_schema (List[Union[Dict, MetaData]]): Metadata describing the output
            data structure and types.
        function (Function): The function type that this dataset is designed for
            (e.g., translation, transcription).
        input_ref_data (Dict[Text, Any], optional): References to existing input
            data in the platform. Defaults to {}.
        metadata_schema (List[Union[Dict, MetaData]], optional): Additional metadata
            describing the dataset. Defaults to [].
        content_path (Union[Union[Text, Path], List[Union[Text, Path]]], optional):
            Path(s) to local files containing the data. Defaults to [].
        split_labels (Optional[List[Text]], optional): Labels for dataset splits
            (e.g., ["train", "test"]). Must be provided with split_rate.
            Defaults to None.
        split_rate (Optional[List[float]], optional): Proportions for dataset splits
            (e.g., [0.8, 0.2]). Must sum to 1.0 and match split_labels length.
            Defaults to None.
        s3_link (Optional[str], optional): S3 URL to data files or directories.
            Alternative to content_path. Defaults to None.

    Raises:
        AssertionError: If any validation fails:
            - No input data specified
            - Incompatible input/output types for function
            - Invalid split configuration
            - No content source provided
            - Multiple split metadata entries
            - Invalid split metadata type
            - Mismatched split labels and rates

    Note:
        Either content_path or s3_link must be provided. If using splits,
        both split_labels and split_rate must be provided.
    """

    metadata_spliting_schema = list(filter(lambda md: str(md.dsubtype) == "split", metadata_schema))

    # validate the input and the output of the dataset
    assert (
        len(input_schema) > 0 or len(input_ref_data) > 0
    ), "Data Asset Onboarding Error: You must specify an input data to onboard a dataset."

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

    # validate the splitting
    assert (
        len(metadata_spliting_schema) < 2
    ), f"Data Asset Onboarding Error: Only 0 or 1 metadata of the split subtype can be added to the `metadata_schema`."
    assert all(
        str(mds.dtype) == "label" for mds in metadata_spliting_schema
    ), f"Data Asset Onboarding Error: The `dtype` must be `label` for any splitting subtype."

    assert (
        content_path is not None or s3_link is not None
    ), "Data Asset Onboarding Error: No path to content Data was provided. Please update `context_path` or `s3_link`."
    assert (split_labels is not None and split_rate is not None) or (
        split_labels is None and split_rate is None
    ), "Data Asset Onboarding Error: Make sure you set the split labels values as well as their rates."
