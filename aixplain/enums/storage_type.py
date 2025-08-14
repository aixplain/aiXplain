__author__ = "aiXplain"

"""
Copyright 2023 The aiXplain SDK authors

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
    Storage Type Enum
"""

from enum import Enum


class StorageType(Enum):
    """Enumeration of possible storage types.

    This enum defines the different types of storage that can be used to store
    assets, including text, URL, and file.

    Attributes:
        TEXT (str): Text storage type.
        URL (str): URL storage type.
        FILE (str): File storage type.
    """
    TEXT = "text"
    URL = "url"
    FILE = "file"

    def __str__(self):
        """Return the string representation of the storage type.

        Returns:
            str: The storage type value as a string.
        """
        return self._value_
