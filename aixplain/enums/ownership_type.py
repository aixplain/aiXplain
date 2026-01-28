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
Date: November 22nd 2023
Description:
    Asset Ownership Type
"""

from enum import Enum


class OwnershipType(Enum):
    """Enumeration of possible ownership types.

    This enum defines the different types of ownership that can be associated with
    an asset or resource, including subscribed and owned ownership.

    Attributes:
        SUBSCRIBED (str): Subscribed ownership type.
        OWNED (str): Owned ownership type.
    """
    SUBSCRIBED = "SUBSCRIBED"
    OWNED = "OWNED"

    def __str__(self):
        """Return the string representation of the ownership type.

        Returns:
            str: The ownership type value as a string.
        """
        return self._value_
