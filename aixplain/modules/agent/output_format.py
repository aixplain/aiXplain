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


class OutputFormat(Text, Enum):
    """Enum representing different output formats for AI agent responses.

    This enum defines the possible output formats that can be used by AI agents.
    Each format is represented by a string constant.

    Attributes:
        MARKDOWN (Text): Markdown format for formatted text output.
        TEXT (Text): Plain text output.
        JSON (Text): JSON format for structured data output.
    """
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
