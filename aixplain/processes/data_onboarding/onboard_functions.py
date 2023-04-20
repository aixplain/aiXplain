__author__ = "aiXplain"

import aixplain.processes.data_onboarding.process_audio_files as process_audio_files
import aixplain.processes.data_onboarding.process_text_files as process_text_files
import aixplain.utils.config as config
import logging

from aixplain.enums.data_type import DataType
from aixplain.enums.file_type import FileType
from aixplain.modules.corpus import Corpus
from aixplain.modules.data import Data
from aixplain.modules.dataset import Dataset
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import _request_with_retry
from pathlib import Path
from typing import Any, Dict, List, Tuple, Text, Union
from urllib.parse import urljoin

FORBIDDEN_COLUMN_NAMES = ["@VOLUME", "@START_TIME", "@END_TIME", "@ORIGINAL", "@SOURCE", "@INDEX", "@SPLIT"]


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
    return paths


def process_data_files(
    data_asset_name: str, metadata: MetaData, paths: List, folder: Union[str, Path] = None
) -> Tuple[List[File], int, int, int]:
    """Process a list of local files, compress and upload them to pre-signed URLs in S3

    Args:
        data_asset_name (str): name of the data asset
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Union[str, Path], optional): local folder to save compressed files before upload them to s3. Defaults to data_asset_name.

    Returns:
        Tuple[List[File], int]: list of s3 links; data, start and end columns index
    """
    if folder is None:
        folder = Path(data_asset_name)
    elif isinstance(folder, str):
        folder = Path(folder)

    files = []
    data_column_idx, start_column_idx, end_column_idx = -1, -1, -1
    if metadata.dtype in [DataType.TEXT, DataType.LABEL]:
        files, data_column_idx = process_text_files.run(metadata=metadata, paths=paths, folder=folder)
    elif metadata.dtype in [DataType.AUDIO]:
        files, data_column_idx, start_column_idx, end_column_idx = process_audio_files.run(
            metadata=metadata, paths=paths, folder=folder
        )
    return files, data_column_idx, start_column_idx, end_column_idx


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
        "batches": [{"tempFilePath": str(file.path), "order": idx + 1} for idx, file in enumerate(data.files)],
        "tags": [],
        "metaData": {},
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


def build_payload_corpus(corpus: Corpus, ref_data: List[Text]) -> Dict:
    """Create corpus payload to call coreengine on the onboard process

    Args:
        corpus (Corpus): corpus object
        ref_data (List[Text]): list of referred data

    Returns:
        Dict: payload
    """
    payload = {
        "name": corpus.name,
        "description": corpus.description,
        "suggestedFunctions": [f.value for f in corpus.functions],
        "tags": corpus.tags,
        "pricing": {"type": "FREE", "cost": 0},
        "privacy": corpus.privacy.value,
        "license": {"typeId": corpus.license.value["id"]},
        "refData": ref_data,
        "data": [],
    }

    for data in corpus.data:
        data_json = build_payload_data(data)
        payload["data"].append(data_json)
    return payload


def build_payload_dataset(
    dataset: Dataset, input_ref_data: Dict[Text, Any], output_ref_data: Dict[Text, List[Any]], tags: List[Text]
) -> Dict:
    # compute ref data
    flat_input_ref_data = [item for sublist in list(input_ref_data.values()) for item in sublist]
    flat_output_ref_data = [item for sublist in list(output_ref_data.values()) for item in sublist]
    ref_data = flat_input_ref_data + flat_output_ref_data

    payload = {
        "name": dataset.name,
        "description": dataset.description,
        "function": dataset.function.value,
        "tags": dataset.tags,
        "privacy": dataset.privacy.value,
        "license": {"typeId": dataset.license.value["id"]},
        "refData": ref_data,
        "tags": tags,
        "data": [],
        "input": [],
        "metadata": [],
    }

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

    # compute output data
    output = {}
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

    assert len(payload["input"]) > 0, "Data Asset Onboarding Error: Please specify the input data of your dataset."
    assert len(payload["output"]) > 0, "Data Asset Onboarding Error: Please specify the output data of your dataset."
    return payload


def create_data_asset(payload: Dict, data_asset_type: Text = "corpus") -> Dict:
    team_key = config.TEAM_API_KEY
    headers = {"Authorization": "token " + team_key}

    url = urljoin(config.BACKEND_URL, f"sdk/inventory/{data_asset_type}/onboard")

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
