__author__ = "aiXplain"

import aixtend.processes.process_audio_files as process_audio_files
import aixtend.processes.process_text_files as process_text_files
import logging

from aixtend.enums.data_type import DataType
from aixtend.enums.file_type import FileType
from aixtend.modules.corpus import Corpus
from aixtend.modules.file import File
from aixtend.modules.metadata import MetaData
from pathlib import Path
from typing import Dict, List, Union

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


def process_data_files(data_asset_name: str, metadata: MetaData, paths: List, folder: Union[str, Path] = None) -> List[File]:
    """Process a list of local files, compress and upload them to pre-signed URLs in S3

    Args:
        data_asset_name (str): name of the data asset
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Union[str, Path], optional): local folder to save compressed files before upload them to s3. Defaults to data_asset_name.

    Returns:
        List[File]: list of s3 links
    """
    if folder is None:
        folder = Path(data_asset_name)
    elif isinstance(folder, str):
        folder = Path(folder)

    files = []
    if metadata.dtype in [DataType.TEXT, DataType.LABEL]:
        files = process_text_files.run(metadata=metadata, paths=paths, folder=folder)
    elif metadata.dtype in [DataType.AUDIO]:
        files = process_audio_files.run(metadata=metadata, paths=paths, folder=folder)
    return files


def create_payload_corpus(corpus: Corpus) -> Dict:
    """Create payload to call coreengine

    Args:
        corpus (Corpus): corpus object

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

        if "language" in data.kwargs:
            data_json["metadata"]["language"] = data.kwargs["language"]
        payload["data"].append(data_json)
    return payload
