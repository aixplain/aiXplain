"""Regression tests for the LLM-overwrite bug (0.2.43/0.2.44).

On those releases ``Agent.get()`` never decoded the ``model`` field from the
API response, so a fetched agent's ``llm`` silently fell back to
``Agent.DEFAULT_LLM`` and the next ``save()`` — even one that only touched
``instructions`` — overwrote the agent's configured LLM with the default.
These tests fail loudly if either the fetch or the fetch→save round-trip
loses a non-default LLM again.
"""

import time

import pytest

def llm_ref_id(llm):
    """Normalize an ``agent.llm`` value (str id, role-ref dict, or Model) to its id."""
    if llm is None:
        return None
    if isinstance(llm, str):
        return llm
    if isinstance(llm, dict):
        return llm.get("id")
    return getattr(llm, "id", None)


@pytest.fixture(scope="module")
def non_default_llm_id(assets):
    """A stable LLM that is not ``Agent.DEFAULT_LLM``."""
    return assets.NON_DEFAULT_LLM


@pytest.fixture(scope="module")
def non_default_llm_agent(client, non_default_llm_id):
    """Create an agent pinned to a non-default LLM, cleaned up after tests."""
    assert non_default_llm_id != client.Agent.DEFAULT_LLM, "test LLM must not be the default"
    agent = client.Agent(
        name=f"LLM Persistence Test Agent {int(time.time())}",
        description="Temporary agent verifying the LLM survives fetch/save round-trips",
        instructions="You are a helpful test agent.",
        llm=non_default_llm_id,
    )
    agent.save()

    yield agent

    try:
        agent.delete()
    except Exception:
        pass


class TestAgentLlmPersistence:
    def test_create_persists_non_default_llm(self, client, non_default_llm_agent, non_default_llm_id):
        """The LLM passed at creation must be what the backend stores."""
        fetched = client.Agent.get(non_default_llm_agent.id)
        assert llm_ref_id(fetched.llm) == non_default_llm_id

    def test_fetched_agent_does_not_fall_back_to_default_llm(self, client, non_default_llm_agent, non_default_llm_id):
        """``Agent.get()`` must decode the stored LLM, not fall back to DEFAULT_LLM.

        This is the read half of the regression: on 0.2.43/0.2.44 the fetched
        agent's ``llm`` was always ``DEFAULT_LLM`` regardless of the record.
        """
        fetched = client.Agent.get(non_default_llm_agent.id)
        assert llm_ref_id(fetched.llm) != client.Agent.DEFAULT_LLM
        # The save payload built from a fetched agent must echo the stored LLM.
        payload_model = fetched.build_save_payload().get("model") or {}
        assert payload_model.get("id") == non_default_llm_id

    def test_instructions_only_save_preserves_llm(self, client, non_default_llm_agent, non_default_llm_id):
        """fetch → edit instructions → save must not clobber the agent's LLM.

        This is the write half of the regression: the exact user flow that
        silently reset agents to GPT-5.4 on 0.2.43/0.2.44.
        """
        fetched = client.Agent.get(non_default_llm_agent.id)
        fetched.instructions = "You are a helpful test agent. (edited)"
        fetched.save()

        refetched = client.Agent.get(non_default_llm_agent.id)
        assert refetched.instructions == "You are a helpful test agent. (edited)"
        assert llm_ref_id(refetched.llm) == non_default_llm_id, (
            "instructions-only save() overwrote the agent's LLM — "
            "DEFAULT_LLM fallback regression (see 0.2.43/0.2.44)"
        )

    def test_explicit_llm_update_persists(self, client, non_default_llm_agent, non_default_llm_id):
        """Explicitly changing ``agent.llm`` on a fetched agent must persist."""
        fetched = client.Agent.get(non_default_llm_agent.id)
        fetched.llm = client.Agent.DEFAULT_LLM
        fetched.save()
        assert llm_ref_id(client.Agent.get(non_default_llm_agent.id).llm) == client.Agent.DEFAULT_LLM

        # restore the non-default LLM and confirm the flip back also persists
        fetched.llm = non_default_llm_id
        fetched.save()
        assert llm_ref_id(client.Agent.get(non_default_llm_agent.id).llm) == non_default_llm_id
