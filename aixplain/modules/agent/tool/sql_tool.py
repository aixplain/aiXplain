"""SQL tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute SQL queries
against databases and CSV files.

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

__author__ = "aiXplain"

import os
import warnings
import validators
import pandas as pd
import numpy as np
from typing import Text, Optional, Dict, List, Union
import sqlite3
from aixplain.enums import AssetStatus
from aixplain.modules.agent.tool import DeployableTool


class SQLToolError(Exception):
    """Base exception for SQL Tool errors."""

    pass


class CSVError(SQLToolError):
    """Exception for CSV-related errors."""

    pass


class DatabaseError(SQLToolError):
    """Exception for database-related errors."""

    pass


def clean_column_name(col: Text) -> Text:
    """Clean column names by replacing spaces and special characters with underscores.

    This function makes column names SQLite-compatible by:
    1. Converting to lowercase
    2. Replacing special characters with underscores
    3. Removing duplicate underscores
    4. Adding 'col_' prefix to names starting with numbers

    Args:
        col (Text): The original column name.

    Returns:
        Text: The cleaned, SQLite-compatible column name.
    """
    # Replace special characters with underscores
    cleaned = col.strip().lower()
    cleaned = "".join(c if c.isalnum() else "_" for c in cleaned)
    # Remove multiple consecutive underscores
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    # Remove leading/trailing underscores
    cleaned = cleaned.strip("_")

    # Add 'col_' prefix to columns that start with numbers
    if cleaned[0].isdigit():
        cleaned = "col_" + cleaned

    return cleaned


def check_duplicate_columns(df: pd.DataFrame) -> None:
    """Check for duplicate column names in DataFrame after cleaning.

    This function checks if any column names would become duplicates after being
    cleaned for SQLite compatibility.

    Args:
        df (pd.DataFrame): The DataFrame to check for duplicate column names.

    Raises:
        CSVError: If any cleaned column names would be duplicates.
    """
    # Get all column names
    columns = df.columns.tolist()
    # Get cleaned column names
    cleaned_columns = [clean_column_name(col) for col in columns]

    # Check for duplicates in cleaned names
    seen = set()
    duplicates = []

    for original, cleaned in zip(columns, cleaned_columns):
        if cleaned in seen:
            duplicates.append(original)
        seen.add(cleaned)

    if duplicates:
        raise CSVError(f"CSV file contains duplicate column names after cleaning: {', '.join(duplicates)}")


def infer_sqlite_type(dtype) -> Text:
    """Infer SQLite type from pandas dtype.

    This function maps pandas data types to appropriate SQLite types:
    - Integer types -> INTEGER
    - Float types -> REAL
    - Boolean types -> INTEGER
    - Datetime types -> TIMESTAMP
    - All others -> TEXT

    Args:
        dtype: The pandas dtype to convert.

    Returns:
        Text: The corresponding SQLite type.

    Note:
        Issues a warning when falling back to TEXT type.
    """
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    elif pd.api.types.is_bool_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        warnings.warn(f"Column with dtype '{dtype}' will be stored as TEXT in SQLite")
        return "TEXT"


def get_table_schema(database_path: str) -> str:
    """Get the schema of all tables in the SQLite database.

    This function retrieves the CREATE TABLE statements for all tables in the database.

    Args:
        database_path (str): Path to the SQLite database file.

    Returns:
        str: A string containing all table schemas, separated by newlines.

    Raises:
        DatabaseError: If the database file doesn't exist or there's an error accessing it.

    Note:
        Issues a warning if no tables are found in the database.
    """
    if not os.path.exists(database_path):
        raise DatabaseError(f"Database file '{database_path}' does not exist")

    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sql
                FROM sqlite_master
                WHERE type='table' AND sql IS NOT NULL
            """
            )
            schemas = cursor.fetchall()
            if not schemas:
                warnings.warn(f"No tables found in database '{database_path}'")
            return "\n".join(schema[0] for schema in schemas if schema[0])
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to get table schema: {str(e)}")
    except Exception as e:
        raise DatabaseError(f"Unexpected error while getting table schema: {str(e)}")


def create_database_from_csv(csv_path: str, database_path: str, table_name: str = None) -> str:
    """Create SQLite database from CSV file and return the schema.

    This function creates or modifies a SQLite database by importing data from a CSV file.
    It handles column name cleaning, data type inference, and data conversion.

    Args:
        csv_path (str): Path to the CSV file to import.
        database_path (str): Path where the SQLite database should be created/modified.
        table_name (str, optional): Name for the table to create. If not provided,
            uses the CSV filename (cleaned). Defaults to None.

    Returns:
        str: The schema of the created database.

    Raises:
        CSVError: If there are issues with the CSV file (doesn't exist, empty, parsing error).
        DatabaseError: If there are issues with database creation or modification.

    Note:
        - Issues warnings for column name changes and existing database/table modifications.
        - Automatically cleans column names for SQLite compatibility.
        - Handles NULL values, timestamps, and numeric data types appropriately.
    """
    if not os.path.exists(csv_path):
        raise CSVError(f"CSV file '{csv_path}' does not exist")
    if not csv_path.endswith(".csv"):
        raise CSVError(f"File '{csv_path}' is not a CSV file")

    try:
        # Load CSV file
        df = pd.read_csv(csv_path)

        if df.empty:
            raise CSVError(f"CSV file '{csv_path}' is empty")

        # Clean column names and track changes
        original_columns = df.columns.tolist()
        cleaned_columns = [clean_column_name(col) for col in original_columns]
        changed_columns = [
            (orig, cleaned) for orig, cleaned in zip(original_columns, cleaned_columns) if orig != cleaned
        ]

        if changed_columns:
            changes = ", ".join([f"'{orig}' to '{cleaned}'" for orig, cleaned in changed_columns])
            warnings.warn(f"Column names were cleaned for SQLite compatibility: {changes}")

        df.columns = cleaned_columns

        # Connect to SQLite database
        if os.path.exists(database_path):
            warnings.warn(f"Database '{database_path}' already exists and will be modified")

        try:
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()

                # Check if table already exists

                if table_name is None:
                    table_name = clean_column_name(os.path.splitext(os.path.basename(csv_path))[0])
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if cursor.fetchone():
                    warnings.warn(f"Table '{table_name}' already exists in the database and will be replaced")
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

                # Create column definitions for SQL table
                cols_definitions = []
                for col, dtype in df.dtypes.items():
                    col_type = infer_sqlite_type(dtype)
                    cols_definitions.append(f'"{col}" {col_type}')

                table_columns = ", ".join(cols_definitions)

                # Create the table
                create_table_query = f"""
                CREATE TABLE {table_name} (
                    {table_columns}
                )
                """
                cursor.execute(create_table_query)

                # Insert data into table
                total_rows = len(df)
                for idx, row in enumerate(df.itertuples(index=False), 1):
                    # Convert all data to Python native types that SQLite can handle
                    row_data = []
                    for val in row:
                        if pd.isna(val):
                            row_data.append(None)
                        elif isinstance(val, pd.Timestamp):
                            row_data.append(val.strftime("%Y-%m-%d %H:%M:%S"))
                        elif isinstance(val, (np.int64, np.int32)):
                            row_data.append(int(val))
                        elif isinstance(val, (np.float64, np.float32)):
                            row_data.append(float(val))
                        else:
                            row_data.append(str(val))

                    placeholders = ", ".join(["?" for _ in df.columns])
                    column_names = ", ".join([f'"{col}"' for col in df.columns])
                    insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                    try:
                        cursor.execute(insert_query, tuple(row_data))
                    except sqlite3.Error as e:
                        raise DatabaseError(f"Error inserting row {idx}/{total_rows}: {str(e)}")

                conn.commit()

        except sqlite3.Error as e:
            raise DatabaseError(f"SQLite error: {str(e)}")

        # Get the schema
        try:
            return get_table_schema(database_path)
        except DatabaseError as e:
            raise DatabaseError(f"Failed to get schema after creating database: {str(e)}")

    except pd.errors.EmptyDataError:
        raise CSVError(f"CSV file '{csv_path}' is empty")
    except pd.errors.ParserError as e:
        raise CSVError(f"Failed to parse CSV file: {str(e)}")
    except Exception as e:
        if isinstance(e, CSVError):
            raise e
        raise CSVError(f"Unexpected error while processing CSV file: {str(e)}")


def get_table_names_from_schema(schema: str) -> List[str]:
    """Extract table names from a database schema string.

    This function parses CREATE TABLE statements to extract table names.

    Args:
        schema (str): The database schema string containing CREATE TABLE statements.

    Returns:
        List[str]: A list of table names found in the schema. Returns an empty list
            if no tables are found or if the schema is empty.
    """
    if not schema:
        return []

    table_names = []
    for line in schema.split("\n"):
        line = line.strip()
        if line.startswith("CREATE TABLE"):
            # Extract table name from CREATE TABLE statement
            table_name = line.split("CREATE TABLE")[1].strip().split("(")[0].strip().strip("\"'")
            table_names.append(table_name)
    return table_names


class SQLTool(DeployableTool):
    """A tool for executing SQL commands in an SQLite database.

    This tool provides an interface for interacting with SQLite databases, including
    executing queries, managing schema, and handling table operations. It supports
    both read-only and write operations based on configuration.

    Attributes:
        description (Text): A description of what the SQL tool does.
        database (Text): The database URI or path.
        schema (Text): The database schema containing table definitions.
        tables (Optional[Union[List[Text], Text]]): List of table names that can be
            accessed by this tool. If None, all tables are accessible.
        enable_commit (bool): Whether write operations (INSERT, UPDATE, DELETE) are
            allowed. If False, only read operations are permitted.
        status (AssetStatus): The current status of the tool (DRAFT or ONBOARDED).
    """

    def __init__(
        self,
        name: Text,
        description: Text,
        database: Text,
        schema: Optional[Text] = None,
        tables: Optional[Union[List[Text], Text]] = None,
        enable_commit: bool = False,
        **additional_info,
    ) -> None:
        """Initialize a new SQLTool instance.

        Args:
            name (Text): The name of the tool.
            description (Text): A description of what the SQL tool does.
            database (Text): The database URI or path. Can be a local file path,
                S3 URI, or HTTP(S) URL.
            schema (Optional[Text], optional): The database schema containing table
                definitions. If not provided, will be inferred from the database.
                Defaults to None.
            tables (Optional[Union[List[Text], Text]], optional): List of table names
                that can be accessed by this tool. If not provided, all tables are
                accessible. Defaults to None.
            enable_commit (bool, optional): Whether write operations are allowed.
                If False, only read operations are permitted. Defaults to False.
            **additional_info: Additional keyword arguments for tool configuration.

        Raises:
            SQLToolError: If required parameters are missing or invalid.
        """
        super().__init__(name=name, description=description, **additional_info)

        self.database = database
        self.schema = schema
        self.tables = tables if isinstance(tables, list) else [tables] if tables else None
        self.enable_commit = enable_commit
        self.status = AssetStatus.ONBOARDED  # TODO: change to DRAFT when we have a way to onboard the tool
        self.validate()

    def to_dict(self) -> Dict[str, Text]:
        """Convert the tool instance to a dictionary representation.

        Returns:
            Dict[str, Text]: A dictionary containing the tool's configuration with keys:
                - name: The tool's name
                - description: The tool's description
                - parameters: List of parameter dictionaries containing:
                    - database: The database URI or path
                    - schema: The database schema
                    - tables: Comma-separated list of table names or None
                    - enable_commit: Whether write operations are allowed
                - type: Always "sql"
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [
                {"name": "database", "value": self.database},
                {"name": "schema", "value": self.schema},
                {"name": "tables", "value": ",".join(self.tables) if self.tables is not None else None},
                {"name": "enable_commit", "value": self.enable_commit},
            ],
            "type": "sql",
        }

    def validate(self):
        """Validate the SQL tool's configuration.

        This method performs several checks:
        1. Verifies required fields (description, database) are provided
        2. Validates database path/URI format
        3. Infers schema from database if not provided
        4. Sets table list from schema if not provided
        5. Uploads local database file to storage

        Raises:
            SQLToolError: If any validation check fails or if there are issues with
                database access or file operations.
        """
        from aixplain.factories.file_factory import FileFactory

        if not self.description or self.description.strip() == "":
            raise SQLToolError("Description is required")
        if not self.database:
            raise SQLToolError("Database must be provided")
        # Handle database validation
        if not (
            str(self.database).startswith("s3://")
            or str(self.database).startswith("http://")
            or str(self.database).startswith("https://")
            or validators.url(self.database)
        ):
            if not os.path.exists(self.database):
                raise SQLToolError(f"Database '{self.database}' does not exist")
            if not self.database.endswith(".db"):
                raise SQLToolError(f"Database '{self.database}' must have .db extension")

            # Infer schema from database if not provided
            if not self.schema:
                try:
                    self.schema = get_table_schema(self.database)
                except DatabaseError as e:
                    raise SQLToolError(f"Failed to get database schema: {str(e)}")

            # Set tables if not already set
            if not self.tables:
                try:
                    self.tables = get_table_names_from_schema(self.schema)
                except Exception as e:
                    raise SQLToolError(f"Failed to set tables: {str(e)}")

            # Upload database
            try:
                self.database = FileFactory.create(local_path=self.database, is_temp=True)
            except Exception as e:
                raise SQLToolError(f"Failed to upload database: {str(e)}")

    def deploy(self) -> None:
        """Deploy the SQL tool by downloading and preparing the database.

        This method handles the deployment process:
        1. For HTTP(S) URLs: Downloads the database file
        2. Creates a unique local filename
        3. Uploads the database to the aiXplain platform
        4. Cleans up temporary files

        Raises:
            requests.exceptions.RequestException: If downloading the database fails.
            Exception: If there are issues with file operations or uploads.
        """
        import uuid
        import requests
        from pathlib import Path
        from aixplain.factories.file_factory import FileFactory
        from aixplain.enums import License

        # Generate unique filename with uuid4
        local_path = str(Path(f"{uuid.uuid4()}.db"))

        # Download database file
        if str(self.database).startswith(("http://", "https://")):
            response = requests.get(self.database)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(response.content)
            self.database = FileFactory.create(local_path=local_path, is_temp=False, license=License.MIT)
            os.remove(local_path)
