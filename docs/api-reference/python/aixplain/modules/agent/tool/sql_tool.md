---
sidebar_label: sql_tool
title: aixplain.modules.agent.tool.sql_tool
---

SQL tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute SQL queries
against databases and CSV files.

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: May 16th 2024
Description:
    Agentification Class

### SQLToolError Objects

```python
class SQLToolError(Exception)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L39)

Base exception for SQL Tool errors.

### CSVError Objects

```python
class CSVError(SQLToolError)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L45)

Exception for CSV-related errors.

### DatabaseError Objects

```python
class DatabaseError(SQLToolError)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L51)

Exception for database-related errors.

#### clean\_column\_name

```python
def clean_column_name(col: Text) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L57)

Clean column names by replacing spaces and special characters with underscores.

This function makes column names SQLite-compatible by:
1. Converting to lowercase
2. Replacing special characters with underscores
3. Removing duplicate underscores
4. Adding &#x27;col_&#x27; prefix to names starting with numbers

**Arguments**:

- `col` _Text_ - The original column name.
  

**Returns**:

- `Text` - The cleaned, SQLite-compatible column name.

#### check\_duplicate\_columns

```python
def check_duplicate_columns(df: pd.DataFrame) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L88)

Check for duplicate column names in DataFrame after cleaning.

This function checks if any column names would become duplicates after being
cleaned for SQLite compatibility.

**Arguments**:

- `df` _pd.DataFrame_ - The DataFrame to check for duplicate column names.
  

**Raises**:

- `CSVError` - If any cleaned column names would be duplicates.

#### infer\_sqlite\_type

```python
def infer_sqlite_type(dtype) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L118)

Infer SQLite type from pandas dtype.

This function maps pandas data types to appropriate SQLite types:
- Integer types -&gt; INTEGER
- Float types -&gt; REAL
- Boolean types -&gt; INTEGER
- Datetime types -&gt; TIMESTAMP
- All others -&gt; TEXT

**Arguments**:

- `dtype` - The pandas dtype to convert.
  

**Returns**:

- `Text` - The corresponding SQLite type.
  

**Notes**:

  Issues a warning when falling back to TEXT type.

#### get\_table\_schema

```python
def get_table_schema(database_path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L150)

Get the schema of all tables in the SQLite database.

This function retrieves the CREATE TABLE statements for all tables in the database.

**Arguments**:

- `database_path` _str_ - Path to the SQLite database file.
  

**Returns**:

- `str` - A string containing all table schemas, separated by newlines.
  

**Raises**:

- `DatabaseError` - If the database file doesn&#x27;t exist or there&#x27;s an error accessing it.
  

**Notes**:

  Issues a warning if no tables are found in the database.

#### create\_database\_from\_csv

```python
def create_database_from_csv(csv_path: str,
                             database_path: str,
                             table_name: str = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L190)

Create SQLite database from CSV file and return the schema.

This function creates or modifies a SQLite database by importing data from a CSV file.
It handles column name cleaning, data type inference, and data conversion.

**Arguments**:

- `csv_path` _str_ - Path to the CSV file to import.
- `database_path` _str_ - Path where the SQLite database should be created/modified.
- `table_name` _str, optional_ - Name for the table to create. If not provided,
  uses the CSV filename (cleaned). Defaults to None.
  

**Returns**:

- `str` - The schema of the created database.
  

**Raises**:

- `CSVError` - If there are issues with the CSV file (doesn&#x27;t exist, empty, parsing error).
- `DatabaseError` - If there are issues with database creation or modification.
  

**Notes**:

  - Issues warnings for column name changes and existing database/table modifications.
  - Automatically cleans column names for SQLite compatibility.
  - Handles NULL values, timestamps, and numeric data types appropriately.

#### get\_table\_names\_from\_schema

```python
def get_table_names_from_schema(schema: str) -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L318)

Extract table names from a database schema string.

This function parses CREATE TABLE statements to extract table names.

**Arguments**:

- `schema` _str_ - The database schema string containing CREATE TABLE statements.
  

**Returns**:

- `List[str]` - A list of table names found in the schema. Returns an empty list
  if no tables are found or if the schema is empty.

### SQLTool Objects

```python
class SQLTool(DeployableTool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L343)

A tool for executing SQL commands in an SQLite database.

This tool provides an interface for interacting with SQLite databases, including
executing queries, managing schema, and handling table operations. It supports
both read-only and write operations based on configuration.

**Attributes**:

- `description` _Text_ - A description of what the SQL tool does.
- `database` _Text_ - The database URI or path.
- `schema` _Text_ - The database schema containing table definitions.
- `tables` _Optional[Union[List[Text], Text]]_ - List of table names that can be
  accessed by this tool. If None, all tables are accessible.
- `enable_commit` _bool_ - Whether write operations (INSERT, UPDATE, DELETE) are
  allowed. If False, only read operations are permitted.
- `status` _AssetStatus_ - The current status of the tool (DRAFT or ONBOARDED).

#### \_\_init\_\_

```python
def __init__(name: Text,
             description: Text,
             database: Text,
             schema: Optional[Text] = None,
             tables: Optional[Union[List[Text], Text]] = None,
             enable_commit: bool = False,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L361)

Initialize a new SQLTool instance.

**Arguments**:

- `name` _Text_ - The name of the tool.
- `description` _Text_ - A description of what the SQL tool does.
- `database` _Text_ - The database URI or path. Can be a local file path,
  S3 URI, or HTTP(S) URL.
- `schema` _Optional[Text], optional_ - The database schema containing table
  definitions. If not provided, will be inferred from the database.
  Defaults to None.
- `tables` _Optional[Union[List[Text], Text]], optional_ - List of table names
  that can be accessed by this tool. If not provided, all tables are
  accessible. Defaults to None.
- `enable_commit` _bool, optional_ - Whether write operations are allowed.
  If False, only read operations are permitted. Defaults to False.
- `**additional_info` - Additional keyword arguments for tool configuration.
  

**Raises**:

- `SQLToolError` - If required parameters are missing or invalid.

#### to\_dict

```python
def to_dict() -> Dict[str, Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L400)

Convert the tool instance to a dictionary representation.

**Returns**:

  Dict[str, Text]: A dictionary containing the tool&#x27;s configuration with keys:
  - name: The tool&#x27;s name
  - description: The tool&#x27;s description
  - parameters: List of parameter dictionaries containing:
  - database: The database URI or path
  - schema: The database schema
  - tables: Comma-separated list of table names or None
  - enable_commit: Whether write operations are allowed
  - type: Always &quot;sql&quot;

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L426)

Validate the SQL tool&#x27;s configuration.

This method performs several checks:
1. Verifies required fields (description, database) are provided
2. Validates database path/URI format
3. Infers schema from database if not provided
4. Sets table list from schema if not provided
5. Uploads local database file to storage

**Raises**:

- `SQLToolError` - If any validation check fails or if there are issues with
  database access or file operations.

#### deploy

```python
def deploy() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/tool/sql_tool.py#L478)

Deploy the SQL tool by downloading and preparing the database.

This method handles the deployment process:
1. For HTTP(S) URLs: Downloads the database file
2. Creates a unique local filename
3. Uploads the database to the aiXplain platform
4. Cleans up temporary files

**Raises**:

- `requests.exceptions.RequestException` - If downloading the database fails.
- `Exception` - If there are issues with file operations or uploads.

