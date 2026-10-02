"""Functional tests for v2 Session management.

These tests run against a real backend and require valid credentials.
Set TEAM_API_KEY (or AIXPLAIN_API_KEY) in the environment.

A test agent is created once per module. Every agent and session is registered
with the shared cleanup tracker as soon as it is saved, so a failing test still
deletes what it created.
"""

import os
import tempfile
import time
import uuid

import pytest

from aixplain.v2 import Session, SessionMessage, SessionStatus
from aixplain.v2.exceptions import APIError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_agent(client, module_resource_tracker):
    """Create a temporary agent for session tests."""
    agent = client.Agent(
        name=f"Session Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        description="Temporary agent for session functional tests",
        instructions="You are a helpful test agent. Keep responses short.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def _make_session(client, agent, tracker, name=None, **kwargs):
    """Create and persist a session bound to ``agent``, registered with ``tracker`` for cleanup."""
    session = client.Session(agent=agent, name=name, **kwargs)
    session.save()
    tracker.append(session)
    return session


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


class TestSessionCRUD:
    """End-to-end session create / get / list / update / delete."""

    def test_create_session_with_agent_object(self, client, test_agent, resource_tracker):
        """Creating a session with ``Session(agent=…)`` returns a saved Session."""
        session = _make_session(client, test_agent, resource_tracker, name="Func Test Session")

        assert session.id is not None
        assert isinstance(session, Session)
        assert session.agent_id == test_agent.id
        assert session.name == "Func Test Session"
        assert session.status == "active"

    def test_create_session_with_agent_id(self, client, test_agent, resource_tracker):
        """``Session(agent=…)`` also accepts a bare agent id string."""
        session = client.Session(agent=test_agent.id, name="Direct Create")
        session.save()
        resource_tracker.append(session)

        assert session.id is not None
        assert session.agent_id == test_agent.id

    def test_get_session(self, client, test_agent, resource_tracker):
        """Retrieving a session by ID should return the same session."""
        session = _make_session(client, test_agent, resource_tracker, name="Get Test")
        fetched = client.Session.get(session.id)

        assert fetched.id == session.id
        assert fetched.name == session.name
        assert fetched.agent_id == session.agent_id

    def test_search_sessions_for_agent(self, client, test_agent, resource_tracker):
        """Session.search(agent=…) returns a Page including the created session."""
        session = _make_session(client, test_agent, resource_tracker, name="List Test")

        page = client.Session.search(agent=test_agent)

        session_ids = [s.id for s in page.results]
        assert session.id in session_ids
        assert page.total >= 1

    def test_search_sessions_with_status_filter(self, client, test_agent, resource_tracker):
        """Filtering by status should only return matching sessions."""
        _make_session(client, test_agent, resource_tracker, name="Status Filter Test")

        page = client.Session.search(agent=test_agent, status="active")
        assert all(s.status == "active" for s in page.results)

    def test_update_session(self, client, test_agent, resource_tracker):
        """Updating session name via save() should persist the change."""
        session = _make_session(client, test_agent, resource_tracker, name="Before Update")
        session.name = "After Update"
        session.save()

        fetched = client.Session.get(session.id)
        assert fetched.name == "After Update"

    def test_seed_session_with_messages(self, client, test_agent, resource_tracker):
        """Seeding a session via add_message should persist the transcript."""
        session = _make_session(client, test_agent, resource_tracker, name="History Test")
        session.add_message(role="user", content="What is 2+2?")
        session.add_message(role="assistant", content="4")

        assert session.id is not None
        messages = session.messages()
        assert len(messages) >= 2
        contents = [m.content for m in messages]
        assert "What is 2+2?" in contents
        assert "4" in contents

    def test_delete_session(self, client, test_agent, resource_tracker):
        """Deleting a session should succeed."""
        session = _make_session(client, test_agent, resource_tracker, name="Delete Me")
        session_id = session.id
        assert session_id is not None

        result = session.delete()
        resource_tracker.mark_cleaned(session)
        assert result.completed is True


# ---------------------------------------------------------------------------
# Session messages
# ---------------------------------------------------------------------------


class TestSessionMessages:
    """End-to-end tests for session message operations."""

    @pytest.fixture()
    def session(self, client, test_agent, resource_tracker):
        """Create a session for message tests; ``resource_tracker`` deletes it afterwards."""
        return _make_session(
            client, test_agent, resource_tracker, name=f"Msg Test {int(time.time())}-{uuid.uuid4().hex[:6]}"
        )

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

    @pytest.mark.skip(
        reason="Backend bug: sessions service validates role but stores every "
        "message as role='user' (verified 2026-07-21), so assistant messages "
        "can never be reacted to. Unskip when the backend persists the role."
    )
    def test_react_like_and_dislike(self, session):
        """Reacting to an assistant message with LIKE then DISLIKE should work."""
        session.add_message(role="user", content="Say something")
        msg = session.add_message(role="assistant", content="Here is my response")

        liked = session.react(msg.id, "LIKE")
        assert liked.reaction == "LIKE"

        disliked = session.react(msg.id, "DISLIKE")
        assert disliked.reaction == "DISLIKE"

    @pytest.mark.skip(
        reason="Backend bug: sessions service stores every message as role='user' — see test_react_like_and_dislike."
    )
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

    def test_run_with_session_adds_messages(self, client, test_agent, resource_tracker):
        """Running an agent with session=… should add messages to the session."""
        session = _make_session(client, test_agent, resource_tracker, name="Run Test")
        msgs_before = session.messages()

        result = test_agent.run(
            "What is the capital of France?",
            session=session,
        )
        assert result.status == "SUCCESS"

        msgs_after = session.messages()
        assert len(msgs_after) > len(msgs_before), "Backend should auto-add messages to the session during a run"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestSessionErrors:
    """Tests that backend errors are raised gracefully."""

    def test_get_nonexistent_session(self, client):
        """Getting a session that doesn't exist should raise APIError."""
        with pytest.raises(APIError):
            client.Session.get("nonexistent-session-id-12345")

    def test_react_to_user_message_raises_error(self, client, test_agent, resource_tracker):
        """Reacting to a user message should raise an APIError."""
        session = _make_session(client, test_agent, resource_tracker, name="React Error Test")
        msg = session.add_message(role="user", content="Can't like this")

        with pytest.raises(APIError, match="assistant"):
            session.react(msg.id, "LIKE")
