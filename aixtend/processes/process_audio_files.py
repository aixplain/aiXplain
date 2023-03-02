__author__="thiagocastroferreira"

import os
import pandas as pd
import shutil
import tarfile

from aixtend.enums.file_type import FileType
from aixtend.enums.storage_type import StorageType
from aixtend.modules.file import File
from aixtend.modules.metadata import MetaData
from aixtend.utils.file_utils import upload_data_s3
from pathlib import Path
from tqdm import tqdm
from typing import List, Union

def compress_folder(folder_path:str):
    with tarfile.open(folder_path + ".tgz", "w:gz") as tar:
        for name in os.listdir(folder_path):
            tar.add(os.path.join(folder_path, name))
    return folder_path + ".tgz"


def run(metadata: MetaData, paths: List, folder:Path, batch_size:int = 100) -> List[File]:
    """Process a list of local audio files, compress and upload them to pre-signed URLs in S3

    Args:
        metadata (MetaData): meta data of the asset
        paths (List): list of paths to local files
        folder (Path): local folder to save compressed files before upload them to s3.

    Returns:
        List[File]: list of s3 links
    """
    # if files are stored locally, create a folder to store it
    audio_folder = Path(".")
    if metadata.storage_type == StorageType.FILE:
        audio_folder = Path(os.path.join(folder, "data"))
        audio_folder.mkdir(exist_ok=True)

    idx = 0
    files, batch = [], []
    for path in paths:
        # TO DO: extract the split from file name
        try:
            audio_paths = pd.read_csv(path)[metadata.name]
        except:
            raise Exception(f"Data Asset Onboarding Error: Column {metadata.name} not found in the local file {path}.")

        # process audios
        for i in tqdm(range(len(audio_paths))):
            audio_path = audio_paths[i]
            if metadata.storage_type == StorageType.FILE:
                fname = os.path.basename(audio_path)
                new_path = os.path.join(audio_folder, fname)
                if os.path.exists(new_path) is False:
                    shutil.copy2(audio_path, new_path)
                batch.append(new_path)
            else:
                batch.append(audio_path)

            if ((idx + 1) % batch_size) == 0:
                batch_index = str(len(files) + 1).zfill(8)

                # save index file with a list of the audio files
                index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"
                df = pd.DataFrame({metadata.name: batch})
                start, end = idx - len(batch) + 1, idx + 1
                df["index"] = range(start, end)

                # if the audio are stored locally, zip them and upload to s3
                if metadata.storage_type == StorageType.FILE:
                    # rename the folder where the audio files are
                    data_file_name = f"{folder}/{metadata.name}-{batch_index}"
                    os.rename(audio_folder, data_file_name)
                    # compress the folder
                    compressed_folder = compress_folder(data_file_name)
                    # upload zipped audios into s3
                    upload_data_s3(compressed_folder, content_type="application/x-tar")
                    # update index files pointing the s3 link
                    df["source"] = compressed_folder
                    # remove audio folder
                    shutil.rmtree(data_file_name)
                    # remove zipped file
                    os.remove(compressed_folder)
                    # create audio folder again
                    audio_folder = Path(os.path.join(folder, "data"))
                    audio_folder.mkdir(exist_ok=True)

                df.to_csv(index_file_name, compression="gzip", index=False)
                s3_link = upload_data_s3(index_file_name, content_type="text/csv", content_encoding="gzip")
                files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
                batch = []
            
            idx += 1

    if len(batch) > 0:
        batch_index = str(len(files) + 1).zfill(8)

        # save index file with a list of the audio files
        index_file_name = f"{folder}/{metadata.name}-{batch_index}.csv.gz"
        df = pd.DataFrame({metadata.name: batch})
        start, end = idx - len(batch) + 1, idx + 1
        df["index"] = range(start, end)

        # if the audio are stored locally, zip them and upload to s3
        if metadata.storage_type == StorageType.FILE:
            # rename the folder where the audio files are
            data_file_name = f"{folder}/{metadata.name}-{batch_index}"
            os.rename(audio_folder, data_file_name)
            # compress the folder
            compressed_folder = compress_folder(data_file_name)
            # upload zipped audios into s3
            upload_data_s3(compressed_folder, content_type="application/x-tar")
            # update index files pointing the s3 link
            df["source"] = compressed_folder
            # remove audio folder
            shutil.rmtree(data_file_name)
            # remove zipped file
            os.remove(compressed_folder)
            # create audio folder again
            audio_folder = Path(os.path.join(folder, "data"))
            audio_folder.mkdir(exist_ok=True)

        df.to_csv(index_file_name, compression="gzip", index=False)
        s3_link = upload_data_s3(index_file_name, content_type="text/csv", content_encoding="gzip")
        files.append(File(path=s3_link, extension=FileType.CSV, compression="gzip"))
        batch = []
    return files