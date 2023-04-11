__author__ = "aiXplain"

import aixplain.processes.data_onboarding.process_audio_files as process_audio_files
import aixplain.processes.data_onboarding.process_text_files as process_text_files
import aixplain.utils.config as config
import logging

from aixplain.enums.data_type import DataType
from aixplain.enums.file_type import FileType
from aixplain.modules.corpus import Corpus
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import _request_with_retry
from pathlib import Path
from typing import Dict, List, Tuple, Text, Union
from urllib.parse import urljoin

FORBIDDEN_COLUMN_NAMES = ["@VOLUME", "@START_TIME", "@END_TIME", "@ORIGINAL", "@SOURCE", "@INDEX"]


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


def build_payload_corpus(corpus: Corpus, ref_data: List[Text]) -> Dict:
    """Create payload to call coreengine

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
        "refData": ref_data,
        "data": [],
    }

    for data in corpus.data:
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

        payload["data"].append(data_json)
    return payload


def create_corpus(payload: Dict) -> Dict:
    team_key = config.TEAM_API_KEY
    headers = {"Authorization": "token " + team_key}

    url = urljoin(config.BACKEND_URL, "sdk/inventory/corpus/onboard")

    r = _request_with_retry("post", url, headers=headers, json=payload)
    if 200 <= r.status_code < 300:
        response = r.json()

        corpus_id = response["id"]
        status = response["status"]
        # coreengine_payload = response["coreEnginePayload"]

        return {
            "success": True,
            "corpus_id": corpus_id,
            "status": status,
            # "coreengine_payload": coreengine_payload
        }
    else:
        try:
            response = r.json()
            msg = response["message"]
            error_msg = f"Data Asset Onboarding Error: {msg}"
        except Exception as e:
            error_msg = "Data Asset Onboarding Error: Failure on creating the corpus. Please contant the administrators."
        return {"success": False, "error": error_msg}
