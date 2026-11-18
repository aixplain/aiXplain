"""Unrecognised agent run kwargs warn but are still forwarded (BUG-1138)."""

import warnings
from unittest.mock import MagicMock, patch

import pytest

from aixplain import Agent


def _agent():
    agent = Agent.from_dict({"id": "a1", "name": "t"})
    agent.context = MagicMock()
    agent.status = None
    fake_result = MagicMock()
    fake_result.url = None
    fake_result.completed = True
    agent.handle_run_response = lambda response, **kw: fake_result
    return agent


def test_unknown_kwarg_warns_and_is_still_sent():
    agent = _agent()
    with pytest.warns(UserWarning, match="tags") as record:
        agent.run(query="q", tags=["a"])

    matching = [w for w in record if "Unrecognised agent run parameter" in str(w.message)]
    assert len(matching) == 1
    assert matching[0].filename == __file__
    body = agent.context.client.request.call_args.kwargs["json"]
    assert body["tags"] == ["a"]


def test_declared_kwargs_do_not_warn():
    agent = _agent()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        agent.run(
            "q",
            identifier="end-user-1",
            criteria="Be concise.",
            timeout=30,
            wait_time=0.1,
            run_retries=0,
            progress_format=None,
        )

    body = agent.context.client.request.call_args.kwargs["json"]
    assert body["identifier"] == "end-user-1"


def test_identifier_is_sent_unchanged():
    agent = _agent()
    agent.run(query="q", identifier="end-user-1")

    call = agent.context.client.request.call_args
    assert call.kwargs["json"]["identifier"] == "end-user-1"


def test_session_path_warns_before_running():
    agent = _agent()
    with patch.object(Agent, "_run_with_session", return_value="done") as run_with_session:
        with pytest.warns(UserWarning, match="labels"):
            assert agent.run("q", session="s1", labels={"k": "v"}) == "done"
    run_with_session.assert_called_once()


def test_run_async_warns_on_unknown_kwarg():
    agent = _agent()
    with patch("aixplain.v2.resource.RunnableResourceMixin.run_async", return_value="submitted") as base:
        with pytest.warns(UserWarning, match="tags"):
            assert agent.run_async("q", tags=["a"]) == "submitted"
    assert base.call_args.kwargs["tags"] == ["a"]
