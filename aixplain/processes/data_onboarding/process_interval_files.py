__author__ = "thiagocastroferreira"

import json
import logging
import os
import pandas as pd
import tarfile

from aixplain.enums.data_type import DataType
from aixplain.enums.file_type import FileType
from aixplain.enums.storage_type import StorageType
from aixplain.modules.content_interval import (
    ContentInterval,
    AudioContentInterval,
    ImageContentInterval,
    TextContentInterval,
    VideoContentInterval,
)
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import upload_data
from pathlib import Path
from tqdm import tqdm
from typing import Any, Dict, List, Text, Tuple


def compress_folder(folder_path: str):
    with tarfile.open(folder_path + ".tgz", "w:gz") as tar:
        for name in os.listdir(folder_path):
            tar.add(os.path.join(folder_path, name))
    return folder_path + ".tgz"


def process_interval(interval: Any, storage_type: StorageType, interval_folder: Text) -> List[Dict]:
    """Process text files

    Args:
        intervals (Any): content intervals to process the content
        storage_type (StorageType): type of storage: URL, local path or textual content

    Returns:
        List[Dict]: content interval
    """
    if storage_type == StorageType.FILE:
        # Check the size of file and assert a limit of 50 MB
        assert (
            os.path.getsize(interval.content) <= 25000000
        ), f'Data Asset Onboarding Error: Local text file "{interval}" exceeds the size limit of 25 MB.'
        fname = os.path.basename(interval)
        new_path = os.path.join(audio_folder, fname)
        if os.path.exists(new_path) is False:
            shutil.copy2(audio_path, new_path)
    return [interval.__dict__ for interval in intervals]


def validate_format(index: int, interval: Dict, metadata: MetaData) -> ContentInterval:
    """Validate the interval format

    Args:
        index (int): row index
        interval (Dict): interval to be validated
        metadata (MetaData): metadata

    Returns:
        ContentInterval: _description_
    """
    if metadata.dtype == DataType.AUDIO_INTERVAL:
        try:
            if isinstance(interval, list):
                interval = [AudioContentInterval(**interval_) for interval_ in interval]
            else:
                interval = [AudioContentInterval(**interval)]
        except Exception as e:
            message = f'Data Asset Onboarding Error: Audio Interval in row {index} of Column "{metadata.name}" is not following the format. Check the "AudioContentInterval" class for the correct format.'
            logging.exception(message)
            raise Exception(message)
    elif metadata.dtype == DataType.IMAGE_INTERVAL:
        try:
            if isinstance(interval, list):
                interval = [ImageContentInterval(**interval_) for interval_ in interval]
            else:
                interval = [ImageContentInterval(**interval)]
        except Exception as e:
            message = f'Data Asset Onboarding Error: Image Interval in row {index} of Column "{metadata.name}" is not following the format. Check the "ImageContentInterval" class for the correct format.'
            logging.exception(message)
            raise Exception(message)
    elif metadata.dtype == DataType.TEXT_INTERVAL:
        try:
            if isinstance(interval, list):
                interval = [TextContentInterval(**interval_) for interval_ in interval]
            else:
                interval = [TextContentInterval(**interval)]
        except Exception as e:
            message = f'Data Asset Onboarding Error: Text Interval in row {index} of Column "{metadata.name}" is not following the format. Check the "TextContentInterval" class for the correct format.'
            logging.exception(message)
            raise Exception(message)
    elif metadata.dtype == DataType.VIDEO_INTERVAL:
        try:
            if isinstance(interval, list):
                interval = [VideoContentInterval(**interval_) for interval_ in interval]
            else:
                interval = [VideoContentInterval(**interval)]
        except Exception as e:
            message = f'Data Asset Onboarding Error: Video Interval in row {index} of Column "{metadata.name}" is not following the format. Check the "VideoContentInterval" class for the correct format.'
            logging.exception(message)
            raise Exception(message)
    return interval


def run(metadata: MetaData, paths: List, folder: Path, batch_size: int = 1000) -> Tuple[List[File], int, int]:
    """Process a list of local interval files, compress and upload them to pre-signed URLs in S3

    Explanation:
        Each interval on "paths" is processed. If the interval content is in a public link or local file, it will be downloaded and added to an index CSV file.
        The intervals are processed in batches such that at each "batch_size" texts, the index CSV file is uploaded into a pre-signed URL in s3 and reset.

    Args:
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Path): local folder to save compressed files before upload them to s3.

    Returns:
        Tuple[List[File], int, int]: list of s3 links, data colum index and number of rows
    """
    logging.debug(f'Data Asset Onboarding: Processing "{metadata.name}".')
    interval_folder = Path(".")
    if metadata.storage_type in [StorageType.FILE, StorageType.TEXT]:
        interval_folder = Path(os.path.join(folder, "data"))
        interval_folder.mkdir(exist_ok=True)

    idx = 0
    data_column_idx = -1
    files, batch = [], []
    for i in tqdm(range(len(paths)), desc=f' Data "{metadata.name}" onboarding progress', position=1, leave=False):
        path = paths[i]
        try:
            dataframe = pd.read_csv(path)
        except Exception as e:
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

        # process intervals
        for j in tqdm(range(len(dataframe)), desc=" File onboarding progress", position=2, leave=False):
            row = dataframe.iloc[j]
            try:
                interval = row[metadata.name]
            except Exception as e:
                message = f'Data Asset Onboarding Error: Column "{metadata.name}" not found in the local file {path}.'
                logging.exception(message)
                raise Exception(message)

            # interval = validate_format(index=j, interval=interval, metadata=metadata)

            try:
                interval = process_interval(interval, metadata.storage_type)
                batch.append(interval)
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
                s3_link = upload_data(file_name, content_type="text/csv", content_encoding="gzip")
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
        s3_link = upload_data(file_name, content_type="text/csv", content_encoding="gzip")
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        # get data column index
        data_column_idx = df.columns.to_list().index(metadata.name)
        batch = []
    return files, data_column_idx, idx
