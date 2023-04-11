__author__ = "aiXplain"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: March 20th 2023
Description:
    File Class
"""

import pathlib

from aixplain.enums.data_split import DataSplit
from aixplain.enums.file_type import FileType
from typing import Optional, Text, Union


class File:
    def __init__(
        self,
        path: Union[Text, pathlib.Path],
        extension: Union[Text, FileType],
        data_split: Optional[DataSplit] = None,
        compression: Optional[Text] = None,
    ) -> None:
        """File Class

        Description:
            File where samples of a data is stored in

        Args:
            path (Union[Text, pathlib.Path]): File path
            extension (Union[Text, FileType]): File extension (e.g. CSV, TXT, etc.)
            data_split (Optional[DataSplit], optional): Data split of the file. Defaults to None.
            compression (Optional[Text], optional): Compression extension (e.g., .gz). Defaults to None.
        """
        self.path = path

        if isinstance(extension, FileType):
            self.extension = extension
        else:
            try:
                self.extension = FileType(extension)
            except Exception as e:
                raise Exception("File Error: This file extension is not supported.")

        self.compression = compression
        self.data_split = data_split
