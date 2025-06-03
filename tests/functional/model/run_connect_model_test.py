import os
from aixplain.enums import ResponseStatus
from aixplain.factories import ModelFactory
from aixplain.modules.model.integration import Integration, AuthenticationSchema
from aixplain.modules.model.connection import ConnectionTool


def test_run_connect_model():
    # get slack connector
    connector = ModelFactory.get("67eff5c0e05614297caeef98")

    assert isinstance(connector, Integration)
    assert connector.id == "67eff5c0e05614297caeef98"
    assert connector.name == "Slack"

    response = connector.connect(authentication_schema=AuthenticationSchema.BEARER, token=os.getenv("SLACK_TOKEN"))
    assert response.status == ResponseStatus.SUCCESS
    assert "id" in response.data
    connection_id = response.data["id"]
    # get slack connection
    connection = ModelFactory.get(connection_id)
    assert isinstance(connection, ConnectionTool)
    assert connection.id == connection_id
    assert connection.actions is not None

    action = [action for action in connection.actions if action.code == "SLACK_CHAT_POST_MESSAGE"]
    assert len(action) > 0
    action = action[0]
    response = connection.run(action, {"text": "This is a test!", "channel": "C084G435LR5"})
    assert response.status == ResponseStatus.SUCCESS
