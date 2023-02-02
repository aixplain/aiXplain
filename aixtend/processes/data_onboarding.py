__author__ = "aiXplain"

import os
import pandas as pd

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
                if extension != FileType.CSV:
                    raise Exception("Onboarding Error: Format not supported.")
                paths.append(subpath)
        else:
            extension = FileType(path.suffix)
            if extension != FileType.CSV:
                raise Exception("Onboarding Error: Format not supported.")
            paths.append(path)
    return paths


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


def process_data_files(data_asset_name: str, metadata: MetaData, paths: List, batch_size: int, folder: Union[str, Path] = None):
    if folder is None:
        folder = data_asset_name

    files, batch = [], []
    for path in paths:
        # TO DO: extract the split from file name
        content = pd.read_csv(path)[metadata.name]
        ndigits, nbdigits = max([4, len(str(len(content)))]), max([4, len(str(int(len(content) / batch_size)))])

        # process texts and labels
        if metadata.dtype in [DataType.TEXT, DataType.LABEL]:
            for idx, row in enumerate(content):
                text = process_text(row, metadata.storage_type)
                batch.append(text)

                if (len(batch) % batch_size) == 0:
                    index = str(idx + 1).zfill(ndigits)
                    batch_index = str(len(files) + 1).zfill(nbdigits)
                    file_name = f"{folder}/{metadata.name}-{batch_index}-{index}.csv.gz"

                    df = pd.DataFrame({metadata.name: batch})
                    df["index"] = range(len(files) * batch_size, len(files) * batch_size + len(batch))
                    df.to_csv(file_name, compression="gzip", index=False)
                    files.append(File(path=Path(file_name), extension=FileType.CSV, compression="gzip"))
                    batch = []

            if len(batch) > 0:
                index = str(idx + 1).zfill(ndigits - len(str(idx + 1)))
                batch_index = str(len(files)).zfill(nbdigits - len(str(len(files))))
                file_name = f"{folder}/{metadata.name}-{batch_index}-{index}.csv.gz"

                df = pd.DataFrame({metadata.name: batch})
                df["index"] = range(len(files) * batch_size, len(files) * batch_size + len(batch))
                df.to_csv(file_name, compression="gzip", index=False)
                files.append(File(path=Path(file_name), extension=FileType.CSV, compression="gzip"))
                batch = []
    return files
