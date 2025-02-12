from aixplain.factories import AgentFactory
from aixplain.modules.agent.tool.sql_tool import SQLTool


def test_create_sql_tool(mocker):
    tool = AgentFactory.create_sql_tool(description="Test", database="test.db", schema="test", table="test")
    assert isinstance(tool, SQLTool)
    assert tool.description == "Test"
    assert tool.database == "test.db"
    assert tool.schema == "test"
    assert tool.table == "test"

    tool_dict = tool.to_dict()
    assert tool_dict["description"] == "Test"
    assert tool_dict["parameters"] == [
        {"name": "database", "value": "test.db"},
        {"name": "schema", "value": "test"},
        {"name": "table", "value": "test"},
    ]

    mocker.patch("aixplain.factories.file_factory.FileFactory.upload", return_value="s3://test.db")
    mocker.patch("os.path.exists", return_value=True)
    tool.validate()
    assert tool.database == "s3://test.db"
