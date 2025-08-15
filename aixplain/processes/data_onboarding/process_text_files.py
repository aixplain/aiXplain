__author__ = "thiagocastroferreira"

import logging
import os
import pandas as pd
import validators

from aixplain.enums.file_type import FileType
from aixplain.enums.storage_type import StorageType
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import upload_data
from pathlib import Path
from tqdm import tqdm
from typing import List, Text, Tuple


def process_text(content: str, storage_type: StorageType) -> Text:
    """Process text content based on its storage type and location.

    This function handles different types of text content:
    - Local files: Reads the file content (with size validation)
    - URLs: Marks them for non-download if they're public links
    - Direct text: Uses the content as-is

    Args:
        content (str): The text content to process. Can be:
            - A path to a local file
            - A URL pointing to text content
            - The actual text content
        storage_type (StorageType): The type of storage for the content:
            - StorageType.FILE for local files
            - StorageType.TEXT for direct text content
            - Other storage types for different handling

    Returns:
        Text: The processed text content. URLs may be prefixed with
            "DONOTDOWNLOAD" if they should not be downloaded.

    Raises:
        AssertionError: If a local text file exceeds 25MB in size.
        IOError: If there are issues reading a local file.
    """
    if storage_type == StorageType.FILE:
        # Check the size of file and assert a limit of 25 MB
        assert (
            os.path.getsize(content) <= 25000000
        ), f'Data Asset Onboarding Error: Local text file "{content}" exceeds the size limit of 25 MB.'
        with open(content) as f:
            text = f.read()
    else:
        text = content

    # if the row is a textual URL (which should not be downloaded), tag it
    if storage_type in [StorageType.FILE, StorageType.TEXT] and (
        str(text).startswith("s3://")
        or str(text).startswith("http://")
        or str(text).startswith("https://")
        or validators.url(text)
    ):
        text = "DONOTDOWNLOAD" + str(text)
    return text


def run(metadata: MetaData, paths: List, folder: Path, batch_size: int = 1000) -> Tuple[List[File], int, int]:
    """Process text files in batches and upload them to S3 with index tracking.

    This function processes text files (either local or from URLs) in batches,
    creating compressed CSV index files that track the text content and their
    positions. The index files are then uploaded to S3.

    The process works as follows:
    1. For each input CSV file:
       - Read the specified column containing text content/paths
       - Process each text entry (read files, handle URLs)
       - Add processed text to the current batch
    2. After every batch_size entries:
       - Create a new index CSV with the processed texts
       - Add row indices for tracking
       - Compress and upload the index to S3
       - Start a new batch

    Args:
        metadata (MetaData): Metadata object containing information about the text data,
            including column names and storage type configuration.
        paths (List): List of paths to CSV files containing the text data or
            references to text content.
        folder (Path): Local folder path where the generated index files will be
            temporarily stored before upload.
        batch_size (int, optional): Number of text entries to process in each batch.
            Defaults to 1000.

    Returns:
        Tuple[List[File], int, int]: A tuple containing:
            - List[File]: List of File objects pointing to uploaded index files in S3
            - int: Index of the data column in the index CSV files
            - int: Total number of text entries processed

    Raises:
        Exception: If:
            - Input CSV files are not found
            - Required columns are missing in input files
            - Text processing fails (e.g., file size limit exceeded)
    """
    logging.debug(f'Data Asset Onboarding: Processing "{metadata.name}".')
    idx = 0
    data_column_idx = -1
    files, batch = [], []
    for i in tqdm(range(len(paths)), desc=f' Data "{metadata.name}" onboarding progress', position=1, leave=False):
        path = paths[i]
        try:
            dataframe = pd.read_csv(path)
        except Exception:
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

        # process texts and labels
        for j in tqdm(range(len(dataframe)), desc=" File onboarding progress", position=2, leave=False):
            row = dataframe.iloc[j]
            try:
                text_path = row[metadata.name]
            except Exception:
                message = f'Data Asset Onboarding Error: Column "{metadata.name}" not found in the local file {path}.'
                logging.exception(message)
                raise Exception(message)

            try:
                text = process_text(text_path, metadata.storage_type)
                batch.append(text)
            except Exception as e:
                logging.exception(e)
                raise Exception(e)

            idx += 1
            if ((idx) % batch_size) == 0:
                batch_index = str(len(files) + 1).zfill(8)
                file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

                df = pd.DataFrame({metadata.name: batch})
                start, end = idx - len(batch), idx
                df["@INDEX"] = range(start, end)
                df.to_csv(file_name, compression="gzip", index=False)
                s3_link = upload_data(file_name, content_type="text/csv", content_encoding="gzip", return_download_link=False)
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                # get data column index
                data_column_idx = df.columns.to_list().index(metadata.name)
                batch = []

    if len(batch) > 0:
        batch_index = str(len(files) + 1).zfill(8)
        file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

        df = pd.DataFrame({metadata.name: batch})
        start, end = idx - len(batch), idx
        df["@INDEX"] = range(start, end)
        df.to_csv(file_name, compression="gzip", index=False)
        s3_link = upload_data(file_name, content_type="text/csv", content_encoding="gzip", return_download_link=False)
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        # get data column index
        data_column_idx = df.columns.to_list().index(metadata.name)
        batch = []
    return files, data_column_idx, idx
