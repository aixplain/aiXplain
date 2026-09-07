"""Tests that save() does not write SDK defaults over server state (BUG-1093).

``Agent.llm`` carries a class default (``DEFAULT_LLM``). When the response that
hydrated an agent omitted ``model``, ``build_save_payload`` used to emit that
default, so an unrelated edit (``agent.name = ...; agent.save()``) silently
replaced the platform's configured model.

Suppression is gated on hydration provenance: it only applies to a value that
came from a server response which did not mention the key, and never to a value
the caller assigned or to a locally constructed agent being created.
"""

from unittest.mock import MagicMock

import pytest

from aixplain.v2.agent import Agent


@pytest.fixture
def context() -> MagicMock:
    """Bind a mock context to the Agent class for the duration of a test."""
    original = Agent.context
    mock = MagicMock()
    Agent.context = mock
    try:
        yield mock
    finally:
        Agent.context = original


def _fetch(context: MagicMock, payload: dict) -> Agent:
    """Hydrate an Agent through GetResourceMixin.get from *payload*."""
    context.client.get.return_value = payload
    return Agent.get(payload["id"])


def test_save_omits_model_when_get_response_omitted_it(context):
    """A GET without "model" must not cause the SDK default to be PUT back."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})

    assert agent.llm == Agent.DEFAULT_LLM  # read side is unchanged
    assert "model" not in agent.build_save_payload()


def test_save_sends_model_when_get_response_included_it(context):
    """A server-reported model is echoed back unchanged."""
    agent = _fetch(context, {"id": "A1", "name": "agent", "model": {"id": "SERVER-LLM"}})

    assert agent.build_save_payload()["model"] == {"id": "SERVER-LLM"}


def test_save_sends_model_when_assigned_after_fetch(context):
    """An explicit assignment is the caller's intent and is always sent."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    agent.llm = "CHOSEN-LLM"

    assert agent.build_save_payload()["model"] == {"id": "CHOSEN-LLM"}


def test_save_sends_model_when_explicitly_assigned_the_default(context):
    """Assigning the default explicitly is still an assignment, not a fallback."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    agent.llm = Agent.DEFAULT_LLM

    assert agent.build_save_payload()["model"] == {"id": Agent.DEFAULT_LLM}


def test_save_sends_model_when_passed_through_save_kwargs(context):
    """save(llm=...) sets the attribute, which counts as explicit."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    context.client.request.return_value = {"id": "A1", "name": "agent"}

    agent.save(llm="KWARG-LLM")

    payload = context.client.request.call_args.kwargs["json"]
    assert payload["model"] == {"id": "KWARG-LLM"}


def test_create_still_sends_default_model(context):
    """Non-regression: a locally built agent still creates with the default LLM."""
    agent = Agent(name="new agent")

    assert agent.build_save_payload()["model"] == {"id": Agent.DEFAULT_LLM}


def test_search_hydrated_agent_does_not_clobber_model(context):
    """List/search hydration records provenance too, not just get()."""
    (agent,) = Agent._build_resources([{"id": "A1", "name": "agent"}], context)

    assert "model" not in agent.build_save_payload()


def test_absent_none_defaulted_roles_are_still_popped(context):
    """Roles defaulting to None keep their existing "omit the key" behaviour."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    payload = agent.build_save_payload()

    assert agent.supervisor is None
    for key in ("supervisor", "planner", "responder"):
        assert key not in payload


def test_clone_of_fetched_agent_sends_model(context):
    """A clone is a create: it forgets provenance and sends the full payload."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    cloned = agent.clone(name="copy")

    assert cloned.build_save_payload()["model"] == {"id": Agent.DEFAULT_LLM}


def test_update_payload_still_carries_server_model(context):
    """End-to-end: the PUT for a model-bearing agent is unchanged."""
    agent = _fetch(context, {"id": "A1", "name": "agent", "model": {"id": "SERVER-LLM"}})
    context.client.request.return_value = {"id": "A1", "name": "renamed"}

    agent.save(name="renamed")

    payload = context.client.request.call_args.kwargs["json"]
    assert payload["model"] == {"id": "SERVER-LLM"}


def test_update_payload_omits_model_for_model_less_agent(context):
    """End-to-end: renaming an agent fetched without "model" leaves it alone."""
    agent = _fetch(context, {"id": "A1", "name": "agent"})
    context.client.request.return_value = {"id": "A1", "name": "renamed"}

    agent.save(name="renamed")

    payload = context.client.request.call_args.kwargs["json"]
    assert "model" not in payload
