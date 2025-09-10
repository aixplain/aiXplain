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
    Data Type Enum
"""

from enum import Enum


class DataType(str, Enum):
    """Enumeration of supported data types in the aiXplain system.

    This enum defines all the data types that can be processed by the system,
    including various media types and basic data types.

    Attributes:
        AUDIO (str): Audio data type.
        FLOAT (str): Floating-point number data type.
        IMAGE (str): Image data type.
        INTEGER (str): Integer number data type.
        LABEL (str): Label/category data type.
        TENSOR (str): Tensor/multi-dimensional array data type.
        TEXT (str): Text data type.
        VIDEO (str): Video data type.
        EMBEDDING (str): Vector embedding data type.
        NUMBER (str): Generic number data type.
        BOOLEAN (str): Boolean data type.
    """
    AUDIO = "audio"
    FLOAT = "float"
    IMAGE = "image"
    INTEGER = "integer"
    LABEL = "label"
    TENSOR = "tensor"
    TEXT = "text"
    VIDEO = "video"
    EMBEDDING = "embedding"
    NUMBER = "number"
    BOOLEAN = "boolean"

    def __str__(self) -> str:
        """Return the string representation of the data type.

        Returns:
            str: The data type value as a string.
        """
        return self._value_
