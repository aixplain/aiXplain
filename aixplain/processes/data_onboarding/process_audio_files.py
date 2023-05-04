__author__ = "thiagocastroferreira"

import logging
import os
import pandas as pd
import shutil
import tarfile

from aixplain.enums.file_type import FileType
from aixplain.enums.storage_type import StorageType
from aixplain.modules.file import File
from aixplain.modules.metadata import MetaData
from aixplain.utils.file_utils import upload_data
from pathlib import Path
from tqdm import tqdm
from typing import List, Optional, Tuple


def compress_folder(folder_path: str):
    with tarfile.open(folder_path + ".tgz", "w:gz") as tar:
        for name in os.listdir(folder_path):
            tar.add(os.path.join(folder_path, name))
    return folder_path + ".tgz"


def run(metadata: MetaData, paths: List, folder: Path, batch_size: int = 100) -> Tuple[List[File], int, int, int]:
    """Process a list of local audio files, compress and upload them to pre-signed URLs in S3

    Explanation:
        Each audio on "paths" is processed. If the audio is in a public link, this link is added into an index CSV file.
        If the audio is in a local path, it will be copied into a local folder and its path will be added to the index CSV file.
        The audios are processed in batches such that at each "batch_size" audios, the index CSV file is uploaded into a pre-signed URL in s3 and reset.
        If the audios are stored locally, the local folder is compressed into a .tgz file and also uploaded into S3.

    Args:
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Path): local folder to save compressed files before upload them to s3.

    Returns:
        Tuple[List[File], int, int, int]: list of s3 links; data, start and end columns index
    """
    # if files are stored locally, create a folder to store it
    audio_folder = Path(".")
    if metadata.storage_type == StorageType.FILE:
        audio_folder = Path(os.path.join(folder, "data"))
        audio_folder.mkdir(exist_ok=True)

    idx = 0
    data_column_idx, start_column_idx, end_column_idx = -1, -1, -1
    files, batch, start_times, end_times = [], [], [], []
    for i in tqdm(range(len(paths)), desc=f' Data "{metadata.name}" onboarding progress', position=1, leave=False):
        path = paths[i]
        try:
            dataframe = pd.read_csv(path)
        except Exception as e:
            message = f'Data Asset Onboarding Error: Local file "{path}" not found.'
            logging.exception(message)
            raise Exception(message)

        # process audios
        for j in tqdm(range(len(dataframe)), desc=" File onboarding progress", position=2, leave=False):
            row = dataframe.iloc[j]
            try:
                audio_path = row[metadata.name]
            except Exception as e:
                message = f'Data Asset Onboarding Error: Column "{metadata.name}" not found in the local file "{path}".'
                logging.exception(message)
                raise Exception(message)

            # adding audios
            if metadata.storage_type == StorageType.FILE:
                fname = os.path.basename(audio_path)
                new_path = os.path.join(audio_folder, fname)
                if os.path.exists(new_path) is False:
                    shutil.copy2(audio_path, new_path)
                batch.append(fname)
            else:
                batch.append(audio_path)

            # adding ranges to crop the audio if it is the case
            if metadata.start_column is not None:
                try:
                    start_times.append(row[metadata.start_column])
                except Exception as e:
                    message = f'Data Asset Onboarding Error: Column "{metadata.start_column}" not found.'
                    logging.exception(message)
                    raise Exception(message)

            if metadata.end_column is not None:
                try:
                    end_times.append(row[metadata.end_column])
                except Exception as e:
                    message = f'Data Asset Onboarding Error: Column "{metadata.end_column}" not found.'
                    logging.exception(message)
                    raise Exception(message)

            idx += 1
            if ((idx) % batch_size) == 0:
                batch_index = str(len(files) + 1).zfill(8)

                # save index file with a list of the audio files
                index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

                # if the audio are stored locally, zip them and upload to s3
                if metadata.storage_type == StorageType.FILE:
                    # rename the folder where the audio files are
                    data_file_name = f"{folder}/{metadata.name}-{batch_index}"
                    os.rename(audio_folder, data_file_name)
                    # rename the audio path in the audio folder
                    for z, audio_fname in enumerate(batch):
                        batch[z] = os.path.join(data_file_name, audio_fname)
                    df = pd.DataFrame({metadata.name: batch})
                    # compress the folder
                    compressed_folder = compress_folder(data_file_name)
                    # upload zipped audios into s3
                    s3_compressed_folder = upload_data(compressed_folder, content_type="application/x-tar")
                    # update index files pointing the s3 link
                    df["@SOURCE"] = s3_compressed_folder
                    # remove audio folder
                    shutil.rmtree(data_file_name)
                    # remove zipped file
                    os.remove(compressed_folder)
                    # create audio folder again
                    audio_folder = Path(os.path.join(folder, "data"))
                    audio_folder.mkdir(exist_ok=True)
                else:
                    df = pd.DataFrame({metadata.name: batch})

                # adding indexes
                start, end = idx - len(batch), idx
                df["@INDEX"] = range(start, end)

                # if there are start and end time ranges, save this into the index csv
                if len(start_times) > 0 and len(end_times) > 0:
                    df["@START_TIME"] = start_times
                    df["@END_TIME"] = end_times

                    start_column_idx = df.columns.to_list().index("@START_TIME")
                    end_column_idx = df.columns.to_list().index("@END_TIME")

                df.to_csv(index_file_name, compression="gzip", index=False)
                s3_link = upload_data(index_file_name, content_type="text/csv", content_encoding="gzip")
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                # get data column index
                data_column_idx = df.columns.to_list().index(metadata.name)
                # restart batch variables
                batch, start_times, end_times = [], [], []

    if len(batch) > 0:
        batch_index = str(len(files) + 1).zfill(8)

        # save index file with a list of the audio files
        index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"

        # if the audio are stored locally, zip them and upload to s3
        if metadata.storage_type == StorageType.FILE:
            # rename the folder where the audio files are
            data_file_name = f"{folder}/{metadata.name}-{batch_index}"
            os.rename(audio_folder, data_file_name)
            # rename the audio path in the audio folder
            for z, audio_fname in enumerate(batch):
                batch[z] = os.path.join(data_file_name, audio_fname)
            df = pd.DataFrame({metadata.name: batch})
            # compress the folder
            compressed_folder = compress_folder(data_file_name)
            # upload zipped audios into s3
            s3_compressed_folder = upload_data(compressed_folder, content_type="application/x-tar")
            # update index files pointing the s3 link
            df["@SOURCE"] = s3_compressed_folder
            # remove audio folder
            shutil.rmtree(data_file_name)
            # remove zipped file
            os.remove(compressed_folder)
            # create audio folder again
            audio_folder = Path(os.path.join(folder, "data"))
            audio_folder.mkdir(exist_ok=True)
        else:
            df = pd.DataFrame({metadata.name: batch})

        # adding indexes
        start, end = idx - len(batch), idx
        df["@INDEX"] = range(start, end)

        # if there are start and end time ranges, save this into the index csv
        if len(start_times) > 0 and len(end_times) > 0:
            df["@START_TIME"] = start_times
            df["@END_TIME"] = end_times

            start_column_idx = df.columns.to_list().index("@START_TIME")
            end_column_idx = df.columns.to_list().index("@END_TIME")

        df.to_csv(index_file_name, compression="gzip", index=False)
        s3_link = upload_data(index_file_name, content_type="text/csv", content_encoding="gzip")
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        # get data column index
        data_column_idx = df.columns.to_list().index(metadata.name)
        # restart batch variables
        batch, start_times, end_times = [], [], []
    return files, data_column_idx, start_column_idx, end_column_idx
