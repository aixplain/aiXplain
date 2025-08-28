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
    """A class representing a collection of data samples of the same type and genre.

    This class provides functionality for managing data in the aiXplain platform,
    supporting various data types, languages, and storage formats. It can handle
    both structured (e.g., CSV) and unstructured data files.

    Attributes:
        id (Text): ID of the data collection.
        name (Text): Name of the data collection.
        dtype (DataType): Type of data (e.g., text, audio, image).
        privacy (Privacy): Privacy settings for the data.
        onboard_status (OnboardStatus): Current onboarding status.
        data_column (Optional[Any]): Column identifier where data is stored in structured files.
        start_column (Optional[Any]): Column identifier for start indexes in structured files.
        end_column (Optional[Any]): Column identifier for end indexes in structured files.
        files (List[File]): List of files containing the data instances.
        languages (List[Language]): List of languages present in the data.
        dsubtype (DataSubtype): Subtype categorization of the data.
        length (Optional[int]): Number of samples/rows in the data collection.
        kwargs (dict): Additional keyword arguments for extensibility.
    """

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
        """Initialize a new Data instance.

        Args:
            id (Text): ID of the data collection.
            name (Text): Name of the data collection.
            dtype (DataType): Type of data (e.g., text, audio, image).
            privacy (Privacy): Privacy settings for the data.
            onboard_status (OnboardStatus): Current onboarding status of the data.
            data_column (Optional[Any], optional): Column identifier where data is stored in
                structured files (e.g., CSV). If None, defaults to the value of name.
            start_column (Optional[Any], optional): Column identifier where start indexes are
                stored in structured files. Defaults to None.
            end_column (Optional[Any], optional): Column identifier where end indexes are
                stored in structured files. Defaults to None.
            files (List[File], optional): List of files containing the data instances.
                Defaults to empty list.
            languages (List[Language], optional): List of languages present in the data.
                Can be provided as Language enums or language codes. Defaults to empty list.
            dsubtype (DataSubtype, optional): Subtype categorization of the data
                (e.g., age, topic, race, split). Defaults to DataSubtype.OTHER.
            length (Optional[int], optional): Number of samples/rows in the data collection.
                Defaults to None.
            **kwargs: Additional keyword arguments for extensibility.
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
