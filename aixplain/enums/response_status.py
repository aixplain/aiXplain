__author__ = "thiagocastroferreira"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: February 21st 2024
Description:
    Asset Enum
"""

from enum import Enum
from typing import Text


class ResponseStatus(Text, Enum):
    """Enumeration of possible response status values.

    This enum defines the different statuses that a response can be in, including
    in progress, success, and failure.

    Attributes:
        IN_PROGRESS (str): Response is in progress.
        SUCCESS (str): Response was successful.
        FAILED (str): Response failed.
    """
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    def __str__(self):
        """Return the string representation of the response status.

        Returns:
            str: The response status value as a string.
        """
        return self.value
