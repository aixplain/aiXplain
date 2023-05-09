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
    Meta-data Class
"""

from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.file_type import FileType
from aixplain.enums.language import Language
from aixplain.enums.privacy import Privacy
from aixplain.enums.storage_type import StorageType
from typing import List, Optional, Text


class MetaData:
    def __init__(
        self,
        name: Text,
        dtype: DataType,
        storage_type: StorageType,
        data_column: Optional[Text] = None,
        start_column: Optional[Text] = None,
        end_column: Optional[Text] = None,
        privacy: Optional[Privacy] = None,
        file_extension: Optional[FileType] = None,
        languages: List[Language] = [],
        dsubtype: DataSubtype = DataSubtype.OTHER,
        **kwargs
    ) -> None:
        """MetaData Class

        Description:
            This class is used to stored the meta-information of the Data Class.
            It may be used to describe Data during the onboarding process of a corpus or dataset.

        Args:
            name (Text): Data Name
            dtype (DataType): Data Type
            storage_type (StorageType): Data Storage (e.g. text, local file, web link)
            data_column (Optional[Text], optional): Column index/name where the data is on a structured file (e.g. CSV). Defaults to None.
            start_column (Optional[Text], optional): Column index/name where the start indexes is on a structured file (e.g. CSV). Defaults to None.
            end_column (Optional[Text], optional): Column index/name where the end indexes is on a structured file (e.g. CSV). Defaults to None.
            privacy (Optional[Privacy], optional): Privacy of data. Defaults to None.
            file_extension (Optional[FileType], optional): File extension (e.g. CSV, TXT, etc.). Defaults to None.
            languages (List[Language], optional): List of languages which the data consists of. Defaults to [].
            dsubtype (DataSubtype, optional): Data subtype (e.g., age, topic, race, split, etc.), used in datasets metadata. Defaults to Other.
        """
        self.name = name
        if isinstance(dtype, str):
            dtype = DataType(dtype)
        self.dtype = dtype

        if isinstance(storage_type, str):
            storage_type = StorageType(storage_type)
        self.storage_type = storage_type

        if data_column is None:
            self.data_column = name
        else:
            self.data_column = data_column

        self.start_column = start_column
        self.end_column = end_column

        if isinstance(privacy, str):
            privacy = Privacy(privacy)
        self.privacy = privacy
        self.file_extension = file_extension

        self.languages = []
        for language in languages:
            if isinstance(language, str):
                language = Language(language)
            self.languages.append(language)
        self.dsubtype = dsubtype
        self.kwargs = kwargs
