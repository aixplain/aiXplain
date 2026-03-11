"""Functional tests for v2 Session management.

These tests run against a real backend and require valid credentials.
Set TEAM_API_KEY (or AIXPLAIN_API_KEY) in the environment.

A test agent is created once per module and cleaned up afterwards.
"""

import os
import tempfile
import time
import warnings

import pytest

from aixplain.v2 import Session, SessionMessage, SessionStatus
from aixplain.v2.exceptions import APIError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_agent(client):
    """Create a temporary agent for session tests."""
    agent = client.Agent(
        name=f"Session Test Agent {int(time.time())}",
        description="Temporary agent for session functional tests",
        instructions="You are a helpful test agent. Keep responses short.",
    )
    agent.save()
    yield agent
    try:
        agent.delete()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


class TestSessionCRUD:
    """End-to-end session create / get / list / update / delete."""

    def test_create_session_via_agent(self, client, test_agent):
        """Creating a session through an agent should return a saved Session."""
        session = test_agent.create_session(name="Func Test Session")

        assert session.id is not None
        assert isinstance(session, Session)
        assert session.agent_id == test_agent.id
        assert session.name == "Func Test Session"
        assert session.status == "active"

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_create_session_directly(self, client, test_agent):
        """Creating a Session instance directly and calling .save()."""
        session = client.Session(agent_id=test_agent.id, name="Direct Create")
        session.save()

        assert session.id is not None
        assert session.agent_id == test_agent.id

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_get_session(self, client, test_agent):
        """Retrieving a session by ID should return the same session."""
        session = test_agent.create_session(name="Get Test")
        fetched = client.Session.get(session.id)

        assert fetched.id == session.id
        assert fetched.name == session.name
        assert fetched.agent_id == session.agent_id

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_list_sessions_for_agent(self, client, test_agent):
        """Listing sessions for an agent should include the created session."""
        session = test_agent.create_session(name="List Test")

        sessions = test_agent.list_sessions()

        assert isinstance(sessions, list)
        session_ids = [s.id for s in sessions]
        assert session.id in session_ids

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_list_sessions_with_status_filter(self, client, test_agent):
        """Filtering by status should only return matching sessions."""
        session = test_agent.create_session(name="Status Filter Test")

        active = test_agent.list_sessions(status="active")
        assert all(s.status == "active" for s in active)

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_update_session(self, client, test_agent):
        """Updating session name via save() should persist the change."""
        session = test_agent.create_session(name="Before Update")
        session.name = "After Update"
        session.save()

        fetched = client.Session.get(session.id)
        assert fetched.name == "After Update"

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_create_session_with_history(self, client, test_agent):
        """Creating a session with history should seed it with messages."""
        history = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
        ]
        session = test_agent.create_session(name="History Test", history=history)

        assert session.id is not None
        messages = session.messages()
        assert len(messages) >= 2
        contents = [m.content for m in messages]
        assert "What is 2+2?" in contents
        assert "4" in contents

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass

    def test_delete_session(self, client, test_agent):
        """Deleting a session should succeed."""
        session = test_agent.create_session(name="Delete Me")
        session_id = session.id
        assert session_id is not None

        result = session.delete()
        assert result.completed is True


# ---------------------------------------------------------------------------
# Session messages
# ---------------------------------------------------------------------------


class TestSessionMessages:
    """End-to-end tests for session message operations."""

    @pytest.fixture()
    def session(self, client, test_agent):
        """Create a session for message tests and clean up after."""
        s = test_agent.create_session(name=f"Msg Test {int(time.time())}")
        yield s
        try:
            s.delete()
        except Exception:
            pass

    def test_add_and_get_message(self, session):
        """Adding a message should return a SessionMessage with content."""
        msg = session.add_message(role="user", content="Hello from test!")

        assert isinstance(msg, SessionMessage)
        assert msg.id is not None
        assert msg.content == "Hello from test!"
        assert msg.role == "user"

    def test_list_messages(self, session):
        """After adding messages, messages() should return them."""
        session.add_message(role="user", content="First message")
        session.add_message(role="assistant", content="Second message")

        messages = session.messages()

        assert isinstance(messages, list)
        assert len(messages) >= 2
        contents = [m.content for m in messages]
        assert "First message" in contents
        assert "Second message" in contents

    def test_get_single_message(self, session):
        """get_message() should return the specific message."""
        created = session.add_message(role="user", content="Specific message")

        fetched = session.get_message(created.id)

        assert fetched.id == created.id
        assert fetched.content == "Specific message"

    def test_delete_message(self, session):
        """delete_message() should remove the message."""
        msg = session.add_message(role="user", content="Delete this message")
        session.delete_message(msg.id)

        remaining = session.messages()
        remaining_ids = [m.id for m in remaining]
        assert msg.id not in remaining_ids

    def test_add_message_with_url_attachments(self, session):
        """Adding a message with explicit URL attachments should include them."""
        attachments = [
            {"url": "https://example.com/test.png", "name": "test.png", "type": "image"},
        ]
        msg = session.add_message(
            role="user",
            content="See attached",
            attachments=attachments,
        )

        assert msg.id is not None
        if msg.attachments:
            assert msg.attachments[0].url == "https://example.com/test.png"
            assert msg.attachments[0].name == "test.png"
            assert msg.attachments[0].type == "image"

    def test_add_message_with_file_upload(self, session):
        """Uploading a local file via add_message(files=...) should attach it."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", prefix="session_test_", delete=False) as f:
            f.write("Test content for file upload verification.\n")
            tmp_path = f.name

        try:
            msg = session.add_message(
                role="user",
                content="Please review this file",
                files=[tmp_path],
            )

            assert msg.id is not None
            assert msg.attachments is not None, "Backend should echo attachments"
            assert len(msg.attachments) == 1

            att = msg.attachments[0]
            assert att.url is not None and att.url.startswith("http")
            assert att.name == os.path.basename(tmp_path)
            assert att.type == "text"

            # Verify the attachment persists when re-fetching
            fetched = session.get_message(msg.id)
            assert fetched.attachments is not None
            assert len(fetched.attachments) == 1
        finally:
            os.remove(tmp_path)

    def test_react_like_and_dislike(self, session):
        """Reacting to an assistant message with LIKE then DISLIKE should work."""
        session.add_message(role="user", content="Say something")
        msg = session.add_message(role="assistant", content="Here is my response")

        liked = session.react(msg.id, "LIKE")
        assert liked.reaction == "LIKE"

        disliked = session.react(msg.id, "DISLIKE")
        assert disliked.reaction == "DISLIKE"

    def test_clear_reaction(self, session):
        """Passing None to react() should clear the reaction."""
        session.add_message(role="user", content="Say something")
        msg = session.add_message(role="assistant", content="Clear reaction response")
        session.react(msg.id, "DISLIKE")

        cleared = session.react(msg.id, None)
        assert cleared.reaction is None


# ---------------------------------------------------------------------------
# Agent run + session interaction
# ---------------------------------------------------------------------------


class TestSessionWithAgentRun:
    """Tests for how agent.run() interacts with sessions."""

    def test_run_with_session_adds_messages(self, client, test_agent):
        """Running an agent with a session_id should add messages to the session."""
        session = test_agent.create_session(name="Run Test")
        msgs_before = session.messages()

        result = test_agent.run(
            "What is the capital of France?",
            session_id=session.id,
        )
        assert result.status == "SUCCESS"

        msgs_after = session.messages()
        assert len(msgs_after) > len(msgs_before), "Backend should auto-add messages to the session during a run"

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestSessionErrors:
    """Tests that backend errors are raised gracefully."""

    def test_get_nonexistent_session(self, client):
        """Getting a session that doesn't exist should raise APIError."""
        with pytest.raises(APIError):
            client.Session.get("nonexistent-session-id-12345")

    def test_react_to_user_message_raises_error(self, client, test_agent):
        """Reacting to a user message should raise an APIError."""
        session = test_agent.create_session(name="React Error Test")
        msg = session.add_message(role="user", content="Can't like this")

        with pytest.raises(APIError, match="assistant"):
            session.react(msg.id, "LIKE")

        # Cleanup
        try:
            session.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Deprecation
# ---------------------------------------------------------------------------


class TestDeprecation:
    """Test that deprecated methods emit warnings."""

    def test_generate_session_id_emits_deprecation_warning(self, test_agent):
        """generate_session_id() should emit a DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                test_agent.generate_session_id()
            except Exception:
                pass
            dep = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(dep) >= 1
            assert "create_session" in str(dep[0].message)
