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
from typing import Dict, List, Union


def get_paths(input_paths: List[Union[str, Path]]):
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
                    logging.warning(f"Onboarding: File Extension not Supported ({str(path)})")
        else:
            extension = FileType(path.suffix)
            if extension == FileType.CSV:
                paths.append(path)
            else:
                logging.warning(f"Onboarding: File Extension not Supported ({str(path)})")
    return paths


def upload_data_s3(file_name: Union[str, Path], content_type: str = "text/csv", content_encoding: str = None):
    try:
        # Get pre-signed URL
        team_key = config.TEAM_API_KEY
        url = config.TEMPFILE_UPLOAD_URL

        headers = {"Authorization": "token " + team_key}

        payload = {"contentType": content_type, "originalName": file_name}
        r = _request_with_retry("post", url, headers=headers, data=payload)
        response = r.json()

        path = response["key"]
        # Upload data
        presigned_url = response["uploadUrl"]
        headers = {"Content-Type": content_type}
        if content_encoding is None:
            headers["Content-Encoding"] = content_encoding
        payload = open(file_name, "rb").read()
        r = _request_with_retry("put", presigned_url, headers=headers, data=payload)

        if r.status_code != 200:
            raise Exception("Onboarding Error: Failure on Uploading to S3.")
        bucket_name = re.findall(r"https://(.*?).s3.amazonaws.com", presigned_url)[0]
        s3_link = f"s3://{bucket_name}/{path}"
        return s3_link
    except:
        raise Exception("Onboarding Error: Failure on Uploading to S3.")


def process_text(content: str, storage_type: StorageType):
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


def process_data_files(data_asset_name: str, metadata: MetaData, paths: List, folder: Union[str, Path] = None):
    if folder is None:
        folder = data_asset_name

    files, batch = [], []
    for path in paths:
        # TO DO: extract the split from file name
        content = pd.read_csv(path)[metadata.name]
        ndigits, nbdigits = max([4, len(str(len(content)))]), 4

        # process texts and labels
        if metadata.dtype in [DataType.TEXT, DataType.LABEL]:
            ncharacters = 0
            for idx, row in enumerate(content):
                text = process_text(row, metadata.storage_type)
                ncharacters += len(text)
                batch.append(text)

                if (ncharacters % 1000000) == 0:
                    index = str(idx + 1).zfill(ndigits)
                    batch_index = str(len(files) + 1).zfill(nbdigits)
                    file_name = f"{folder}/{metadata.name}-{batch_index}-{index}.csv.gz"

                    df = pd.DataFrame({metadata.name: batch})
                    start, end = idx - len(batch) + 1, idx + 1
                    df["index"] = range(start, end)
                    df.to_csv(file_name, compression="gzip", index=False)
                    s3_link = upload_data_s3(file_name, content_type="text/csv", content_encoding="gzip")
                    files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                    batch = []

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


def create_payload_corpus(corpus: Corpus):
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
