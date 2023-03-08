__author__="thiagocastroferreira"

import logging
import os
import pandas as pd

from aixtend.enums.file_type import FileType
from aixtend.enums.storage_type import StorageType
from aixtend.modules.file import File
from aixtend.modules.metadata import MetaData
from aixtend.utils.file_utils import download_data, upload_data_s3
from pathlib import Path
from typing import List, Text, Tuple

def process_text(content: str, storage_type: StorageType) -> Text:
    """Process text files

    Args:
        content (str): URL with text, local path with text or textual content
        storage_type (StorageType): type of storage: URL, local path or textual content

    Returns:
        Text: textual content
    """
    # if storage_type == StorageType.URL:
    #     tempfile = download_data(content)
    #     with open(tempfile) as f:
    #         text = f.read()
    #     os.remove(tempfile)
    if storage_type == StorageType.FILE:
        with open(content) as f:
            text = f.read()
    else:
        text = content
    return text


def run(metadata: MetaData, paths: List, folder: Path, batch_size:int = 1000) -> Tuple[List[File], int]:
    """Process a list of local textual files, compress and upload them to pre-signed URLs in S3

    Args:
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Path): local folder to save compressed files before upload them to s3.

    Returns:
        Tuple[List[File], int]: list of s3 links and data colum index
    """
    idx = 0
    data_column_idx = -1
    files, batch = [], []
    for path in paths:
        # TO DO: extract the split from file name
        try:
            dataframe = pd.read_csv(path)
        except:
            raise Exception(f"Data Asset Onboarding Error: Local file \"{path}\" not found.")

        # process texts and labels
        for (_, row) in dataframe.iterrows():
            try:
                text_path = row[metadata.name]
            except:
                raise Exception(f"Data Asset Onboarding Error: Column \"{metadata.name}\" not found in the local file {path}.")
            
            try:
                text = process_text(text_path, metadata.storage_type)
                batch.append(text)
            except:
                logging.warning(f"Data Asset Onboarding: The instance \"{row}\" of \"{metadata.name}\" could not be processed and will be skipped.")

            if ((idx + 1) % batch_size) == 0:
                batch_index = str(len(files) + 1).zfill(8)
                file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

                df = pd.DataFrame({metadata.name: batch})
                start, end = idx - len(batch) + 1, idx + 1
                df["@INDEX"] = range(start, end)
                df.to_csv(file_name, compression="gzip", index=False)
                s3_link = upload_data_s3(file_name, content_type="text/csv", content_encoding="gzip")
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                # get data column index
                data_column_idx = df.columns.to_list().index(metadata.name) + 1
                batch = []
            idx += 1

    if len(batch) > 0:
        batch_index = str(len(files) + 1).zfill(8)
        file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

        df = pd.DataFrame({metadata.name: batch})
        start, end = idx - len(batch) + 1, idx + 1
        df["@INDEX"] = range(start, end)
        df.to_csv(file_name, compression="gzip", index=False)
        s3_link = upload_data_s3(file_name, content_type="text/csv", content_encoding="gzip")
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        # get data column index
        data_column_idx = df.columns.to_list().index(metadata.name) + 1
        batch = []
    return files, data_column_idx