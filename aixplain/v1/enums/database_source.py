__author__ = "aiXplain"

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

Author: Lucas Pavanelli and Thiago Castro Ferreira and Ahmet Gunduz
Date: March 7th 2025
Description:
    Database Source Type Enum
"""

from enum import Enum


class DatabaseSourceType(Enum):
    """Enumeration of supported database source types.

    This enum defines the different types of database sources that can be used
    for data storage and retrieval in the system.

    Attributes:
        POSTGRESQL (str): PostgreSQL database source type.
        SQLITE (str): SQLite database source type.
        CSV (str): CSV file source type.
    """

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    CSV = "csv"

    @classmethod
    def from_string(cls, source_type: str) -> "DatabaseSourceType":
        """Convert string to DatabaseSourceType enum

        Args:
            source_type (str): Source type string

        Returns:
            DatabaseSourceType: Corresponding enum value
        """
        try:
            return cls[source_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid source type: {source_type}")
