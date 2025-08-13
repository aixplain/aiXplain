__author__ = "thiagocastroferreira"

import logging
import os
import pandas as pd
import shutil
import tarfile
import validators

from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.file_type import FileType
from aixplain.enums.storage_type import StorageType
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import upload_data
from pathlib import Path
from tqdm import tqdm
from typing import List, Tuple

AUDIO_MAX_SIZE = 50000000
IMAGE_TEXT_MAX_SIZE = 25000000


def compress_folder(folder_path: str) -> str:
    """Compress a folder into a gzipped tar archive.

    This function takes a folder and creates a compressed tar archive (.tgz)
    containing all files in the folder. The archive is created in the same
    directory as the input folder.

    Args:
        folder_path (str): Path to the folder to be compressed.

    Returns:
        str: Path to the created .tgz archive file.
    """
    with tarfile.open(folder_path + ".tgz", "w:gz") as tar:
        for name in os.listdir(folder_path):
            tar.add(os.path.join(folder_path, name))
    return folder_path + ".tgz"


def run(metadata: MetaData, paths: List, folder: Path, batch_size: int = 100) -> Tuple[List[File], int, int, int, int]:
    """Process media files and prepare them for upload to S3 with batch processing.

    This function handles the processing and uploading of media files (audio, image, etc.)
    to S3. It supports both local files and public URLs, processes them in batches,
    and creates index files to track the media locations and any interval information.

    The process works as follows:
    1. For each media file in the input paths:
       - If it's a public URL: Add the URL to an index CSV file
       - If it's a local file: Copy to a temporary folder and add path to index
    2. After every batch_size files:
       - For local files: Compress the folder into .tgz and upload to S3
       - Create and upload an index CSV file with paths and metadata
       - Reset for the next batch

    Args:
        metadata (MetaData): Metadata object containing information about the media type,
            storage type, and column mappings.
        paths (List): List of paths to CSV files containing media information.
        folder (Path): Local folder path where temporary files and compressed archives
            will be stored during processing.
        batch_size (int, optional): Number of media files to process in each batch.
            Defaults to 100.

    Returns:
        Tuple[List[File], int, int, int, int]: A tuple containing:
            - List[File]: List of File objects pointing to uploaded index files in S3
            - int: Index of the data column in the index CSV
            - int: Index of the start column for intervals (-1 if not used)
            - int: Index of the end column for intervals (-1 if not used)
            - int: Total number of media files processed

    Raises:
        Exception: If:
            - Input files are not found
            - Required columns are missing
            - File size limits are exceeded (50MB for audio, 25MB for others)
            - Invalid interval configurations are detected
    """
    if metadata.dtype != DataType.LABEL:
        assert (
            metadata.storage_type != StorageType.TEXT
        ), f'Data Asset Onboarding Error: Column "{metadata.name}" of type "{metadata.dtype}" can not be stored in text.'

    # if files are stored locally, create a folder to store it
    media_folder = Path(".")
    if metadata.storage_type == StorageType.FILE:
        media_folder = Path(os.path.join(folder, "data"))
        media_folder.mkdir(exist_ok=True)

    idx = 0
    data_column_idx, start_column_idx, end_column_idx = -1, -1, -1
    files, batch, start_intervals, end_intervals = [], [], [], []
    for i in tqdm(range(len(paths)), desc=f' Data "{metadata.name}" onboarding progress', position=1, leave=False):
        path = paths[i]

        if not os.path.exists(path):
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

        dataframe = pd.read_csv(path)

        # process medias
        for j in tqdm(range(len(dataframe)), desc=" File onboarding progress", position=2, leave=False):
            row = dataframe.iloc[j]
            try:
                media_path = row[metadata.name]
            except Exception:
                message = f'Data Asset Onboarding Error: Column "{metadata.name}" not found in the local file "{path}".'
                logging.exception(message)
                raise Exception(message)

            # adding medias
            if metadata.storage_type == StorageType.FILE:
                if metadata.dsubtype == DataSubtype.INTERVAL:
                    # check whether the interval is in audio, image, text and video
                    assert metadata.dtype in [
                        DataType.AUDIO,
                        DataType.IMAGE,
                        DataType.TEXT,
                        DataType.VIDEO,
                    ], f'Data Asset Onboarding Error: Content Intervals do not work with "{metadata.dtype}".'
                    assert (
                        os.path.getsize(media_path) <= IMAGE_TEXT_MAX_SIZE
                    ), f'Data Asset Onboarding Error: Local interval file "{media_path}" exceeds the size limit of 25 MB.'
                    _, file_extension = os.path.splitext(media_path)
                    assert (
                        file_extension == ".json"
                    ), f'Data Asset Onboarding Error: Local interval files, such as "{media_path}", must be a JSON.'
                elif metadata.dtype == DataType.AUDIO:
                    assert (
                        os.path.getsize(media_path) <= AUDIO_MAX_SIZE
                    ), f'Data Asset Onboarding Error: Local audio file "{media_path}" exceeds the size limit of 50 MB.'
                elif metadata.dtype == DataType.LABEL:
                    assert (
                        os.path.getsize(media_path) <= IMAGE_TEXT_MAX_SIZE
                    ), f'Data Asset Onboarding Error: Local label file "{media_path}" exceeds the size limit of 25 MB.'
                else:
                    assert (
                        os.path.getsize(media_path) <= IMAGE_TEXT_MAX_SIZE
                    ), f'Data Asset Onboarding Error: Local image file "{media_path}" exceeds the size limit of 25 MB.'
                fname = os.path.basename(media_path)
                new_path = os.path.join(media_folder, fname)
                if os.path.exists(new_path) is False:
                    shutil.copy2(media_path, new_path)
                batch.append(fname)
            else:
                if metadata.storage_type == StorageType.TEXT and (
                    str(media_path).startswith("s3://")
                    or str(media_path).startswith("http://")
                    or str(media_path).startswith("https://")
                    or validators.url(media_path)
                ):
                    media_path = "DONOTDOWNLOAD" + str(media_path)
                batch.append(media_path)

            # crop intervals can not be used with interval data types
            if metadata.start_column is not None or metadata.end_column is not None:
                assert (
                    metadata.dsubtype != DataSubtype.INTERVAL
                ), "Data Asset Onboarding Error: Interval data types can not be cropped. Remove start and end columns."

            # adding ranges to crop the media if it is the case
            if metadata.start_column is not None:
                try:
                    start_intervals.append(row[metadata.start_column])
                except Exception:
                    message = f'Data Asset Onboarding Error: Column "{metadata.start_column}" not found.'
                    logging.exception(message)
                    raise Exception(message)

            if metadata.end_column is not None:
                try:
                    end_intervals.append(row[metadata.end_column])
                except Exception:
                    message = f'Data Asset Onboarding Error: Column "{metadata.end_column}" not found.'
                    logging.exception(message)
                    raise Exception(message)

            idx += 1
            if ((idx) % batch_size) == 0:
                batch_index = str(len(files) + 1).zfill(8)

                # save index file with a list of the media files
                index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

                # if the media are stored locally, zip them and upload to s3
                if metadata.storage_type == StorageType.FILE:
                    # rename the folder where the media files are
                    data_file_name = f"{folder}/{metadata.name}-{batch_index}"
                    os.rename(media_folder, data_file_name)
                    # rename the media path in the media folder
                    for z, media_fname in enumerate(batch):
                        batch[z] = os.path.join(data_file_name, media_fname)
                    df = pd.DataFrame({metadata.name: batch})
                    # compress the folder
                    compressed_folder = compress_folder(data_file_name)
                    # upload zipped medias into s3
                    s3_compressed_folder = upload_data(
                        compressed_folder, content_type="application/x-tar", return_download_link=False
                    )
                    # update index files pointing the s3 link
                    df["@SOURCE"] = s3_compressed_folder
                    # remove media folder
                    shutil.rmtree(data_file_name)
                    # remove zipped file
                    os.remove(compressed_folder)
                    # create media folder again
                    media_folder = Path(os.path.join(folder, "data"))
                    media_folder.mkdir(exist_ok=True)
                else:
                    df = pd.DataFrame({metadata.name: batch})

                # adding indexes
                start, end = idx - len(batch), idx
                df["@INDEX"] = range(start, end)

                # if there are start and end time ranges, save this into the index csv
                if len(start_intervals) > 0 and len(end_intervals) > 0:
                    if metadata.dtype == DataType.AUDIO:
                        start_column = "@START_TIME"
                        end_column = "@END_TIME"
                    else:
                        start_column = "@START"
                        end_column = "@END"

                    df[start_column] = start_intervals
                    df[end_column] = end_intervals

                    start_column_idx = df.columns.to_list().index(start_column)
                    end_column_idx = df.columns.to_list().index(end_column)

                df.to_csv(index_file_name, compression="gzip", index=False)
                s3_link = upload_data(
                    index_file_name, content_type="text/csv", content_encoding="gzip", return_download_link=False
                )
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                # get data column index
                data_column_idx = df.columns.to_list().index(metadata.name)
                # restart batch variables
                batch, start_intervals, end_intervals = [], [], []

    if len(batch) > 0:
        batch_index = str(len(files) + 1).zfill(8)

        # save index file with a list of the media files
        index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

        # if the media are stored locally, zip them and upload to s3
        if metadata.storage_type == StorageType.FILE:
            # rename the folder where the media files are
            data_file_name = f"{folder}/{metadata.name}-{batch_index}"
            os.rename(media_folder, data_file_name)
            # rename the media path in the media folder
            for z, media_fname in enumerate(batch):
                batch[z] = os.path.join(data_file_name, media_fname)
            df = pd.DataFrame({metadata.name: batch})
            # compress the folder
            compressed_folder = compress_folder(data_file_name)
            # upload zipped medias into s3
            s3_compressed_folder = upload_data(compressed_folder, content_type="application/x-tar", return_download_link=False)
            # update index files pointing the s3 link
            df["@SOURCE"] = s3_compressed_folder
            # remove media folder
            shutil.rmtree(data_file_name)
            # remove zipped file
            os.remove(compressed_folder)
            # create media folder again
            media_folder = Path(os.path.join(folder, "data"))
            media_folder.mkdir(exist_ok=True)
        else:
            df = pd.DataFrame({metadata.name: batch})

        # adding indexes
        start, end = idx - len(batch), idx
        df["@INDEX"] = range(start, end)

        # if there are start and end time ranges, save this into the index csv
        if len(start_intervals) > 0 and len(end_intervals) > 0:
            if metadata.dtype == DataType.AUDIO:
                start_column = "@START_TIME"
                end_column = "@END_TIME"
            else:
                start_column = "@START"
                end_column = "@END"

            df[start_column] = start_intervals
            df[end_column] = end_intervals

            start_column_idx = df.columns.to_list().index(start_column)
            end_column_idx = df.columns.to_list().index(end_column)

        df.to_csv(index_file_name, compression="gzip", index=False)
        s3_link = upload_data(index_file_name, content_type="text/csv", content_encoding="gzip", return_download_link=False)
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        # get data column index
        data_column_idx = df.columns.to_list().index(metadata.name)
        # restart batch variables
        batch, start_intervals, end_intervals = [], [], []
    return files, data_column_idx, start_column_idx, end_column_idx, idx
