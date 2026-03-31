"""Unit tests for the v2 Tool update and integration resolution logic."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from aixplain.v2.tool import Tool, ToolResult
from aixplain.v2.integration import Integration
from aixplain.v2.resource import ResourceError

MOCK_BACKEND_RESPONSE = {
    "id": "69bbf9c19e1085b478304903",
    "name": "Slack Tool (1773926848)",
    "serviceName": None,
    "status": "onboarded",
    "host": "Composio",
    "developer": "aixplain",
    "description": "Slack channel-based messaging platform.\n\n Authentication scheme used for this connections: BEARER_TOKEN",
    "vendor": {"id": 1, "name": "aiXplain", "code": "aixplain"},
    "supplier": {"id": 1, "name": "aiXplain", "code": "aixplain"},
    "connectionType": ["synchronous"],
    "function": {"id": "utilities", "name": "Utilites"},
    "pricing": {"price": 0.00001, "unitType": "REQUEST", "unitTypeScale": "SECOND"},
    "version": {"name": None, "id": "slack"},
    "functionType": "connection",
    "type": "regular",
    "createdAt": "2026-03-19T13:27:29.604Z",
    "updatedAt": "2026-03-19T13:27:29.604Z",
    "supportsStreaming": None,
    "supportsBYOC": None,
    "attributes": {
        "auth_schemes": '["OAUTH2","BEARER_TOKEN"]',
        "BEARER_TOKEN-inputs": '[{"name":"token","displayName":"Bearer Token","type":"string","description":"Token for bearer authentication","required":true}]',
        "OAUTH2-inputs": "[]",
    },
    "parentModelId": "686432941223092cb4294d3f",
    "params": [
        {
            "name": "action",
            "required": True,
            "isFixed": False,
            "values": [],
            "defaultValues": [],
            "availableOptions": [],
            "dataType": "text",
            "dataSubType": "text",
            "multipleValues": False,
        },
        {
            "name": "data",
            "required": True,
            "isFixed": False,
            "values": [],
            "defaultValues": [],
            "availableOptions": [],
            "dataType": "text",
            "dataSubType": "json",
            "multipleValues": False,
        },
    ],
}


def _make_fetched_tool(response=None, context=None):
    """Simulate a tool as returned by Tool.get() (deserialized from backend)."""
    data = dict(response or MOCK_BACKEND_RESPONSE)
    tool = Tool.from_dict(data)
    tool.context = context or Mock()
    tool._update_saved_state()
    return tool


def _make_connection_tool(context=None):
    """Create a minimal tool object returned by integration.connect()."""
    connection = Mock()
    connection.id = "69bbf9c19e1085b478304903"
    connection.name = "Slack Tool (1773926848)"
    connection.redirect_url = None
    for attr_name in Tool.__dataclass_fields__:
        setattr(connection, attr_name, None)
    connection.id = "69bbf9c19e1085b478304903"
    connection.name = "Slack Tool (1773926848)"
    return connection


# =============================================================================
# integration_id deserialization (maps to backend parentModelId)
# =============================================================================


class TestIntegrationIdDeserialization:
    """Tests for parentModelId → integration_id field mapping."""

    def test_integration_id_deserialized_from_backend(self):
        """parentModelId in the response should map to integration_id."""
        tool = _make_fetched_tool()
        assert tool.integration_id == "686432941223092cb4294d3f"

    def test_integration_id_none_when_absent(self):
        """Older tools without parentModelId should have integration_id=None."""
        data = dict(MOCK_BACKEND_RESPONSE)
        del data["parentModelId"]
        tool = _make_fetched_tool(response=data)
        assert tool.integration_id is None

    def test_integration_id_serialized_as_camel_case(self):
        """integration_id should serialize back as parentModelId."""
        tool = _make_fetched_tool()
        d = tool.to_dict()
        assert "parentModelId" in d
        assert d["parentModelId"] == "686432941223092cb4294d3f"

    def test_integration_id_setter(self):
        tool = _make_fetched_tool()
        tool.integration_id = "new-integration-id"
        assert tool.integration_id == "new-integration-id"


class TestIntegrationPathProperty:
    """Tests for integration_path property."""

    def test_integration_path_returns_path_when_resolved(self):
        tool = _make_fetched_tool()
        mock_integration = Mock(spec=Integration)
        mock_integration.path = "aixplain/python-sandbox/aixplain"
        tool.integration = mock_integration
        assert tool.integration_path == "aixplain/python-sandbox/aixplain"

    def test_integration_path_none_when_not_resolved(self):
        tool = _make_fetched_tool()
        assert tool.integration is None
        assert tool.integration_path is None

    def test_integration_path_none_when_string(self):
        tool = _make_fetched_tool()
        tool.integration = "686432941223092cb4294d3f"
        assert tool.integration_path is None

    def test_integration_path_none_when_integration_has_no_path(self):
        tool = _make_fetched_tool()
        mock_integration = Mock(spec=Integration)
        mock_integration.path = None
        tool.integration = mock_integration
        assert tool.integration_path is None


# =============================================================================
# _resolve_integration
# =============================================================================


class TestResolveIntegration:
    """Tests for _resolve_integration auto-resolution logic."""

    def test_resolve_skips_when_integration_already_set(self):
        """Should return immediately when integration is already set."""
        tool = _make_fetched_tool()
        tool.integration = "already-set-id"

        tool._resolve_integration()

        assert tool.integration == "already-set-id"

    def test_resolve_uses_integration_id(self):
        """Should set integration from integration_id when available."""
        tool = _make_fetched_tool()
        assert tool.integration is None

        tool._resolve_integration()

        assert tool.integration == "686432941223092cb4294d3f"

    def test_resolve_raises_when_no_integration_id(self):
        """Should raise ValueError when integration_id is None (older tool)."""
        data = dict(MOCK_BACKEND_RESPONSE)
        del data["parentModelId"]
        tool = _make_fetched_tool(response=data)

        with pytest.raises(ValueError, match="integration_id is not set"):
            tool._resolve_integration()

    def test_resolve_is_idempotent(self):
        """Calling _resolve_integration twice should be safe."""
        tool = _make_fetched_tool()

        tool._resolve_integration()
        first_value = tool.integration

        tool._resolve_integration()
        assert tool.integration == first_value


# =============================================================================
# _update
# =============================================================================


class TestToolUpdate:
    """Tests for _update: metadata via PUT + optional reconnect."""

    def _setup_mocks(self, tool):
        """Set up mocks for both the PUT call and integration.connect."""
        mock_integration = Mock(spec=Integration)
        mock_connection = _make_connection_tool()
        mock_integration.connect = Mock(return_value=mock_connection)

        mock_context = Mock()
        mock_context.Integration.get = Mock(return_value=mock_integration)
        mock_context.client.request = Mock(return_value={"id": tool.id})
        tool.context = mock_context
        return mock_integration, mock_connection

    def test_update_sends_metadata_via_put(self):
        """_update should PUT name and description to sdk/utilities/{id}."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.name = "Updated Name"

        tool._update("v2/tools", {})

        tool.context.client.request.assert_called_once()
        call_args = tool.context.client.request.call_args
        assert call_args[0] == ("put", f"sdk/utilities/{tool.id}")
        put_payload = call_args[1]["json"]
        assert put_payload["name"] == "Updated Name"
        assert put_payload["id"] == tool.id

    def test_update_metadata_only_does_not_reconnect(self):
        """When only name/description change, connect should NOT be called."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.name = "Just a Name Change"

        tool._update("v2/tools", {})

        mock_integration.connect.assert_not_called()

    def test_update_with_config_triggers_reconnect(self):
        """When config is set, connect should be called with assetId."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"code": "print('hello')", "function_name": "greet"}

        tool._update("v2/tools", {})

        mock_integration.connect.assert_called_once()
        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["data"]["code"] == "print('hello')"
        assert call_kwargs["data"]["function_name"] == "greet"
        assert call_kwargs["data"]["assetId"] == tool.id

    def test_update_with_code_triggers_reconnect(self):
        """When code is set, connect should be called."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.code = "def add(a, b): return a + b"

        tool._update("v2/tools", {})

        mock_integration.connect.assert_called_once()
        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["data"]["code"] == "def add(a, b): return a + b"

    def test_update_reconnect_resolves_integration(self):
        """Reconnect path should auto-resolve integration via integration_id."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        tool.context.Integration.get.assert_called_once_with("686432941223092cb4294d3f")

    def test_update_reconnect_uses_asset_id_fallback(self):
        """When asset_id is None, should use self.id as assetId."""
        tool = _make_fetched_tool()
        assert tool.asset_id is None
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["data"]["assetId"] == tool.id

    def test_update_reconnect_prefers_asset_id(self):
        """When asset_id is set, should use it instead of self.id."""
        tool = _make_fetched_tool()
        tool.asset_id = "explicit-asset-id"
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["data"]["assetId"] == "explicit-asset-id"

    def test_update_reconnect_refreshes_id(self):
        """Reconnect should set self.id from the returned connection."""
        tool = _make_fetched_tool()
        mock_integration, mock_connection = self._setup_mocks(tool)
        mock_connection.id = "new-id-after-reconnect"
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        assert tool.id == "new-id-after-reconnect"

    def test_update_reconnect_does_not_overwrite_existing_fields(self):
        """Conservative field refresh should not overwrite user-set values."""
        tool = _make_fetched_tool()
        mock_integration, mock_connection = self._setup_mocks(tool)
        tool.allowed_actions = ["SLACK_SENDS_A_MESSAGE_IN_A_CHANNEL"]
        mock_connection.allowed_actions = []
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        assert tool.allowed_actions == ["SLACK_SENDS_A_MESSAGE_IN_A_CHANNEL"]

    def test_update_reconnect_sets_redirect_url(self):
        """Should propagate redirect_url from the returned connection."""
        tool = _make_fetched_tool()
        mock_integration, mock_connection = self._setup_mocks(tool)
        mock_connection.redirect_url = "https://oauth.example.com/callback"
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        assert tool.redirect_url == "https://oauth.example.com/callback"

    def test_update_reconnect_sends_empty_name(self):
        """Reconnect should send empty name to avoid 'Name already exists' error."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.name = "My Tool Name"
        tool.config = {"code": "print('hi')"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["name"] == ""

    def test_update_reconnect_omits_description(self):
        """Reconnect should not include description (metadata PUT handles it)."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.description = "Updated description"
        tool.config = {"code": "print('hi')"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert "description" not in call_kwargs

    def test_update_reconnect_clears_config_and_code(self):
        """After a successful reconnect, config and code should be cleared."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"code": "print('hi')", "function_name": "greet"}
        tool.code = "def greet(): pass"

        tool._update("v2/tools", {})

        assert tool.config is None
        assert tool.code is None


# =============================================================================
# _create clears transient fields
# =============================================================================


class TestToolCreate:
    """Tests that _create clears config/code after success."""

    def test_create_clears_config_after_success(self):
        """After successful creation, config should be cleared to prevent false reconnects."""
        mock_connection = _make_connection_tool()
        mock_integration = Mock(spec=Integration)
        mock_integration.connect = Mock(return_value=mock_connection)

        tool = _make_fetched_tool()
        tool.id = None
        tool.integration_id = None
        tool.name = "test-tool"
        tool.description = "desc"
        tool.config = {"code": "def add(): pass", "function_name": "add"}
        tool.code = None
        tool.integration = mock_integration

        tool._create("v2/tools", {})

        assert tool.config is None
        assert tool.code is None
        assert tool.id == mock_connection.id


# =============================================================================
# save() integration (update path)
# =============================================================================


class TestToolSaveUpdate:
    """Tests for save() triggering _update when tool has an id."""

    def test_save_calls_put_when_id_present(self):
        """save() should PUT metadata when self.id is set."""
        tool = _make_fetched_tool()
        tool.context = Mock()
        tool.context.client.request = Mock(return_value={"id": tool.id})

        tool.name = "Renamed Tool"
        tool.save()

        tool.context.client.request.assert_called_once()
        call_args = tool.context.client.request.call_args
        assert call_args[0][0] == "put"
        assert "sdk/utilities/" in call_args[0][1]
        assert call_args[1]["json"]["name"] == "Renamed Tool"

    def test_save_name_only_does_not_reconnect(self):
        """Changing just the name should PUT metadata without reconnecting."""
        tool = _make_fetched_tool()
        tool.context = Mock()
        tool.context.client.request = Mock(return_value={"id": tool.id})

        tool.name = "Just The Name"
        tool.save()

        tool.context.client.request.assert_called_once()
        put_payload = tool.context.client.request.call_args[1]["json"]
        assert put_payload["name"] == "Just The Name"


# =============================================================================
# _extract_auth_scheme
# =============================================================================


class TestExtractAuthScheme:
    """Tests for _extract_auth_scheme helper."""

    def test_extracts_bearer_token_from_description(self):
        tool = _make_fetched_tool()
        assert tool._extract_auth_scheme() == "BEARER_TOKEN"

    def test_extracts_oauth2_from_description(self):
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = "Some tool.\n\n Authentication scheme used for this connections: OAUTH2"
        tool = _make_fetched_tool(response=data)
        assert tool._extract_auth_scheme() == "OAUTH2"

    def test_returns_none_when_description_has_no_scheme(self):
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = "A plain description with no auth info."
        data["attributes"] = {}
        tool = _make_fetched_tool(response=data)
        assert tool._extract_auth_scheme() is None

    def test_falls_back_to_attributes_when_description_missing(self):
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = "No auth info here."
        tool = _make_fetched_tool(response=data)
        assert tool._extract_auth_scheme() == "BEARER_TOKEN"

    def test_returns_none_for_empty_description_and_no_attributes(self):
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = None
        data["attributes"] = None
        tool = _make_fetched_tool(response=data)
        assert tool._extract_auth_scheme() is None


# =============================================================================
# _update sends authScheme
# =============================================================================


class TestUpdateSendsAuthScheme:
    """Tests that reconnect includes authScheme in the connect payload."""

    def _setup_mocks(self, tool):
        mock_integration = Mock(spec=Integration)
        mock_connection = _make_connection_tool()
        mock_integration.connect = Mock(return_value=mock_connection)
        mock_context = Mock()
        mock_context.Integration.get = Mock(return_value=mock_integration)
        mock_context.client.request = Mock(return_value={"id": tool.id})
        tool.context = mock_context
        return mock_integration, mock_connection

    def test_reconnect_sends_auth_scheme_from_description(self):
        """Reconnect should include authScheme extracted from the description."""
        tool = _make_fetched_tool()
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["authScheme"] == "BEARER_TOKEN"

    def test_reconnect_omits_auth_scheme_when_not_extractable(self):
        """Reconnect should not include authScheme when it can't be extracted."""
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = "No auth info."
        data["attributes"] = {}
        tool = _make_fetched_tool(response=data)
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert "authScheme" not in call_kwargs

    def test_reconnect_sends_oauth2_when_tool_uses_oauth(self):
        """Reconnect should send OAUTH2 authScheme for OAuth tools."""
        data = dict(MOCK_BACKEND_RESPONSE)
        data["description"] = "Tool description.\n\n Authentication scheme used for this connections: OAUTH2"
        tool = _make_fetched_tool(response=data)
        mock_integration, _ = self._setup_mocks(tool)
        tool.config = {"token": "xyz"}

        tool._update("v2/tools", {})

        call_kwargs = mock_integration.connect.call_args[1]
        assert call_kwargs["authScheme"] == "OAUTH2"
