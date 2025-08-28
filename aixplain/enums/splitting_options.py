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
Date: May 30th 2025
Description:
    Splitting Options Enum
"""

from enum import Enum


class SplittingOptions(str, Enum):
    """Enumeration of possible splitting options.

    This enum defines the different ways that text can be split into chunks,
    including by word, sentence, passage, page, and line.

    Attributes:
        WORD (str): Split by word.
        SENTENCE (str): Split by sentence.
        PASSAGE (str): Split by passage.
        PAGE (str): Split by page.
        LINE (str): Split by line.
    """
    WORD = "word"
    SENTENCE = "sentence"
    PASSAGE = "passage"
    PAGE = "page"
    LINE = "line"

    def __str__(self):
        """Return the string representation of the splitting option.

        Returns:
            str: The splitting option value as a string.
        """
        return self._value_
