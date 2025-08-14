__author__ = "aiXplain"

import aixplain.processes.data_onboarding.process_media_files as process_media_files
import aixplain.processes.data_onboarding.process_text_files as process_text_files
import aixplain.utils.config as config
import logging
import os
import pandas as pd
import random

from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.error_handler import ErrorHandler
from aixplain.enums.file_type import FileType
from aixplain.enums.storage_type import StorageType
from aixplain.modules.corpus import Corpus
from aixplain.modules.data import Data
from aixplain.modules.dataset import Dataset
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.request_utils import _request_with_retry
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Text, Union
from urllib.parse import urljoin

FORBIDDEN_COLUMN_NAMES = [
    "@VOLUME",
    "@START_TIME",
    "@END_TIME",
    "@START",
    "@END",
    "@ORIGINAL",
    "@SOURCE",
    "@INDEX",
    "@SPLIT",
    "@STATUS",
]


def get_paths(input_paths: List[Union[str, Path]]) -> List[Path]:
    """Recursively collect all supported local file paths from the given input paths.

    This function traverses through the provided paths, which can be files or directories,
    and collects paths to all supported files (currently only CSV files). It also performs
    size validation to ensure files don't exceed 1GB.

    Args:
        input_paths (List[Union[str, Path]]): List of input paths. Can include both
            individual file paths and directory paths.

    Returns:
        List[Path]: List of validated local file paths that are supported.

    Raises:
        AssertionError: If any CSV file exceeds 1GB in size.
        Warning: If a file has an unsupported extension.
    """
    paths = []
    for path in input_paths:
        if isinstance(path, str):
            path = Path(path)

        if path.is_dir():
            for subpath in path.iterdir():
                extension = subpath.suffix
                if extension == FileType.CSV:
                    paths.append(subpath)
                else:
                    logging.warning(f"Data Asset Onboarding: File Extension not Supported ({str(path)})")
        else:
            extension = FileType(path.suffix)
            if extension == FileType.CSV:
                paths.append(path)
            else:
                logging.warning(f"Data Asset Onboarding: File Extension not Supported ({str(path)})")

    # check CSV sizes
    for path in paths:
        assert os.path.getsize(path) <= 1e9, f'Data Asset Onboarding Error: CSV file "{path}" exceeds the size limit of 1 GB.'
    return paths


def process_data_files(
    data_asset_name: str, metadata: MetaData, paths: List, folder: Optional[Union[str, Path]] = None
) -> Tuple[List[File], int, int, int, int]:
    """Process data files based on their type and prepare them for upload to S3.

    This function handles different types of data files (audio, image, text, etc.)
    by delegating to appropriate processing modules. It compresses the files if needed
    and prepares them for upload to S3.

    Args:
        data_asset_name (str): Name of the data asset being processed.
        metadata (MetaData): Metadata object containing type and subtype information
            for the data being processed.
        paths (List): List of paths to local files that need processing.
        folder (Optional[Union[str, Path]], optional): Local folder to save processed
            files before uploading to S3. If None, uses data_asset_name. Defaults to None.

    Returns:
        Tuple[List[File], int, int, int, int]: A tuple containing:
            - List[File]: List of processed file objects ready for S3 upload
            - int: Index of the data column
            - int: Index of the start column (for intervals)
            - int: Index of the end column (for intervals)
            - int: Total number of rows processed
    """
    if folder is None:
        folder = Path(data_asset_name)
    elif isinstance(folder, str):
        folder = Path(folder)

    files = []
    data_column_idx, start_column_idx, end_column_idx, nrows, = (
        -1,
        -1,
        -1,
        0,
    )
    if metadata.dtype in [DataType.AUDIO, DataType.IMAGE, DataType.LABEL] or metadata.dsubtype == DataSubtype.INTERVAL:
        files, data_column_idx, start_column_idx, end_column_idx, nrows = process_media_files.run(
            metadata=metadata, paths=paths, folder=folder
        )
    elif metadata.dtype in [DataType.TEXT]:
        files, data_column_idx, nrows = process_text_files.run(metadata=metadata, paths=paths, folder=folder)
    return files, data_column_idx, start_column_idx, end_column_idx, nrows


def build_payload_data(data: Data) -> Dict:
    """Build a payload dictionary for data onboarding to the core engine.

    This function creates a standardized payload structure for onboarding data
    to the core engine. It includes data properties, file information, and metadata
    such as languages and column mappings.

    Args:
        data (Data): Data object containing information about the data to be onboarded,
            including name, type, files, and language information.

    Returns:
        Dict: A dictionary containing the formatted payload with the following key fields:
            - name: Name of the data
            - dataColumn: Column identifier for the data
            - dataType: Type of the data
            - dataSubtype: Subtype of the data
            - batches: List of file information with paths and order
            - tags: List of descriptive tags
            - metaData: Additional metadata including languages
            Additional fields may be added for interval data (start/end columns).
    """
    data_json = {
        "name": data.name,
        "dataColumn": data.data_column,
        "dataType": data.dtype.value,
        "dataSubtype": data.dsubtype.value,
        "batches": [{"tempFilePath": str(file.path), "order": idx + 1} for idx, file in enumerate(data.files)],
        "tags": [],
        "metaData": {"languages": []},
    }

    if len(data.languages) > 0:
        data_json["metaData"]["languages"] = [lng.value for lng in data.languages]

    if data.start_column is not None and data.start_column > -1 and data.end_column is not None and data.end_column > -1:
        if data.dtype == DataType.AUDIO:
            data_json["startTimeColumn"] = data.start_column
            data_json["endTimeColumn"] = data.end_column
        else:
            data_json["startColumn"] = data.start_column
            data_json["endColumn"] = data.end_column
    return data_json


def build_payload_corpus(corpus: Corpus, ref_data: List[Text], error_handler: ErrorHandler) -> Dict:
    """Build a payload dictionary for corpus onboarding to the core engine.

    This function creates a standardized payload structure for onboarding a corpus,
    including all its associated data, metadata, and configuration settings.

    Args:
        corpus (Corpus): Corpus object containing the data collection to be onboarded,
            including name, description, functions, and associated data.
        ref_data (List[Text]): List of referenced data IDs that this corpus depends on
            or is related to.
        error_handler (ErrorHandler): Configuration for how to handle rows that fail
            during the onboarding process.

    Returns:
        Dict: A dictionary containing the formatted payload with the following key fields:
            - name: Name of the corpus
            - description: Description of the corpus
            - suggestedFunctions: List of suggested AI functions
            - onboardingErrorsPolicy: Error handling policy
            - tags: List of descriptive tags
            - pricing: Pricing configuration
            - privacy: Privacy settings
            - license: License information
            - refData: Referenced data IDs
            - data: List of data payloads for each data component
    """
    payload = {
        "name": corpus.name,
        "description": corpus.description,
        "suggestedFunctions": [f.value for f in corpus.functions],
        "onboardingErrorsPolicy": error_handler.value,
        "tags": corpus.tags,
        "pricing": {"usage": ["benchmark", "finetune"], "type": "free", "cost": 0},
        "privacy": corpus.privacy.value,
        "license": {"typeId": corpus.license.value},
        "refData": ref_data,
        "data": [],
    }

    for data in corpus.data:
        data_json = build_payload_data(data)
        payload["data"].append(data_json)
    return payload


def build_payload_dataset(
    dataset: Dataset,
    input_ref_data: Dict[Text, Any],
    output_ref_data: Dict[Text, List[Any]],
    hypotheses_ref_data: Dict[Text, Any],
    meta_ref_data: Dict[Text, Any],
    tags: List[Text],
    error_handler: ErrorHandler,
) -> Dict:
    """Build a payload dictionary for dataset onboarding to the core engine.

    This function creates a comprehensive payload structure for onboarding a dataset,
    including all its components: input data, output data, hypotheses, and metadata.
    It handles both new data and references to existing data.

    Args:
        dataset (Dataset): Dataset object to be onboarded, containing all the data
            components and configuration.
        input_ref_data (Dict[Text, Any]): Dictionary mapping input names to existing
            data IDs in the system.
        output_ref_data (Dict[Text, List[Any]]): Dictionary mapping output names to
            lists of existing data IDs for multi-reference outputs.
        hypotheses_ref_data (Dict[Text, Any]): Dictionary mapping hypothesis names to
            existing data IDs for model outputs or predictions.
        meta_ref_data (Dict[Text, Any]): Dictionary mapping metadata names to existing
            metadata IDs in the system.
        tags (List[Text]): List of descriptive tags for the dataset.
        error_handler (ErrorHandler): Configuration for how to handle rows that fail
            during the onboarding process.

    Returns:
        Dict: A dictionary containing the formatted payload with the following sections:
            - Basic information (name, description, function, etc.)
            - Configuration (error handling, privacy, license)
            - Input data section with both new and referenced inputs
            - Output data section with both new and referenced outputs
            - Hypotheses section with both new and referenced hypotheses
            - Metadata section with both new and referenced metadata
    """
    # compute ref data
    flat_input_ref_data = list(input_ref_data.values())
    flat_output_ref_data = [item for sublist in list(output_ref_data.values()) for item in sublist]
    flat_meta_ref_data = list(meta_ref_data.values())
    flat_hypotheses_ref_data = list(hypotheses_ref_data.values())
    ref_data = flat_input_ref_data + flat_output_ref_data + flat_meta_ref_data + flat_hypotheses_ref_data

    payload = {
        "name": dataset.name,
        "description": dataset.description,
        "function": dataset.function.value,
        "onboardingErrorsPolicy": error_handler.value,
        "tags": dataset.tags or tags,
        "privacy": dataset.privacy.value,
        "license": {"typeId": dataset.license.value},
        "refData": ref_data,
        "data": [],
        "input": [],
        "hypotheses": [],
        "metadata": [],
    }

    # INPUT DATA
    # compute ref input data
    index = 1
    for data_name in dataset.source_data:
        data = dataset.source_data[data_name]
        data_json = build_payload_data(data)
        data_json["tempId"] = data.id
        payload["data"].append(data_json)
        payload["input"].append({"index": index, "name": data.name, "dataId": data.id})
        index += 1

    # process input ref data
    for data_name in input_ref_data:
        payload["input"].append({"index": index, "name": data_name, "dataId": input_ref_data[data_name]})
        index += 1

    # HYPOTHESES
    index = 1
    for data_name in dataset.hypotheses:
        data = dataset.hypotheses[data_name]
        data_json = build_payload_data(data)
        data_json["tempId"] = data.id
        payload["data"].append(data_json)
        payload["hypotheses"].append({"index": index, "name": data.name, "dataId": data.id})
        index += 1

    # process hypotheses ref data
    for data_name in hypotheses_ref_data:
        payload["hypotheses"].append({"index": index, "name": data_name, "dataId": hypotheses_ref_data[data_name]})
        index += 1

    # METADATA
    index = 1
    for data_name in dataset.metadata:
        data = dataset.metadata[data_name]
        data_json = build_payload_data(data)
        data_json["tempId"] = data.id
        payload["data"].append(data_json)
        payload["metadata"].append({"index": index, "name": data.name, "dataId": data.id})
        index += 1

    # process meta ref data
    for data_name in meta_ref_data:
        payload["metadata"].append({"index": index, "name": data_name, "dataId": meta_ref_data[data_name]})
        index += 1

    # OUTPUT DATA
    # compute output data
    output = {}
    index = 1
    for output_name in dataset.target_data:
        output_data = {"index": index, "name": output_name, "dataIds": []}
        for data in dataset.target_data[output_name]:
            data_json = build_payload_data(data)
            data_json["tempId"] = data.id
            payload["data"].append(data_json)
            output_data["dataIds"].append(data.id)
        output[output_name] = output_data
        index += 1

    # process output ref data
    for output_name in output_ref_data:
        if output_name in output:
            output[output_name]["dataIds"] += output_ref_data[output_name]
        else:
            output_data = {"index": index, "name": output_name, "dataIds": []}
            for data_id in output_ref_data[output_name]:
                output_data["dataIds"].append(data_id)
            index += 1
            output[output_name] = output_data
    payload["output"] = list(output.values())
    return payload


def create_data_asset(payload: Dict, data_asset_type: Text = "corpus", api_key: Optional[Text] = None) -> Dict:
    """Create a new data asset (corpus or dataset) in the core engine.

    This function sends the onboarding request to the core engine and handles the response.
    It supports both corpus and dataset creation with proper authentication.

    Args:
        payload (Dict): The complete payload for the data asset, containing all necessary
            information for onboarding (structure depends on data_asset_type).
        data_asset_type (Text, optional): Type of data asset to create. Must be either
            "corpus" or "dataset". Defaults to "corpus".
        api_key (Optional[Text], optional): Team API key for authentication. If None,
            uses the default key from config. Defaults to None.

    Returns:
        Dict: A dictionary containing the onboarding status with the following fields:
            - success (bool): Whether the operation was successful
            - asset_id (str): ID of the created asset (if successful)
            - status (str): Current status of the asset (if successful)
            - error (str): Error message (if not successful)

    Note:
        The function handles both successful and failed responses, providing appropriate
        error messages in case of failure.
    """
    if api_key is not None:
        team_key = api_key
    else:
        team_key = config.TEAM_API_KEY
    headers = {"Authorization": "token " + team_key}

    url = urljoin(config.BACKEND_URL, f"sdk/{data_asset_type}/onboard")

    r = _request_with_retry("post", url, headers=headers, json=payload)
    if 200 <= r.status_code < 300:
        response = r.json()

        asset_id = response["id"]
        status = response["status"]

        return {
            "success": True,
            "asset_id": asset_id,
            "status": status,
            # "coreengine_payload": coreengine_payload
        }
    else:
        try:
            response = r.json()
            msg = response["message"]
            error_msg = f"Data Asset Onboarding Error: {msg}"
        except Exception:
            error_msg = (
                f"Data Asset Onboarding Error: Failure on creating the {data_asset_type}. Please contact the administrators."
            )
        return {"success": False, "error": error_msg}


def is_data(data_id: Text) -> bool:
    """Check if a data object exists in the system by its ID.

    This function makes an API call to verify the existence of a data object
    in the system. It's typically used to validate references before creating
    new assets that depend on existing data.

    Args:
        data_id (Text): The ID of the data object to check.

    Returns:
        bool: True if the data exists and is accessible, False otherwise.
            Returns False in case of API errors or if the data is not found.

    Note:
        The function handles API errors gracefully, returning False instead
        of raising exceptions.
    """
    try:
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL
        url = urljoin(backend_url, f"sdk/data/{data_id}/overview")
        headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()

        if "id" in resp:
            return True
        return False
    except Exception:
        return False


def split_data(paths: List, split_rate: List[float], split_labels: List[Text]) -> MetaData:
    """Split data files into partitions based on specified rates and labels.

    This function adds a new column to CSV files to indicate the split assignment
    for each row. It randomly assigns rows to splits based on the provided rates.
    The function tries to find an unused column name for the split information.

    Args:
        paths (List): List of paths to CSV files that need to be split.
        split_rate (List[float]): List of proportions for each split. Should sum to 1.0.
            For example, [0.8, 0.1, 0.1] for train/dev/test split.
        split_labels (List[Text]): List of labels corresponding to each split rate.
            For example, ["train", "dev", "test"].

    Returns:
        MetaData: A metadata object for the new split column with:
            - name: The generated column name for the split
            - dtype: Set to DataType.LABEL
            - dsubtype: Set to DataSubtype.SPLIT
            - storage_type: Set to StorageType.TEXT

    Raises:
        Exception: If no available column name is found or if file operations fail.

    Note:
        The function modifies the input CSV files in place, adding the new split column.
    """
    # get column name
    column_name = None
    for path in paths:
        try:
            dataframe = pd.read_csv(path)
            for candidate_name in ["split", "SPLIT", "_split", "_split_", "split_"]:
                if candidate_name not in dataframe.columns:
                    column_name = candidate_name
                    break

            if column_name is not None:
                break
        except Exception:
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

    if column_name is None:
        message = "Data Asset Onboarding Error: All split names are used."
        raise Exception(message)

    for path in paths:
        dataframe = pd.read_csv(path)
        dataframe[column_name] = [slabel for (slabel, srate) in zip(split_labels, split_rate) if srate == max(split_rate)][0]

        size = len(dataframe)
        start = 0
        indexes = list(range(size))
        random.shuffle(indexes)
        for (slabel, srate) in zip(split_labels, split_rate):
            split_size = int(srate * size)

            split_indexes = indexes[start : start + split_size]
            dataframe.loc[split_indexes, column_name] = slabel
            start = start + split_size
        dataframe.to_csv(path, index=False)

    return MetaData(name=column_name, dtype=DataType.LABEL, dsubtype=DataSubtype.SPLIT, storage_type=StorageType.TEXT)
