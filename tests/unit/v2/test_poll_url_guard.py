"""Regression tests: poll URLs from response bodies must not receive the API key.

A poll URL is supplied by an API response body, i.e. by data that flows through
model/agent/tool execution. BUG-937: the SDK used to hand ``TEAM_API_KEY`` to
whatever host such a body named, on every resource that polls. These tests cover
each poll path with a real :class:`AixplainClient`, and assert the transport is
never reached.
"""

import pytest
from dataclasses import dataclass
from unittest.mock import Mock, patch

from dataclasses_json import dataclass_json

from aixplain.v2.agent import Agent
from aixplain.v2.client import AixplainClient
from aixplain.v2.exceptions import UntrustedURLError
from aixplain.v2.model import Model
from aixplain.v2.resource import BaseResource, Result, RunnableResourceMixin
from aixplain.v2.utility import Utility


BACKEND_URL = "https://platform-api.aixplain.com"
MODEL_URL = "https://models.aixplain.com/api/v2/execute"

# The two URLs the bug report reproduced against the host-blind regex, plus a
# link-local address that must never see a credentialed request.
FOREIGN_POLL_URLS = [
    "http://evil.example.com/sdk/runs/abc",
    "https://evil.example.com/sdk/runs/abc",
    "http://169.254.169.254/api/v1/data/abc",
    "http://127.0.0.1/sdk/runs/abc",
    "http://10.0.0.5/sdk/models/abc/result",
]


def _context():
    """Build a context whose client is a real, production-configured client."""
    context = Mock()
    context.backend_url = BACKEND_URL
    context.model_url = MODEL_URL
    context.client = AixplainClient(
        base_url=BACKEND_URL,
        team_api_key="team-key",
        trusted_urls=[MODEL_URL],
    )
    return context


def _bind(cls, **kwargs):
    """Instantiate a resource subclass bound to a real-client context."""

    @dataclass_json
    @dataclass
    class Bound(cls):
        pass

    instance = Bound(**kwargs)
    instance.context = _context()
    return instance


@dataclass_json
@dataclass
class _PlainRunnable(BaseResource, RunnableResourceMixin[Result, dict]):
    """Bare mixin subclass, standing in for every resource that inherits poll()."""

    RESOURCE_PATH: str = "sdk/plain"


@pytest.fixture
def no_transport():
    """Patch the transport layer and hand back the mock, to assert it stays unused."""
    with patch("requests.adapters.HTTPAdapter.send") as send:
        yield send


@pytest.mark.parametrize(
    "factory",
    [
        lambda: _bind(Model, id="model-1", name="m"),
        lambda: _bind(Agent, id="agent-1", name="a"),
        lambda: _bind(Utility, id="utility-1", name="u"),
        lambda: _bind(_PlainRunnable, id="plain-1", name="p"),
    ],
    ids=["model", "agent", "utility", "plain-runnable"],
)
@pytest.mark.parametrize("poll_url", FOREIGN_POLL_URLS)
class TestForeignPollURLsAreRefused:
    """Every resource that polls must refuse a foreign poll URL."""

    def test_poll_raises_without_opening_a_socket(self, factory, poll_url, no_transport):
        """poll() refuses before the transport is invoked."""
        resource = factory()

        with pytest.raises(UntrustedURLError):
            resource.poll(poll_url)

        no_transport.assert_not_called()

    def test_sync_poll_raises_immediately(self, factory, poll_url, no_transport):
        """sync_poll() must re-raise, not swallow the error and poll until timeout.

        ``sync_poll`` catches broad exceptions and keeps looping; if
        ``UntrustedURLError`` fell into that branch the acceptance criterion
        would degrade into a 300-second ``TimeoutError``.
        """
        resource = factory()

        with pytest.raises(UntrustedURLError):
            # Short timeout so a regression here fails fast instead of hanging.
            resource.sync_poll(poll_url, timeout=1, wait_time=0.2)

        no_transport.assert_not_called()


class TestActionPollPathIsGuarded:
    """``ActionMixin._poll_for_data`` polls a body-supplied URL outside the run mixin."""

    def _actions(self):
        """Build a bare ActionMixin bound to a real-client context."""
        from aixplain.v2.integration import ActionMixin

        @dataclass_json
        @dataclass
        class _Actions(ActionMixin):
            pass

        instance = _Actions()
        instance.context = _context()
        return instance

    def test_foreign_action_poll_url_is_refused(self, no_transport):
        """A LIST_ACTIONS response naming a foreign host must not be polled."""
        actions = self._actions()

        with pytest.raises(UntrustedURLError):
            actions._poll_for_data(
                {"completed": False, "data": "http://169.254.169.254/api/v1/data/abc"},
                timeout=1,
                wait_time=0,
            )

        no_transport.assert_not_called()

    def test_trusted_action_poll_url_still_works(self):
        """A poll URL on an aiXplain host keeps resolving."""
        actions = self._actions()
        with patch.object(
            actions.context.client, "request", return_value={"completed": True, "data": ["ok"]}
        ) as mock_request:
            data = actions._poll_for_data(
                {"completed": False, "data": f"{BACKEND_URL}/sdk/runs/abc"},
                timeout=5,
                wait_time=0,
            )

        assert data == ["ok"]
        mock_request.assert_called_once_with("get", f"{BACKEND_URL}/sdk/runs/abc")


class TestTrustedPollURLsStillWork:
    """The guard must not break legitimate polling."""

    @pytest.mark.parametrize(
        "poll_url",
        [
            f"{BACKEND_URL}/sdk/agents/abc/result",
            "https://models.aixplain.com/api/v1/data/abc",
            "sdk/runs/abc",
        ],
    )
    def test_trusted_poll_url_reaches_the_client(self, poll_url):
        """Both aiXplain hosts and relative paths poll as before."""
        resource = _bind(_PlainRunnable, id="plain-1", name="p")
        with patch.object(
            resource.context.client, "get", return_value={"status": "SUCCESS", "completed": True}
        ) as mock_get:
            result = resource.poll(poll_url)

        mock_get.assert_called_once_with(poll_url)
        assert result.completed

    def test_agent_execution_id_is_resolved_and_trusted(self):
        """A bare execution ID still resolves to the backend agent-result endpoint."""
        agent = _bind(Agent, id="agent-1", name="a")
        with patch.object(
            agent.context.client, "get", return_value={"status": "SUCCESS", "completed": True}
        ) as mock_get:
            agent.poll("exec-123")

        assert mock_get.call_args[0][0] == f"{BACKEND_URL}/sdk/agents/exec-123/result"


class TestModelIsPollURL:
    """``Model._is_poll_url`` is a routing predicate, not an authorization check."""

    @pytest.mark.parametrize(
        "url",
        [
            "sdk/runs/abc",
            "/sdk/runs/abc",
            f"{BACKEND_URL}/sdk/runs/abc",
            f"{BACKEND_URL}/sdk/models/abc/result",
            "https://models.aixplain.com/api/v1/data/abc",
            # Host-blind by design: routing says "poll-shaped", the guard says "no".
            "http://evil.example.com/sdk/runs/abc",
            "http://169.254.169.254/api/v1/data/abc",
        ],
    )
    def test_poll_shaped_paths_route_to_polling(self, url):
        """Anything whose path is poll-shaped is routed to poll()."""
        assert Model._is_poll_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://aixplain-platform-assets.s3.amazonaws.com/output/audio.wav",
            f"{BACKEND_URL}/sdk/agents/abc/result",
            "https://evil.example.com/",
            "",
        ],
    )
    def test_media_output_urls_are_not_poll_urls(self, url):
        """Result/media URLs stay data and are returned to the caller unchanged."""
        assert Model._is_poll_url(url) is False

    def test_query_string_does_not_defeat_routing(self):
        """A signed query string on a poll path must still route to polling."""
        assert Model._is_poll_url(f"{BACKEND_URL}/sdk/runs/abc?token=x") is True


class TestModelRunRefusesForeignPollURL:
    """A sync model whose response names a foreign poll URL must raise."""

    def test_run_raises_on_foreign_poll_url(self, no_transport):
        """The end-to-end acceptance case from the bug report."""
        model = _bind(Model, id="model-1", name="m")
        model.function = "text-generation"
        in_progress = Model.RESPONSE_CLASS.from_dict(
            {
                "status": "IN_PROGRESS",
                "completed": False,
                "url": "http://169.254.169.254/api/v1/data/abc",
            }
        )

        with patch.object(Model, "is_sync_only", True):
            with patch.object(model, "_run_sync_v2", return_value=in_progress):
                with pytest.raises(UntrustedURLError):
                    # Explicit short timeout: if sync_poll ever stops re-raising
                    # this error it degrades to polling until timeout, and the
                    # default is 300s.
                    model.run(text="hello", timeout=1)

        no_transport.assert_not_called()
