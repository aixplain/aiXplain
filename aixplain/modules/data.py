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
    Data Class
"""

from aixplain.modules.file import File
from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.language import Language
from aixplain.enums.onboard_status import OnboardStatus
from aixplain.enums.privacy import Privacy
from typing import List, Optional, Text, Any


class Data:
    def __init__(
        self,
        id: Text,
        name: Text,
        dtype: DataType,
        privacy: Privacy,
        onboard_status: OnboardStatus,
        data_column: Optional[Any] = None,
        start_column: Optional[Any] = None,
        end_column: Optional[Any] = None,
        files: List[File] = [],
        languages: List[Language] = [],
        dsubtype: DataSubtype = DataSubtype.OTHER,
        length: Optional[int] = None,
        **kwargs
    ) -> None:
        """Data Class.

        Description:
            Data consists of a list of samples of same type and genre.

        Args:
            id (Text): Data ID
            name (Text): Data Name
            dtype (DataType): Data Type
            privacy (Privacy): Privacy of data
            onboard_status (OnboardStatus): onboard status
            data_column (Optional[Any], optional): Column index/name where the data is on a structured file (e.g. CSV). Defaults to None.
            start_column (Optional[Any], optional): Column index/name where the start indexes is on a structured file (e.g. CSV). Defaults to None.
            end_column (Optional[Any], optional): Column index/name where the end indexes is on a structured file (e.g. CSV). Defaults to None.
            files (List[File], optional): List of files where the data instances are stored. Defaults to [].
            languages (List[Language], optional): List of languages which the data consists of. Defaults to [].
            dsubtype (DataSubtype, optional): Data subtype (e.g., age, topic, race, split, etc.), used in datasets metadata. Defaults to Other.
            length (Optional[int], optional): Number of rows in the Data. Defaults to None.
        """
        self.id = id
        self.name = name
        self.dtype = dtype
        self.privacy = privacy
        if isinstance(onboard_status, str):
            onboard_status = OnboardStatus(onboard_status)
        self.onboard_status = onboard_status
        self.files = files
        if data_column is None:
            self.data_column = name
        else:
            self.data_column = data_column
        self.start_column = start_column
        self.end_column = end_column
        self.languages = []
        for language in languages:
            if isinstance(language, str):
                language = Language(language)
            self.languages.append(language)
        self.dsubtype = dsubtype
        self.length = length
        self.kwargs = kwargs
