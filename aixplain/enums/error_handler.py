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
Date: May 26th 2023
Description:
    Error Handler Enum
"""

from enum import Enum


class ErrorHandler(Enum):
    """
    Enumeration class defining different error handler strategies.

    Attributes:
        SKIP (str): skip failed rows.
        FAIL (str): raise an exception.
    """

    SKIP = "skip"
    FAIL = "fail"
