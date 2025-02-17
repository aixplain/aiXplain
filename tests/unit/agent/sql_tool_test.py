from aixplain.factories import AgentFactory
from aixplain.modules.agent.tool.sql_tool import SQLTool


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
    tool.validate()
    assert tool.database == "s3://test.db"
