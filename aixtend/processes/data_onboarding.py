__author__ = "aiXplain"

import logging
import os
import pandas as pd
import re

import aixtend.utils.config as config
from aixtend.utils.file_utils import _request_with_retry
from aixtend.modules.corpus import Corpus
from aixtend.modules.file import File
from aixtend.modules.metadata import MetaData
from aixtend.enums.data_type import DataType
from aixtend.enums.file_type import FileType
from aixtend.enums.storage_type import StorageType
from aixtend.utils.file_utils import download_data
from pathlib import Path
from typing import Dict, List, Union, Text


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


def upload_data_s3(file_name: Union[str, Path], content_type: str = "text/csv", content_encoding: str = None):
    """Upload files to S3 with pre-signed URLs

    Args:
        file_name (Union[str, Path]): local path of file to be uploaded
        content_type (str, optional): Type of content. Defaults to "text/csv".
        content_encoding (str, optional): Content encoding. Defaults to None.

    Returns:
        URL: s3 path
    """
    try:
        # Get pre-signed URL
        team_key = config.TEAM_API_KEY
        url = config.TEMPFILE_UPLOAD_URL

        headers = {"Authorization": "token " + team_key}

        payload = {"contentType": content_type, "originalName": file_name}
        r = _request_with_retry("post", url, headers=headers, data=payload)
        response = r.json()
        print(response)
        path = response["key"]
        # Upload data
        presigned_url = response["uploadUrl"]
        headers = {"Content-Type": content_type}
        if content_encoding is None:
            headers["Content-Encoding"] = content_encoding
        payload = open(file_name, "rb").read()
        r = _request_with_retry("put", presigned_url, headers=headers, data=payload)

        if r.status_code != 200:
            raise Exception("Data Asset Onboarding Error: Failure on Uploading to S3.")
        bucket_name = re.findall(r"https://(.*?).s3.amazonaws.com", presigned_url)[0]
        s3_link = f"s3://{bucket_name}/{path}"
        return s3_link
    except:
        raise Exception("Data Asset Onboarding Error: Failure on Uploading to S3.")


def process_text(content: str, storage_type: StorageType) -> Text:
    """Process text files

    Args:
        content (str): URL with text, local path with text or textual content
        storage_type (StorageType): type of storage: URL, local path or textual content

    Returns:
        Text: textual content
    """
    if storage_type == StorageType.URL:
        tempfile = download_data(content)
        with open(tempfile) as f:
            text = f.read()
        os.remove(tempfile)
    elif storage_type == StorageType.FILE:
        with open(content) as f:
            text = f.read()
    else:
        text = content
    return text


def process_data_files(data_asset_name: str, metadata: MetaData, paths: List, folder: Union[str, Path] = None) -> List[Union[str, Path]]:
    """Process a list of local files, compress and upload them to pre-signed URLs in S3

    Args:
        data_asset_name (str): name of the data asset
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Union[str, Path], optional): local folder to save compressed files before upload them to s3. Defaults to data_asset_name.

    Returns:
        List[Union[str, Path]]: list of s3 links
    """
    if folder is None:
        folder = data_asset_name

    files, batch = [], []
    for path in paths:
        # TO DO: extract the split from file name
        try:
            content = pd.read_csv(path)[metadata.name]
        except:
            raise Exception(f"Data Asset Onboarding Error: Column {metadata.name} not found in the local file {path}.")
        ndigits, nbdigits = max([4, len(str(len(content)))]), 4

        # process texts and labels
        if metadata.dtype in [DataType.TEXT, DataType.LABEL]:
            ncharacters = 0
            for idx, row in enumerate(content):
                try:
                    text = process_text(row, metadata.storage_type)
                    ncharacters += len(text)
                    batch.append(text)
                except:
                    logging.warning(f"Data Asset Onboarding: The instance {row} of {metadata.name} could not be processed and will be skipped.")

                if ncharacters >= 1000000:
                    index = str(idx + 1).zfill(ndigits)
                    batch_index = str(len(files) + 1).zfill(nbdigits)
                    file_name = f"{folder}/{metadata.name}-{batch_index}-{index}.csv.gz"

                    df = pd.DataFrame({metadata.name: batch})
                    start, end = idx - len(batch) + 1, idx + 1
                    df["index"] = range(start, end)
                    df.to_csv(file_name, compression="gzip", index=False)
                    s3_link = upload_data_s3(file_name, content_type="text/csv", content_encoding="gzip")
                    files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                    batch, ncharacters = [], 0

            if len(batch) > 0:
                index = str(idx + 1).zfill(ndigits - len(str(idx + 1)))
                batch_index = str(len(files)).zfill(nbdigits - len(str(len(files))))
                file_name = f"{folder}/{metadata.name}-{batch_index}-{index}.csv.gz"

                df = pd.DataFrame({metadata.name: batch})
                start, end = idx - len(batch) + 1, idx + 1
                df["index"] = range(start, end)
                df.to_csv(file_name, compression="gzip", index=False)
                s3_link = upload_data_s3(file_name, content_type="text/csv", content_encoding="gzip")
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                batch = []
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
            "dataColumn": 1,
            "dataType": data.dtype.value,
            "batches": [{"tempFilePath": str(file.path), "order": idx + 1} for idx, file in enumerate(data.files)],
            "tags": [],
            "metaData": {},
        }

        if "language" in data.kwargs:
            data_json["metadata"]["language"] = data.kwargs["language"]
        payload["data"].append(data_json)
    return payload
