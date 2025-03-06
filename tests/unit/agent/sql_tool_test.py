import os
import pytest
import pandas as pd
from aixplain.factories import AgentFactory
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


def test_create_sql_tool(mocker):
    tool = AgentFactory.create_sql_tool(description="Test", database="test.db", schema="test", tables=["test", "test2"])
    assert isinstance(tool, SQLTool)
    assert tool.description == "Test"
    assert tool.database == "test.db"
    assert tool.schema == "test"
    assert tool.tables == ["test", "test2"]

    tool_dict = tool.to_dict()
    assert tool_dict["description"] == "Test"
    assert tool_dict["parameters"] == [
        {"name": "database", "value": "test.db"},
        {"name": "schema", "value": "test"},
        {"name": "tables", "value": "test,test2"},
        {"name": "enable_commit", "value": False},
    ]

    mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("aixplain.modules.agent.tool.sql_tool.get_table_schema", return_value="CREATE TABLE test (id INTEGER)")
    tool.validate()
    assert tool.database == "s3://test.db"


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


def test_sql_tool_validation_errors():
    # Test missing description
    with pytest.raises(SQLToolError, match="Description is required"):
        tool = AgentFactory.create_sql_tool(description="", database="test.db")
        tool.validate()

    # Test missing database
    with pytest.raises(SQLToolError, match="Database must be provided"):
        tool = AgentFactory.create_sql_tool(description="Test", database="")
        tool.validate()

    # Test non-existent database
    with pytest.raises(SQLToolError, match="Database .* does not exist"):
        tool = AgentFactory.create_sql_tool(description="Test", database="nonexistent.db")
        tool.validate()


def test_create_sql_tool_with_schema_inference(tmp_path, mocker):
    # Create a test database file
    db_path = os.path.join(tmp_path, "test.db")
    with open(db_path, "w") as f:
        f.write("dummy db")  # Just to create the file

    # Create tool without schema and tables
    tool = AgentFactory.create_sql_tool(description="Test", database=db_path)
    assert tool.schema is None
    assert tool.tables is None

    # Mock schema inference
    schema = "CREATE TABLE test (id INTEGER, name TEXT)"
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("aixplain.modules.agent.tool.sql_tool.get_table_schema", return_value=schema)
    mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")

    # Validate and check schema/tables inference
    tool.validate()
    assert tool.schema == schema
    assert tool.tables == ["test"]
    assert tool.database == "s3://test.db"


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
        tool = AgentFactory.create_sql_tool_from_csv(description="Test", csv_path=csv_path)

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


def test_create_sql_tool_from_csv(tmp_path):
    # Create a temporary CSV file
    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"], "value": [1.1, 2.2, 3.3]})
    df.to_csv(csv_path, index=False)

    # Test non-existent CSV file
    with pytest.raises(SQLToolError, match="CSV file .* does not exist"):
        AgentFactory.create_sql_tool_from_csv(description="Test", csv_path="nonexistent.csv")

    # Test invalid file extension
    invalid_path = os.path.join(tmp_path, "test.txt")
    with open(invalid_path, "w") as f:
        f.write("test")
    with pytest.raises(SQLToolError, match="File .* is not a CSV file"):
        AgentFactory.create_sql_tool_from_csv(description="Test", csv_path=invalid_path)

    # Test successful creation
    tool = AgentFactory.create_sql_tool_from_csv(description="Test", csv_path=csv_path)
    assert isinstance(tool, SQLTool)
    assert tool.description == "Test"
    assert tool.database.endswith("test.db")
    assert os.path.exists(tool.database)

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


def test_sql_tool_schema_inference(tmp_path):
    # Create a temporary CSV file
    csv_path = os.path.join(tmp_path, "test.csv")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["test1", "test2", "test3"]})
    df.to_csv(csv_path, index=False)

    # Create tool without schema and tables
    tool = AgentFactory.create_sql_tool_from_csv(description="Test", csv_path=csv_path)

    try:
        assert tool.schema is not None
        assert "CREATE TABLE test" in tool.schema
        assert tool.tables == ["test"]
    finally:
        # Clean up the database file
        if os.path.exists(tool.database):
            os.remove(tool.database)
