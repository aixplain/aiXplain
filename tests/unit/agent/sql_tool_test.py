import os
import pytest
import pandas as pd
from aixplain.factories import AgentFactory, FileFactory
from aixplain.enums import DatabaseSourceType

from aixplain.modules.agent.tool.sql_tool import (
    SQLTool,
    create_database_from_csv,
    get_table_schema,
    SQLToolError,
    CSVError,
    DatabaseError,
    clean_column_name,
)


def test_clean_column_name():
    # Test basic cleaning
    assert clean_column_name("test name") == "test_name"
    assert clean_column_name("test(name)") == "test_name"
    assert clean_column_name("test/name") == "test_name"
    assert clean_column_name("test__name") == "test_name"
    assert clean_column_name(" test name ") == "test_name"

    # Test Case-insensitive
    assert clean_column_name("Test Name") == "test_name"
    assert clean_column_name("TEST NAME") == "test_name"
    assert clean_column_name("TEST-NAME") == "test_name"

    # Test number prefix
    assert clean_column_name("1test") == "col_1test"

    # Test special characters
    assert clean_column_name("test@#$%^&*()name") == "test_name"
    assert clean_column_name("test!!!name") == "test_name"

    # Test multiple underscores
    assert clean_column_name("test___name") == "test_name"

    # Test leading/trailing special chars
    assert clean_column_name("_test_name_") == "test_name"
    assert clean_column_name("___test___name___") == "test_name"


def test_create_sql_tool(mocker, tmp_path):
    # Create a test database file
    # Create a test database file
    db_path = os.path.join(tmp_path, "test.db")
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.close()

    mocker.patch.object(FileFactory, "upload", return_value="s3://test.db")

    # Test SQLite source type
    tool = AgentFactory.create_sql_tool(
        name="Test SQL", description="Test", source=db_path, source_type="sqlite", schema="test", tables=["test", "test2"]
    )
    assert isinstance(tool, SQLTool)
    assert tool.description == "Test"
    assert os.path.basename(db_path) in os.path.basename(tool.database)
    assert tool.database.startswith("s3://")
    assert tool.database.endswith(".db")
    assert tool.schema == "test"
    assert tool.tables == ["test", "test2"]

    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"]})
    df.to_csv(csv_path, index=False)
    # Test CSV source type
    csv_tool = AgentFactory.create_sql_tool(
        name="Test CSV", description="Test CSV", source=csv_path, source_type="csv", tables=["data"]
    )
    assert isinstance(csv_tool, SQLTool)
    assert csv_tool.description == "Test CSV"
    assert csv_tool.database.endswith(".db")

    # Test to_dict() method
    tool_dict = tool.to_dict()
    assert tool_dict["description"] == "Test"
    assert tool_dict["parameters"] == [
        {"name": "database", "value": tool.database},
        {"name": "schema", "value": "test"},
        {"name": "tables", "value": "test,test2"},
        {"name": "enable_commit", "value": False},
    ]

    # Test validation and file upload
    mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("aixplain.modules.agent.tool.sql_tool.get_table_schema", return_value="CREATE TABLE test (id INTEGER)")
    tool.validate()
    assert tool.database.startswith("s3://")
    assert tool.database.endswith(".db")


def test_create_database_from_csv(tmp_path):
    # Create a temporary CSV file
    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"], "value": [1.1, 2.2, 3.3]})
    df.to_csv(csv_path, index=False)

    # Create database from CSV
    db_path = os.path.join(tmp_path, "test.db")
    try:
        schema = create_database_from_csv(csv_path, db_path)

        # Verify results
        assert "CREATE TABLE test" in schema
        assert '"id" INTEGER' in schema
        assert '"name" TEXT' in schema
        assert '"value" REAL' in schema
        assert os.path.exists(db_path)

        # Test get_table_schema
        retrieved_schema = get_table_schema(db_path)
        assert retrieved_schema == schema
    finally:
        # Clean up the database file
        if os.path.exists(db_path):
            os.remove(db_path)


def test_create_database_from_csv_errors(tmp_path):
    # Test non-existent CSV file
    with pytest.raises(CSVError, match="CSV file .* does not exist"):
        create_database_from_csv("nonexistent.csv", "test.db")

    # Test invalid file extension
    invalid_ext = os.path.join(tmp_path, "test.txt")
    open(invalid_ext, "w").close()
    with pytest.raises(CSVError, match="File .* is not a CSV file"):
        create_database_from_csv(invalid_ext, "test.db")

    # Test empty CSV file
    empty_csv = os.path.join(tmp_path, "empty.csv")
    open(empty_csv, "w").close()
    with pytest.raises(CSVError, match="CSV file .* is empty"):
        create_database_from_csv(empty_csv, "test.db")

    # Test empty CSV file
    dup_cols_empty_csv = os.path.join(tmp_path, "dup_cols_empty.csv")
    with open(dup_cols_empty_csv, "w") as f:
        f.write("id,id\n")  # Only header with duplicate columns, no data
    with pytest.raises(CSVError, match="CSV file .* is empty"):
        create_database_from_csv(dup_cols_empty_csv, "test.db")


def test_get_table_schema_errors(tmp_path):
    # Test non-existent database
    with pytest.raises(DatabaseError, match="Database file .* does not exist"):
        get_table_schema("nonexistent.db")


def test_sql_tool_validation_errors(tmp_path):
    # Create a test database file
    db_path = os.path.join(tmp_path, "test.db")
    # creat a proper sqlite database
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.close()

    # Test missing description
    with pytest.raises(SQLToolError, match="Description is required"):
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="", source=db_path, source_type="sqlite")
        tool.validate()

    # Test missing source
    with pytest.raises(SQLToolError, match="Source must be provided"):
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source="", source_type="sqlite")
        tool.validate()

    # Test missing source_type
    with pytest.raises(TypeError, match="missing 1 required positional argument: 'source_type'"):
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source=db_path)
        tool.validate()

    # Test invalid source type
    with pytest.raises(SQLToolError, match="Invalid source type"):
        AgentFactory.create_sql_tool(name="Test SQL", description="Test", source=db_path, source_type="invalid")

    # Test non-existent SQLite database
    with pytest.raises(SQLToolError, match="Database .* does not exist"):
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source="nonexistent.db", source_type="sqlite")
        tool.validate()

    # Test non-existent CSV file
    with pytest.raises(SQLToolError, match="CSV file .* does not exist"):
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source="nonexistent.csv", source_type="csv")
        tool.validate()

    # Test PostgreSQL (not supported)
    with pytest.raises(SQLToolError, match="PostgreSQL is not supported yet"):
        tool = AgentFactory.create_sql_tool(
            name="Test SQL",
            description="Test",
            source="postgresql://user:pass@localhost/mydb",
            source_type="postgresql",
            schema="public",
            tables=["users"],
        )
        tool.validate()


def test_create_sql_tool_with_schema_inference(tmp_path, mocker):
    # Create a test database file
    db_path = os.path.join(tmp_path, "test.db")
    # creat a proper sqlite database
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.close()

    mocker.patch.object(FileFactory, "upload", return_value=db_path)

    # Create tool without schema and tables
    tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source=db_path, source_type="sqlite")

    # Mock schema inference
    schema = "CREATE TABLE test (id INTEGER, name TEXT)"
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("aixplain.modules.agent.tool.sql_tool.get_table_schema", return_value=schema)
    mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")

    # Validate and check schema/tables inference
    tool.validate()
    assert tool.schema == schema
    assert tool.tables == ["test"]
    assert tool.database.startswith("s3://")
    assert tool.database.endswith(".db")


def test_create_sql_tool_from_csv_with_warnings(tmp_path, mocker):
    # Create a CSV with column names that need cleaning
    csv_path = os.path.join(tmp_path, "test with spaces.csv")
    df = pd.DataFrame(
        {
            "1id": [1, 2],  # Should be prefixed with col_
            "test name": ["test1", "test2"],  # Should replace space with underscore
            "value(%)": [1.1, 2.2],  # Should remove special characters
        }
    )
    df.to_csv(csv_path, index=False)

    # Create tool and check for warnings
    with pytest.warns(UserWarning) as record:
        tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source=csv_path, source_type="csv")

    # Verify warnings about column name changes
    warning_messages = [str(w.message) for w in record]
    column_changes_warning = next(
        (msg for msg in warning_messages if "Column names were cleaned for SQLite compatibility" in msg), None
    )
    assert column_changes_warning is not None
    assert "'1id' to 'col_1id'" in column_changes_warning
    assert "'test name' to 'test_name'" in column_changes_warning
    assert "'value(%)' to 'value'" in column_changes_warning

    try:
        # Mock file upload for validation
        mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")

        # Validate and verify schema
        tool.validate()
        assert "col_1id" in tool.schema
        assert "test_name" in tool.schema
        assert "value" in tool.schema
        assert tool.tables == ["test_with_spaces"]
    finally:
        # Clean up the database file
        if os.path.exists(tool.database):
            os.remove(tool.database)


def test_create_sql_tool_from_csv(tmp_path, mocker):
    # Create a temporary CSV file
    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"], "value": [1.1, 2.2, 3.3]})
    df.to_csv(csv_path, index=False)

    with open("test.db", "w") as f:
        f.write("")

    mocker.patch.object(FileFactory, "upload", return_value="s3://test.db")

    # Test successful creation
    tool = AgentFactory.create_sql_tool(
        name="Test SQL", description="Test", source=csv_path, source_type="csv", tables=["test"]
    )
    assert isinstance(tool, SQLTool)
    assert tool.description == "Test"
    assert tool.database.endswith(".db")
    assert tool.database.startswith("s3://")

    # Test schema and table inference during validation
    try:
        tool.validate()
        assert "CREATE TABLE test" in tool.schema
        assert '"id" INTEGER' in tool.schema
        assert '"name" TEXT' in tool.schema
        assert '"value" REAL' in tool.schema
        assert tool.tables == ["test"]
    finally:
        # Clean up the database file
        if os.path.exists(tool.database):
            os.remove(tool.database)
        if os.path.exists("test.db"):
            os.remove("test.db")


def test_sql_tool_schema_inference(tmp_path):
    # Create a temporary CSV file
    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"]})
    df.to_csv(csv_path, index=False)

    # Create tool without schema and tables
    tool = AgentFactory.create_sql_tool(name="Test SQL", description="Test", source=csv_path, source_type="csv")

    try:
        tool.validate()
        assert tool.schema is not None
        assert "CREATE TABLE test" in tool.schema
        assert tool.tables == ["test"]
    finally:
        # Clean up the database file
        if os.path.exists(tool.database):
            os.remove(tool.database)


def test_create_sql_tool_source_type_handling(tmp_path):
    # Create a test database file
    db_path = os.path.join(tmp_path, "test.db")
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.close()

    # Test with string input
    tool_str = AgentFactory.create_sql_tool(
        name="Test SQL", description="Test", source=db_path, source_type="sqlite", schema="test"
    )
    assert isinstance(tool_str, SQLTool)

    # Test with enum input
    tool_enum = AgentFactory.create_sql_tool(
        name="Test SQL", description="Test", source=db_path, source_type=DatabaseSourceType.SQLITE, schema="test"
    )
    assert isinstance(tool_enum, SQLTool)

    # Test invalid type
    with pytest.raises(SQLToolError, match="Source type must be either a string or DatabaseSourceType enum, got <class 'int'>"):
        AgentFactory.create_sql_tool(
            name="Test SQL", description="Test", source=db_path, source_type=123, schema="test"
        )  # Invalid type
