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

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: May 16th 2024
Description:
    Agentification Class
"""
import os
import validators
from typing import Text, Optional, Dict

from aixplain.modules.agent.tool import Tool


class SQLTool(Tool):
    """Tool to execute SQL commands in an SQLite database.

    Attributes:
        description (Text): description of the tool
        database (Text): database name
        schema (Text): database schema description
        table (Optional[Text]): table name (optional)
    """

    def __init__(
        self,
        description: Text,
        database: Text,
        schema: Text,
        table: Optional[Text] = None,
        **additional_info,
    ) -> None:
        """Tool to execute SQL query commands in an SQLite database.

        Args:
            description (Text): description of the tool
            database (Text): database name
            schema (Text): database schema description
            table (Optional[Text]): table name (optional)
        """
        super().__init__("", description, **additional_info)
        self.database = database
        self.schema = schema
        self.table = table

    def to_dict(self) -> Dict[str, Text]:
        return {
            "description": self.description,
            "parameters": [
                {"name": "database", "value": self.database},
                {"name": "schema", "value": self.schema},
                {"name": "table", "value": self.table},
            ],
            "type": "sql",
        }

    def validate(self):
        from aixplain.factories.file_factory import FileFactory

        assert self.description and self.description.strip() != "", "SQL Tool Error: Description is required"
        assert self.database and self.database.strip() != "", "SQL Tool Error: Database is required"
        if not (
            str(self.database).startswith("s3://")
            or str(self.database).startswith("http://")
            or str(self.database).startswith("https://")
            or validators.url(self.database)
        ):
            if not os.path.exists(self.database):
                raise Exception(f"SQL Tool Error: Database '{self.database}' does not exist")
            self.database = FileFactory.upload(local_path=self.database, is_temp=True)
        assert self.schema and self.schema.strip() != "", "SQL Tool Error: Schema is required"
