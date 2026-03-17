"""Unit tests for the v2 Session module.

This module tests Session, SessionMessage, and SessionMessageAttachment
dataclasses, serialization, CRUD operations, and the MIME-to-AttachmentType
mapping — all with mocked HTTP calls.
"""

from unittest.mock import Mock, patch, call

import pytest

from aixplain.v2.session import (
    Session,
    SessionMessage,
    SessionMessageAttachment,
    _mime_to_attachment_type,
)
from aixplain.v2.enums import (
    SessionStatus,
    RunStatus,
    MessageRole,
    Reaction,
    AttachmentType,
)
from aixplain.v2.agent import Agent
from aixplain.v2.exceptions import ValidationError, APIError, ResourceError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_context(**overrides):
    """Create a mock Aixplain context with a mock client."""
    client = Mock()
    ctx = Mock(
        client=client,
        backend_url="https://platform-api.aixplain.com",
        api_key="test_key",
    )
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def _bound_session_class(ctx=None):
    """Return a Session subclass bound to a mock context."""
    ctx = ctx or _make_mock_context()

    class BoundSession(Session):
        context = ctx

    return BoundSession


def _bound_agent_class(ctx=None):
    """Return an Agent subclass bound to a mock context."""
    ctx = ctx or _make_mock_context()

    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


# Sample API payloads ---------------------------------------------------

SAMPLE_SESSION_DICT = {
    "id": "sess_001",
    "userId": "user_42",
    "agentId": "agent_99",
    "name": "My Session",
    "status": "active",
    "runStatus": "idle",
    "messageCount": 3,
    "lastMessagePreview": "Hello there",
    "lastMessageAt": "2025-06-01T12:00:00Z",
    "createdAt": "2025-06-01T10:00:00Z",
    "updatedAt": "2025-06-01T12:00:00Z",
}

SAMPLE_MESSAGE_DICT = {
    "id": "msg_001",
    "sessionId": "sess_001",
    "userId": "user_42",
    "agentId": "agent_99",
    "role": "user",
    "content": "Hello!",
    "sequence": 1,
    "requestId": "req_001",
    "reaction": None,
    "attachments": None,
    "createdAt": "2025-06-01T10:01:00Z",
}


# =========================================================================
# Enum tests
# =========================================================================


class TestSessionEnums:
    """Verify new enums have expected members and values."""

    def test_session_status_values(self):
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.FAILED == "failed"
        assert SessionStatus.ARCHIVED == "archived"

    def test_run_status_values(self):
        assert RunStatus.IDLE == "idle"
        assert RunStatus.RUNNING == "running"
        assert RunStatus.COMPLETED == "completed"

    def test_message_role_values(self):
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"

    def test_reaction_values(self):
        assert Reaction.LIKE == "LIKE"
        assert Reaction.DISLIKE == "DISLIKE"

    def test_attachment_type_values(self):
        assert AttachmentType.TEXT == "text"
        assert AttachmentType.IMAGE == "image"
        assert AttachmentType.VIDEO == "video"
        assert AttachmentType.AUDIO == "audio"
        assert AttachmentType.DOCUMENT == "document"
        assert AttachmentType.CODE == "code"
        assert AttachmentType.UNKNOWN == "unknown"


# =========================================================================
# MIME type mapping
# =========================================================================


class TestMimeToAttachmentType:
    """Tests for the _mime_to_attachment_type helper."""

    @pytest.mark.parametrize(
        "mime, expected",
        [
            ("image/png", "image"),
            ("image/jpeg", "image"),
            ("video/mp4", "video"),
            ("audio/mpeg", "audio"),
            ("audio/wav", "audio"),
            ("text/plain", "text"),
            ("text/csv", "text"),
        ],
    )
    def test_main_type_mapping(self, mime, expected):
        assert _mime_to_attachment_type(mime) == expected

    @pytest.mark.parametrize(
        "mime",
        [
            "text/x-python",
            "application/javascript",
            "application/x-javascript",
            "application/typescript",
        ],
    )
    def test_code_types(self, mime):
        assert _mime_to_attachment_type(mime) == "code"

    @pytest.mark.parametrize(
        "mime",
        [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
    )
    def test_document_types(self, mime):
        assert _mime_to_attachment_type(mime) == "document"

    def test_unknown_fallback(self):
        assert _mime_to_attachment_type("application/octet-stream") == "unknown"

    def test_empty_string(self):
        assert _mime_to_attachment_type("") == "unknown"

    def test_none_like_empty(self):
        # None is not str, but the function guards against falsy values
        assert _mime_to_attachment_type("") == "unknown"


# =========================================================================
# SessionMessageAttachment
# =========================================================================


class TestSessionMessageAttachment:
    """Tests for the SessionMessageAttachment dataclass."""

    def test_create_minimal(self):
        att = SessionMessageAttachment(url="https://example.com/f.png")
        assert att.url == "https://example.com/f.png"
        assert att.name is None
        assert att.type is None

    def test_create_full(self):
        att = SessionMessageAttachment(url="https://example.com/f.png", name="f.png", type="image")
        assert att.name == "f.png"
        assert att.type == "image"

    def test_serialization_roundtrip(self):
        att = SessionMessageAttachment(url="https://example.com/f.png", name="f.png", type="image")
        d = att.to_dict()
        assert d["url"] == "https://example.com/f.png"
        restored = SessionMessageAttachment.from_dict(d)
        assert restored.url == att.url
        assert restored.name == att.name
        assert restored.type == att.type


# =========================================================================
# SessionMessage
# =========================================================================


class TestSessionMessage:
    """Tests for the SessionMessage dataclass."""

    def test_from_dict_maps_camel_case(self):
        msg = SessionMessage.from_dict(SAMPLE_MESSAGE_DICT)
        assert msg.id == "msg_001"
        assert msg.session_id == "sess_001"
        assert msg.user_id == "user_42"
        assert msg.agent_id == "agent_99"
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert msg.sequence == 1
        assert msg.request_id == "req_001"
        assert msg.reaction is None
        assert msg.attachments is None
        assert msg.created_at == "2025-06-01T10:01:00Z"

    def test_to_dict_uses_camel_case(self):
        msg = SessionMessage(
            id="m1",
            session_id="s1",
            user_id="u1",
            agent_id="a1",
            role="assistant",
            content="Hi",
            sequence=2,
            created_at="2025-01-01",
        )
        d = msg.to_dict()
        assert d["sessionId"] == "s1"
        assert d["userId"] == "u1"
        assert d["agentId"] == "a1"
        assert d["requestId"] is None
        assert d["createdAt"] == "2025-01-01"

    def test_with_attachments(self):
        data = {
            **SAMPLE_MESSAGE_DICT,
            "attachments": [{"url": "https://example.com/img.png", "name": "img.png", "type": "image"}],
        }
        msg = SessionMessage.from_dict(data)
        assert len(msg.attachments) == 1
        assert isinstance(msg.attachments[0], SessionMessageAttachment)
        assert msg.attachments[0].url == "https://example.com/img.png"


# =========================================================================
# Session — dataclass / serialization
# =========================================================================


class TestSessionSerialization:
    """Tests for Session dataclass creation and serialization."""

    def test_from_dict_maps_camel_case(self):
        session = Session.from_dict(SAMPLE_SESSION_DICT)
        assert session.id == "sess_001"
        assert session.user_id == "user_42"
        assert session.agent_id == "agent_99"
        assert session.name == "My Session"
        assert session.status == "active"
        assert session.run_status == "idle"
        assert session.message_count == 3
        assert session.last_message_preview == "Hello there"
        assert session.last_message_at == "2025-06-01T12:00:00Z"
        assert session.created_at == "2025-06-01T10:00:00Z"
        assert session.updated_at == "2025-06-01T12:00:00Z"

    def test_build_save_payload_create(self):
        session = Session(agent_id="agent_99", name="New")
        payload = session.build_save_payload()
        assert payload == {"agentId": "agent_99", "name": "New", "status": "active"}

    def test_build_save_payload_excludes_readonly(self):
        session = Session.from_dict(SAMPLE_SESSION_DICT)
        payload = session.build_save_payload()
        # Should NOT include read-only fields
        assert "userId" not in payload
        assert "runStatus" not in payload
        assert "messageCount" not in payload
        assert "createdAt" not in payload
        assert "updatedAt" not in payload
        assert "lastMessagePreview" not in payload
        assert "lastMessageAt" not in payload

    def test_build_save_payload_update(self):
        session = Session.from_dict(SAMPLE_SESSION_DICT)
        session.name = "Renamed"
        session.status = "archived"
        payload = session.build_save_payload()
        assert payload["name"] == "Renamed"
        assert payload["status"] == "archived"
        assert payload["agentId"] == "agent_99"

    def test_default_status_is_active(self):
        session = Session(agent_id="a1")
        assert session.status == "active"

    def test_repr(self):
        session = Session(id="sess_001", name="My Session", agent_id="a1")
        r = repr(session)
        assert "Session" in r
        assert "sess_001" in r


# =========================================================================
# Session — CRUD operations (mocked)
# =========================================================================


class TestSessionCreate:
    """Tests for Session.save() (create path)."""

    def test_save_creates_new_session(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {
            **SAMPLE_SESSION_DICT,
            "id": "new_sess",
        }
        BoundSession = _bound_session_class(ctx)
        session = BoundSession(agent_id="agent_99", name="Test")

        session.save()

        ctx.client.request.assert_called_once()
        args, kwargs = ctx.client.request.call_args
        assert args[0] == "post"
        assert "v1/sessions" in args[1]
        assert kwargs["json"]["agentId"] == "agent_99"
        assert session.id == "new_sess"

    def test_save_updates_existing_session(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = [
            # First call: create
            {**SAMPLE_SESSION_DICT, "id": "sess_001"},
            # Second call: update
            None,
        ]
        BoundSession = _bound_session_class(ctx)
        session = BoundSession(agent_id="agent_99", name="Test")
        session.save()
        assert session.id == "sess_001"

        # Now update
        session.name = "Renamed"
        session.save()

        second_call = ctx.client.request.call_args_list[1]
        assert second_call[0][0] == "put"
        assert "sess_001" in second_call[0][1]


class TestSessionGet:
    """Tests for Session.get()."""

    def test_get_by_id(self):
        ctx = _make_mock_context()
        ctx.client.get.return_value = SAMPLE_SESSION_DICT
        BoundSession = _bound_session_class(ctx)

        session = BoundSession.get("sess_001")

        ctx.client.get.assert_called_once()
        call_path = ctx.client.get.call_args[0][0]
        assert "v1/sessions/sess_001" in call_path
        assert session.id == "sess_001"
        assert session.agent_id == "agent_99"


class TestSessionDelete:
    """Tests for Session.delete()."""

    def test_delete_session(self):
        ctx = _make_mock_context()
        ctx.client.request_raw.return_value = Mock(status_code=200, ok=True)
        BoundSession = _bound_session_class(ctx)
        session = BoundSession.from_dict(SAMPLE_SESSION_DICT)
        session.context = ctx
        session._update_saved_state()

        result = session.delete()

        ctx.client.request_raw.assert_called_once()
        args = ctx.client.request_raw.call_args[0]
        assert args[0] == "delete"
        assert "sess_001" in args[1]
        assert result.completed is True


class TestSessionList:
    """Tests for Session.list() classmethod."""

    def test_list_returns_sessions(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = [
            SAMPLE_SESSION_DICT,
            {**SAMPLE_SESSION_DICT, "id": "sess_002", "name": "Second"},
        ]
        BoundSession = _bound_session_class(ctx)

        sessions = BoundSession.list()

        ctx.client.request.assert_called_once()
        args, kwargs = ctx.client.request.call_args
        assert args[0] == "get"
        assert "v1/sessions" in args[1]
        assert len(sessions) == 2
        assert sessions[0].id == "sess_001"
        assert sessions[1].id == "sess_002"

    def test_list_with_agent_id_filter(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = [SAMPLE_SESSION_DICT]
        BoundSession = _bound_session_class(ctx)

        BoundSession.list(agent_id="agent_99")

        _, kwargs = ctx.client.request.call_args
        assert kwargs["params"]["agentId"] == "agent_99"

    def test_list_with_status_filter(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = []
        BoundSession = _bound_session_class(ctx)

        BoundSession.list(status="completed")

        _, kwargs = ctx.client.request.call_args
        assert kwargs["params"]["status"] == "completed"

    def test_list_with_user_id_filter(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = []
        BoundSession = _bound_session_class(ctx)

        BoundSession.list(user_id="user_42")

        _, kwargs = ctx.client.request.call_args
        assert kwargs["params"]["userId"] == "user_42"

    def test_list_with_all_filters(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = []
        BoundSession = _bound_session_class(ctx)

        BoundSession.list(agent_id="a1", status="active", user_id="u1")

        _, kwargs = ctx.client.request.call_args
        params = kwargs["params"]
        assert params == {"agentId": "a1", "status": "active", "userId": "u1"}

    def test_list_empty_result(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = []
        BoundSession = _bound_session_class(ctx)

        sessions = BoundSession.list()
        assert sessions == []


# =========================================================================
# Session — message operations
# =========================================================================


class TestSessionMessages:
    """Tests for Session message methods."""

    def _make_session(self, ctx=None):
        ctx = ctx or _make_mock_context()
        BoundSession = _bound_session_class(ctx)
        session = BoundSession.from_dict(SAMPLE_SESSION_DICT)
        session.context = ctx
        session._update_saved_state()
        return session

    def test_messages_returns_list(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = [SAMPLE_MESSAGE_DICT]
        session = self._make_session(ctx)

        messages = session.messages()

        ctx.client.request.assert_called_once()
        args = ctx.client.request.call_args[0]
        assert args[0] == "get"
        assert "sess_001/messages" in args[1]
        assert len(messages) == 1
        assert isinstance(messages[0], SessionMessage)
        assert messages[0].id == "msg_001"

    def test_messages_empty(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = []
        session = self._make_session(ctx)

        messages = session.messages()
        assert messages == []

    def test_add_message_basic(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        msg = session.add_message(role="user", content="Hello!")

        ctx.client.request.assert_called_once()
        args, kwargs = ctx.client.request.call_args
        assert args[0] == "post"
        assert "sess_001/messages" in args[1]
        assert kwargs["json"]["role"] == "user"
        assert kwargs["json"]["content"] == "Hello!"
        assert "requestId" not in kwargs["json"]
        assert "attachments" not in kwargs["json"]
        assert isinstance(msg, SessionMessage)

    def test_add_message_with_request_id(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        session.add_message(role="user", content="Hi", request_id="req_xyz")

        payload = ctx.client.request.call_args[1]["json"]
        assert payload["requestId"] == "req_xyz"

    def test_add_message_with_attachments(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        attachments = [{"url": "https://example.com/f.png", "name": "f.png", "type": "image"}]
        session.add_message(role="user", content="See image", attachments=attachments)

        payload = ctx.client.request.call_args[1]["json"]
        assert len(payload["attachments"]) == 1
        assert payload["attachments"][0]["url"] == "https://example.com/f.png"

    def test_add_message_with_files(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        with (
            patch("aixplain.v2.upload_utils.FileUploader") as MockUploader,
            patch("aixplain.v2.upload_utils.MimeTypeDetector") as MockDetector,
        ):
            instance = MockUploader.return_value
            instance.upload.return_value = "https://cdn.example.com/uploaded.png"
            MockDetector.detect_mime_type.return_value = "image/png"

            session.add_message(role="user", content="File", files=["/tmp/photo.png"])

            instance.upload.assert_called_once_with(
                "/tmp/photo.png",
                is_temp=True,
                return_download_link=True,
            )
            payload = ctx.client.request.call_args[1]["json"]
            assert len(payload["attachments"]) == 1
            assert payload["attachments"][0]["url"] == "https://cdn.example.com/uploaded.png"
            assert payload["attachments"][0]["name"] == "photo.png"
            assert payload["attachments"][0]["type"] == "image"

    def test_add_message_merges_attachments_and_files(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        with (
            patch("aixplain.v2.upload_utils.FileUploader") as MockUploader,
            patch("aixplain.v2.upload_utils.MimeTypeDetector") as MockDetector,
        ):
            instance = MockUploader.return_value
            instance.upload.return_value = "https://cdn.example.com/doc.pdf"
            MockDetector.detect_mime_type.return_value = "application/pdf"

            existing = [{"url": "https://example.com/a.txt", "name": "a.txt", "type": "text"}]
            session.add_message(
                role="user",
                content="Both",
                attachments=existing,
                files=["/tmp/doc.pdf"],
            )

            payload = ctx.client.request.call_args[1]["json"]
            assert len(payload["attachments"]) == 2
            assert payload["attachments"][0]["url"] == "https://example.com/a.txt"
            assert payload["attachments"][1]["url"] == "https://cdn.example.com/doc.pdf"
            assert payload["attachments"][1]["type"] == "document"

    def test_get_message(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = SAMPLE_MESSAGE_DICT
        session = self._make_session(ctx)

        msg = session.get_message("msg_001")

        args = ctx.client.request.call_args[0]
        assert args[0] == "get"
        assert "sess_001/messages/msg_001" in args[1]
        assert isinstance(msg, SessionMessage)
        assert msg.id == "msg_001"

    def test_delete_message(self):
        ctx = _make_mock_context()
        ctx.client.request_raw.return_value = Mock(status_code=200, ok=True)
        session = self._make_session(ctx)

        session.delete_message("msg_001")

        args = ctx.client.request_raw.call_args[0]
        assert args[0] == "delete"
        assert "sess_001/messages/msg_001" in args[1]

    def test_react_like(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {**SAMPLE_MESSAGE_DICT, "reaction": "LIKE"}
        session = self._make_session(ctx)

        msg = session.react("msg_001", "LIKE")

        args, kwargs = ctx.client.request.call_args
        assert args[0] == "post"
        assert "sess_001/messages/msg_001/reaction" in args[1]
        assert kwargs["json"]["reaction"] == "LIKE"
        assert msg.reaction == "LIKE"

    def test_react_clear(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {**SAMPLE_MESSAGE_DICT, "reaction": None}
        session = self._make_session(ctx)

        msg = session.react("msg_001", None)

        payload = ctx.client.request.call_args[1]["json"]
        assert payload["reaction"] is None
        assert msg.reaction is None


class TestSessionValidation:
    """Tests that session methods enforce valid state."""

    def _make_unsaved_session(self):
        ctx = _make_mock_context()
        BoundSession = _bound_session_class(ctx)
        return BoundSession(agent_id="a1")

    def test_messages_requires_saved_session(self):
        session = self._make_unsaved_session()
        with pytest.raises(ValidationError):
            session.messages()

    def test_add_message_requires_saved_session(self):
        session = self._make_unsaved_session()
        with pytest.raises(ValidationError):
            session.add_message(role="user", content="hi")

    def test_get_message_requires_saved_session(self):
        session = self._make_unsaved_session()
        with pytest.raises(ValidationError):
            session.get_message("msg_001")

    def test_delete_message_requires_saved_session(self):
        session = self._make_unsaved_session()
        with pytest.raises(ValidationError):
            session.delete_message("msg_001")

    def test_react_requires_saved_session(self):
        session = self._make_unsaved_session()
        with pytest.raises(ValidationError):
            session.react("msg_001", "LIKE")


# =========================================================================
# Error handling
# =========================================================================


class TestSessionErrorHandling:
    """Tests that backend errors are handled gracefully."""

    def _make_session(self, ctx=None):
        ctx = ctx or _make_mock_context()
        BoundSession = _bound_session_class(ctx)
        session = BoundSession.from_dict(SAMPLE_SESSION_DICT)
        session.context = ctx
        session._update_saved_state()
        return session

    # --- list() errors ---

    def test_list_api_error_propagates(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = APIError("Unauthorized", status_code=401)
        BoundSession = _bound_session_class(ctx)

        with pytest.raises(APIError, match="Unauthorized"):
            BoundSession.list()

    def test_list_non_list_response_raises_resource_error(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {"error": "something went wrong"}
        BoundSession = _bound_session_class(ctx)

        with pytest.raises(ResourceError, match="Expected a list of sessions"):
            BoundSession.list()

    def test_list_malformed_item_raises_resource_error(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = ["not_a_dict"]
        BoundSession = _bound_session_class(ctx)

        with pytest.raises(ResourceError, match="Failed to parse session"):
            BoundSession.list()

    # --- messages() errors ---

    def test_messages_api_error_propagates(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = APIError("Not Found", status_code=404)
        session = self._make_session(ctx)

        with pytest.raises(APIError, match="Not Found"):
            session.messages()

    def test_messages_non_list_response_raises_resource_error(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {"error": "bad"}
        session = self._make_session(ctx)

        with pytest.raises(ResourceError, match="Expected a list of messages"):
            session.messages()

    # --- add_message() errors ---

    def test_add_message_api_error_propagates(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = APIError("Bad Request", status_code=400)
        session = self._make_session(ctx)

        with pytest.raises(APIError, match="Bad Request"):
            session.add_message(role="user", content="hello")

    def test_add_message_malformed_response_raises_resource_error(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = "not_a_dict"
        session = self._make_session(ctx)

        with pytest.raises(ResourceError, match="Failed to parse session message"):
            session.add_message(role="user", content="hello")

    def test_add_message_file_upload_error_wraps_with_context(self):
        ctx = _make_mock_context()
        session = self._make_session(ctx)

        with patch("aixplain.v2.upload_utils.FileUploader") as MockUploader:
            instance = MockUploader.return_value
            instance.upload.side_effect = Exception("S3 timeout")

            with pytest.raises(ResourceError, match="Failed to upload file.*photo.png.*session.*sess_001"):
                session.add_message(role="user", content="file", files=["/tmp/photo.png"])

    # --- get_message() errors ---

    def test_get_message_not_found(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = APIError("Message not found", status_code=404)
        session = self._make_session(ctx)

        with pytest.raises(APIError, match="Message not found"):
            session.get_message("nonexistent")

    # --- delete_message() errors ---

    def test_delete_message_not_found(self):
        ctx = _make_mock_context()
        ctx.client.request_raw.side_effect = APIError("Message not found", status_code=404)
        session = self._make_session(ctx)

        with pytest.raises(APIError, match="Message not found"):
            session.delete_message("nonexistent")

    # --- react() errors ---

    def test_react_to_user_message_error(self):
        ctx = _make_mock_context()
        ctx.client.request.side_effect = APIError("Only assistant messages can be liked/disliked", status_code=400)
        session = self._make_session(ctx)

        with pytest.raises(APIError, match="Only assistant messages"):
            session.react("msg_001", "LIKE")

    def test_react_malformed_response_raises_resource_error(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = "bad_response"
        session = self._make_session(ctx)

        with pytest.raises(ResourceError, match="Failed to parse session message"):
            session.react("msg_001", "LIKE")


# =========================================================================
# Agent — session convenience methods
# =========================================================================


class TestAgentCreateSession:
    """Tests for Agent.create_session()."""

    def test_create_session_calls_save(self):
        ctx = _make_mock_context()
        # Mock Session class bound to context
        mock_session_instance = Mock()
        mock_session_instance.save.return_value = mock_session_instance
        mock_session_instance.id = "new_sess"

        MockSession = Mock(return_value=mock_session_instance)
        ctx.Session = MockSession

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        session = agent.create_session(name="Chat 1")

        MockSession.assert_called_once_with(agent_id="agent_99", name="Chat 1")
        mock_session_instance.save.assert_called_once()
        assert session is mock_session_instance

    def test_create_session_without_name(self):
        ctx = _make_mock_context()
        mock_session_instance = Mock()
        mock_session_instance.save.return_value = mock_session_instance
        MockSession = Mock(return_value=mock_session_instance)
        ctx.Session = MockSession

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        agent.create_session()

        MockSession.assert_called_once_with(agent_id="agent_99", name=None)

    def test_create_session_with_history(self):
        ctx = _make_mock_context()
        mock_session_instance = Mock()
        mock_session_instance.save.return_value = mock_session_instance
        mock_session_instance.id = "new_sess"
        MockSession = Mock(return_value=mock_session_instance)
        ctx.Session = MockSession

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        session = agent.create_session(name="With History", history=history)

        mock_session_instance.save.assert_called_once()
        assert mock_session_instance.add_message.call_count == 3
        calls = mock_session_instance.add_message.call_args_list
        assert calls[0] == call(role="user", content="Hello", attachments=None, files=None)
        assert calls[1] == call(role="assistant", content="Hi there!", attachments=None, files=None)
        assert calls[2] == call(role="user", content="How are you?", attachments=None, files=None)

    def test_create_session_with_history_attachments_and_files(self):
        ctx = _make_mock_context()
        mock_session_instance = Mock()
        mock_session_instance.save.return_value = mock_session_instance
        mock_session_instance.id = "new_sess"
        MockSession = Mock(return_value=mock_session_instance)
        ctx.Session = MockSession

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        att = [{"url": "https://example.com/img.png", "name": "img.png", "type": "image"}]
        history = [
            {"role": "user", "content": "See image", "attachments": att},
            {"role": "user", "content": "And file", "files": ["/tmp/data.csv"]},
            {"role": "assistant", "content": "Got it"},
        ]
        agent.create_session(name="Rich History", history=history)

        calls = mock_session_instance.add_message.call_args_list
        assert calls[0] == call(role="user", content="See image", attachments=att, files=None)
        assert calls[1] == call(role="user", content="And file", attachments=None, files=["/tmp/data.csv"])
        assert calls[2] == call(role="assistant", content="Got it", attachments=None, files=None)

    def test_create_session_with_invalid_history(self):
        ctx = _make_mock_context()
        ctx.Session = Mock()

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        with pytest.raises(ValueError):
            agent.create_session(history=[{"bad": "format"}])

    def test_create_session_requires_saved_agent(self):
        ctx = _make_mock_context()
        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(name="Unsaved Agent")

        with pytest.raises(ValueError, match="must be saved"):
            agent.create_session()


class TestAgentListSessions:
    """Tests for Agent.list_sessions()."""

    def test_list_sessions_delegates_to_session_list(self):
        ctx = _make_mock_context()
        mock_sessions = [Mock(), Mock()]
        ctx.Session = Mock()
        ctx.Session.list.return_value = mock_sessions

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        result = agent.list_sessions()

        ctx.Session.list.assert_called_once_with(agent_id="agent_99", status=None)
        assert result == mock_sessions

    def test_list_sessions_with_status_filter(self):
        ctx = _make_mock_context()
        ctx.Session = Mock()
        ctx.Session.list.return_value = []

        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(id="agent_99", name="Test Agent")

        agent.list_sessions(status="completed")

        ctx.Session.list.assert_called_once_with(agent_id="agent_99", status="completed")

    def test_list_sessions_requires_saved_agent(self):
        ctx = _make_mock_context()
        BoundAgent = _bound_agent_class(ctx)
        agent = BoundAgent(name="Unsaved Agent")

        with pytest.raises(ValueError, match="must be saved"):
            agent.list_sessions()


# =========================================================================
# Core registration
# =========================================================================


class TestCoreSessionRegistration:
    """Tests that Session is properly registered in Aixplain."""

    def test_session_registered_on_init(self):
        from aixplain.v2.core import Aixplain

        ax = Aixplain(api_key="test_key")
        assert ax.Session is not None
        assert issubclass(ax.Session, Session)
        assert ax.Session.context is ax

    def test_session_unique_per_instance(self):
        from aixplain.v2.core import Aixplain

        ax1 = Aixplain(api_key="key1")
        ax2 = Aixplain(api_key="key2")
        assert ax1.Session is not ax2.Session
        assert ax1.Session.context is ax1
        assert ax2.Session.context is ax2

    def test_session_enums_on_aixplain_class(self):
        from aixplain.v2.core import Aixplain

        assert Aixplain.SessionStatus is SessionStatus
        assert Aixplain.RunStatus is RunStatus
        assert Aixplain.MessageRole is MessageRole
        assert Aixplain.Reaction is Reaction
        assert Aixplain.AttachmentType is AttachmentType
