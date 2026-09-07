"""Tests that the v2 client never logs credentials or bodies (BUG-939).

The client used to ``logger.debug`` the whole ``kwargs`` dict -- which by that
point carries the merged ``x-api-key`` header and the request body -- plus the
full ``response.text``. With ``.env.example`` shipping ``LOG_LEVEL=DEBUG``, a
single connected Slack tool wrote the user's third-party bot token and the team
key into the application log.
"""

import logging

import pytest
from unittest.mock import Mock, patch

from aixplain.v2.client import (
    LOG_BODIES_ENV_VAR,
    LOG_BODY_MAX_BYTES,
    AixplainClient,
)

TEAM_KEY = "TEAMKEY_AAA"
SLACK_TOKEN = "xoxb-USER-THIRD-PARTY-SECRET"
RESPONSE_BODY = '{"accessKey": "ACCESSKEY_FOR_EVERY_KEY_ON_THE_ACCOUNT"}'
REQUEST_BODY = {"name": "slack", "data": {"token": SLACK_TOKEN}}

SECRETS = (TEAM_KEY, SLACK_TOKEN, "ACCESSKEY_FOR_EVERY_KEY_ON_THE_ACCOUNT", "x-api-key")


@pytest.fixture(autouse=True)
def bodies_off(monkeypatch):
    """Ensure the body-logging opt-in is off unless a test sets it."""
    monkeypatch.delenv(LOG_BODIES_ENV_VAR, raising=False)


@pytest.fixture
def client():
    """A client pointed at a trusted origin, with a recognisable API key."""
    return AixplainClient(base_url="https://platform-api.aixplain.com", team_api_key=TEAM_KEY)


def _mock_response(body=RESPONSE_BODY, status=200):
    """Return a mock response carrying *body* and *status*."""
    response = Mock()
    response.ok = 200 <= status < 400
    response.status_code = status
    response.text = body
    response.content = body.encode()
    response.headers = {"Content-Length": str(len(body))}
    return response


def _messages(caplog):
    """Return every formatted log message captured so far."""
    return [record.getMessage() for record in caplog.records]


def test_no_record_contains_a_secret_or_a_body(client, caplog):
    """The acceptance criterion: nothing sensitive reaches a log record."""
    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=_mock_response()):
            client.request_raw(
                "POST",
                "sdk/tools",
                json=REQUEST_BODY,
                headers={"Authorization": "Bearer abcdefghijklmnopqrst"},
            )

    joined = "\n".join(_messages(caplog))
    for secret in SECRETS:
        assert secret not in joined
    assert RESPONSE_BODY not in joined
    assert "slack" not in joined


def test_outline_is_still_logged(client, caplog):
    """Method, path, status and byte count remain available for debugging."""
    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=_mock_response()):
            client.request_raw("POST", "sdk/tools", json=REQUEST_BODY)

    joined = "\n".join(_messages(caplog))
    assert "POST" in joined
    assert "sdk/tools" in joined
    assert "200" in joined
    assert f"{len(RESPONSE_BODY)} bytes" in joined


def test_query_string_is_not_logged(client, caplog):
    """Query strings carry presigned signatures and one-time tokens."""
    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=_mock_response()):
            client.request_raw("GET", "https://platform-api.aixplain.com/sdk/x?X-Amz-Signature=SECRETSIG")

    joined = "\n".join(_messages(caplog))
    assert "SECRETSIG" not in joined
    assert "/sdk/x" in joined


def test_opt_in_logs_bodies_but_redacts_credentials(client, caplog, monkeypatch):
    """With the opt-in on, bodies appear -- with credential values masked."""
    monkeypatch.setenv(LOG_BODIES_ENV_VAR, "1")
    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=_mock_response()):
            client.request_raw("POST", "sdk/tools", json=REQUEST_BODY)

    joined = "\n".join(_messages(caplog))
    assert "slack" in joined  # the body really is logged now
    assert SLACK_TOKEN not in joined
    assert "***REDACTED***" in joined


def test_opt_in_truncates_long_bodies(client, caplog, monkeypatch):
    """A large response cannot flood the log even under the opt-in."""
    monkeypatch.setenv(LOG_BODIES_ENV_VAR, "1")
    big = "a" * (LOG_BODY_MAX_BYTES * 3)
    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=_mock_response(body=big)):
            client.request_raw("GET", "sdk/x")

    joined = "\n".join(_messages(caplog))
    assert "(truncated)" in joined
    assert len(joined) < len(big)


def test_streaming_request_does_not_consume_the_body(client, caplog):
    """The streaming path must not touch ``.content``/``.text`` to log a size."""
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.headers = {}
    type(response).content = property(lambda self: pytest.fail("streaming body was consumed"))
    type(response).text = property(lambda self: pytest.fail("streaming body was consumed"))

    with caplog.at_level(logging.DEBUG):
        with patch.object(client.session, "request", return_value=response):
            client.request_stream("GET", "sdk/stream")

    assert any("sdk/stream" in message for message in _messages(caplog))


def test_env_example_does_not_ship_debug_logging():
    """``.env.example`` was the documented way to turn the leak on."""
    from pathlib import Path

    env_example = Path(__file__).resolve().parents[3] / ".env.example"
    lines = [line.strip() for line in env_example.read_text().splitlines() if not line.strip().startswith("#")]
    assert "LOG_LEVEL=DEBUG" not in lines
    assert "LOG_LEVEL=INFO" in lines
