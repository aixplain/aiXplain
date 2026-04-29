import os
import pytest
import pandas as pd
from aixplain.factories import AgentFactory
from aixplain.enums import DatabaseSourceType
from aixplain.modules.agent.tool.sql_tool import SQLTool, SQLToolError


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
        )
