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
from aixplain.utils.file_utils import _request_with_retry
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
    """Recursively access all local paths. Check if file extensions are supported.

    Args:
        input_paths (List[Union[str, Path]]): list of input pahts including folders and files

    Returns:
        List[Path]: list of local file paths
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
    """Process a list of local files, compress and upload them to pre-signed URLs in S3

    Args:
        data_asset_name (str): name of the data asset
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Union[str, Path], optional): local folder to save compressed files before upload them to s3. Defaults to data_asset_name.

    Returns:
        Tuple[List[File], int, int, int]: list of s3 links; data, start and end columns index; and number of rows
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
    if metadata.dtype in [DataType.AUDIO, DataType.IMAGE] or metadata.dsubtype == DataSubtype.INTERVAL:
        files, data_column_idx, start_column_idx, end_column_idx, nrows = process_media_files.run(
            metadata=metadata, paths=paths, folder=folder
        )
    elif metadata.dtype in [DataType.TEXT, DataType.LABEL]:
        files, data_column_idx, nrows = process_text_files.run(metadata=metadata, paths=paths, folder=folder)
    return files, data_column_idx, start_column_idx, end_column_idx, nrows


def build_payload_data(data: Data) -> Dict:
    """Create data payload to call coreengine on Corpus/Dataset onboard

    Args:
        data (Data): data object

    Returns:
        Dict: payload
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
    """Create corpus payload to call coreengine on the onboard process

    Args:
        corpus (Corpus): corpus object
        ref_data (List[Text]): list of referred data
        error_handler (ErrorHandler): how to handle failed rows

    Returns:
        Dict: payload
    """
    payload = {
        "name": corpus.name,
        "description": corpus.description,
        "suggestedFunctions": [f.value for f in corpus.functions],
        "onboardingErrorsPolicy": error_handler.value,
        "tags": corpus.tags,
        "pricing": {"type": "FREE", "cost": 0},
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
    """Generate onboard payload to coreengine

    Args:
        dataset (Dataset): dataset to be onboard
        input_ref_data (Dict[Text, Any]): reference to existent input data
        output_ref_data (Dict[Text, List[Any]]): reference to existent output data
        hypotheses_ref_data (Dict[Text, Any]): reference to existent hypotheses to the target data
        meta_ref_data (Dict[Text, Any]): reference to existent metadata
        tags (List[Text]): description tags
        error_handler (ErrorHandler): how to handle failed rows

    Returns:
        Dict: onboard payload
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
        "tags": dataset.tags,
        "privacy": dataset.privacy.value,
        "license": {"typeId": dataset.license.value},
        "refData": ref_data,
        "tags": tags,
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


def create_data_asset(payload: Dict, data_asset_type: Text = "corpus") -> Dict:
    """Service to call onboard process in coreengine

    Args:
        payload (Dict): onboard payload
        data_asset_type (Text, optional): corpus or dataset. Defaults to "corpus".

    Returns:
        Dict: onboard status
    """
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
        except Exception as e:
            error_msg = (
                f"Data Asset Onboarding Error: Failure on creating the {data_asset_type}. Please contant the administrators."
            )
        return {"success": False, "error": error_msg}


def is_data(data_id: Text) -> bool:
    """Check whether reference data exists

    Args:
        data_id (Text): ID of the data

    Returns:
        bool: True if it exists, False otherwise
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
    except:
        return False


def split_data(paths: List, split_rate: List[float], split_labels: List[Text]) -> MetaData:
    """Split the data according to some split labels and rate

    Args:
        paths (List): path to data files
        split_rate (List[Text]): split rate
        split_labels (List[Text]): split labels

    Returns:
        MetaData: metadata of the new split
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
        except Exception as e:
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

    if column_name is None:
        message = f"Data Asset Onboarding Error: All split names are used."
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
