__author__ = "aiXplain"

import pathlib

from aixtend.enums.data_split import DataSplit
from aixtend.enums.file_type import FileType
from typing import Optional, Union


class File:
    def __init__(
        self, path: Union[str, pathlib.Path], extension: Union[str, FileType], data_split: Optional[DataSplit] = None
    ) -> None:
        self.path = path

        if isinstance(extension, FileType):
            self.extension = extension
        else:
            try:
                self.extension = FileType(extension)
            except:
                raise Exception("File Error: This file extension is not supported.")

        self.data_split = data_split
