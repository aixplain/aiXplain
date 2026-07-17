"""Functional tests for v2 Triggers (aix.Trigger).

Time-trigger tests run with only TEAM_API_KEY/AIXPLAIN_API_KEY set (a temporary
agent is created and cleaned up). Event-trigger tests are gated on extra env vars:

- TEST_COMPOSIO_INTEGRATION_ID : an integration id (e.g. composio/gmail resolved id)
                                 used for `integration.triggers` discovery.
- TEST_CONNECTION_ID           : a connected tool id used to activate a real event
                                 trigger end-to-end.
"""

import os
import time

import pytest

from aixplain.v2 import Trigger, TriggerEventOption
from aixplain.v2.resource import Page


# Far-future instant so a "once" trigger is valid/schedulable.
FUTURE_RUN_AT = "2099-01-26T12:00:00Z"


@pytest.fixture(scope="module")
def test_agent(client):
    """Create a temporary agent to attach triggers to, and clean it up."""
    agent = client.Agent(
        name=f"Trigger Functional Agent {int(time.time())}",
        description="Temporary agent for trigger functional tests",
        instructions="You are a helpful test agent. Respond briefly.",
    )
    agent.save()
    yield agent
    try:
        agent.delete()
    except Exception:
        pass


@pytest.fixture
def cleanup_triggers():
    """Collect triggers created during a test and delete them afterwards."""
    created = []
    yield created
    for t in created:
        try:
            t.delete()
        except Exception:
            pass


@pytest.fixture(scope="module")
def composio_integration_id():
    """Integration id for event-discovery tests (skips if not provided)."""
    value = os.getenv("TEST_COMPOSIO_INTEGRATION_ID")
    if not value:
        pytest.skip("TEST_COMPOSIO_INTEGRATION_ID is required for event-discovery tests")
    return value


@pytest.fixture(scope="module")
def connection_id():
    """Connected tool id for end-to-end event-trigger tests (skips if not provided)."""
    value = os.getenv("TEST_CONNECTION_ID")
    if not value:
        pytest.skip("TEST_CONNECTION_ID is required for event-trigger activation tests")
    return value


# =============================================================================
# Time triggers
# =============================================================================


class TestTimeTriggerLifecycle:
    def test_create_once_trigger(self, client, test_agent, cleanup_triggers):
        """A one-off (run_at) trigger is created and enabled by default."""
        t = client.Trigger(
            name=f"once-{int(time.time())}",
            agent=test_agent,
            input="Remind the team about the launch.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        cleanup_triggers.append(t)

        assert t.id is not None
        assert t.trigger_type == "time"
        assert t.schedule_type == "once"
        assert t.enabled is True

    def test_create_daily_trigger(self, client, test_agent, cleanup_triggers):
        """A daily trigger maps at/timezone onto a daily schedule."""
        t = client.Trigger(
            name=f"daily-{int(time.time())}",
            agent=test_agent,
            input="Summarise today's AI news.",
            every="day",
            at="09:00",
            timezone="Europe/London",
            notifications=True,
        )
        t.save()
        cleanup_triggers.append(t)

        assert t.id is not None
        assert t.schedule_type == "daily"
        assert t.notifications is True

    def test_create_interval_and_weekly_and_monthly(self, client, test_agent, cleanup_triggers):
        """Interval, weekly, and monthly schedules all create successfully."""
        hourly = client.Trigger(
            name=f"hourly-{int(time.time())}", agent=test_agent, input="Check the queue.",
            every="hour", interval=2,
        )
        hourly.save()
        cleanup_triggers.append(hourly)
        assert hourly.schedule_type == "recurring"

        weekly = client.Trigger(
            name=f"weekly-{int(time.time())}", agent=test_agent, input="Compile the weekly report.",
            every="week", on=["mon", "thu"], at="17:00",
        )
        weekly.save()
        cleanup_triggers.append(weekly)
        assert weekly.schedule_type == "weekly"

        monthly = client.Trigger(
            name=f"monthly-{int(time.time())}", agent=test_agent, input="Generate invoices.",
            every="month", on=[1, 15], at="09:00",
        )
        monthly.save()
        cleanup_triggers.append(monthly)
        assert monthly.schedule_type == "monthly"

    def test_get_trigger(self, client, test_agent, cleanup_triggers):
        """Trigger.get(id) retrieves a created trigger."""
        t = client.Trigger(
            name=f"get-{int(time.time())}", agent=test_agent, input="Ping.", run_at=FUTURE_RUN_AT,
        )
        t.save()
        cleanup_triggers.append(t)

        fetched = client.Trigger.get(t.id)
        assert fetched.id == t.id
        assert fetched.name == t.name
        assert fetched.trigger_type == "time"
        assert fetched.schedule_type == "once"

    def test_search_by_agent(self, client, test_agent, cleanup_triggers):
        """Trigger.search(agent=) returns a Page containing the agent's triggers."""
        t = client.Trigger(
            name=f"search-{int(time.time())}", agent=test_agent, input="Ping.", run_at=FUTURE_RUN_AT,
        )
        t.save()
        cleanup_triggers.append(t)

        page = client.Trigger.search(agent=test_agent)
        assert isinstance(page, Page)
        ids = [item.id for item in page.results]
        assert t.id in ids
        for item in page.results:
            assert isinstance(item, Trigger)
            assert item.asset_id == test_agent.id

    def test_enable_disable_via_save(self, client, test_agent, cleanup_triggers):
        """Setting enabled=False and saving disables the trigger."""
        t = client.Trigger(
            name=f"toggle-{int(time.time())}", agent=test_agent, input="Ping.", run_at=FUTURE_RUN_AT,
        )
        t.save()
        cleanup_triggers.append(t)
        assert t.enabled is True

        t.enabled = False
        t.save()
        assert client.Trigger.get(t.id).enabled is False

        t.enabled = True
        t.save()
        assert client.Trigger.get(t.id).enabled is True

    def test_delete_trigger(self, client, test_agent):
        """delete() removes the trigger."""
        t = client.Trigger(
            name=f"delete-{int(time.time())}", agent=test_agent, input="Ping.", run_at=FUTURE_RUN_AT,
        )
        t.save()
        trigger_id = t.id

        t.delete()

        with pytest.raises(Exception):
            client.Trigger.get(trigger_id)


# =============================================================================
# Event triggers
# =============================================================================


class TestEventTriggerDiscovery:
    def test_integration_triggers_lists_options(self, client, composio_integration_id):
        """integration.triggers lists available event options (like .actions)."""
        integration = client.Integration.get(composio_integration_id)
        triggers = integration.triggers

        # Browsable collection: len / iterate / membership / indexing.
        assert len(triggers) >= 0
        slugs = list(triggers)
        for slug in slugs:
            assert isinstance(slug, str)
        if slugs:
            option = triggers[slugs[0]]
            assert isinstance(option, TriggerEventOption)
            assert option.slug == slugs[0]
            # Discovery from an (unconnected) integration carries no connection.
            assert option.connection_id is None


class TestEventTriggerLifecycle:
    def test_create_and_delete_event_trigger(self, client, test_agent, connection_id):
        """Create a real Composio event trigger from a connected tool and delete it."""
        tool = client.Tool.get(connection_id)

        slugs = list(tool.triggers)
        if not slugs:
            pytest.skip("Connected tool exposes no trigger types")
        option = tool.triggers[slugs[0]]
        assert option.connection_id == tool.id  # connected tool carries the connection

        t = client.Trigger(
            name=f"event-{int(time.time())}",
            agent=test_agent,
            input="Handle this event.",
            event=option,
        )
        try:
            t.save()
            assert t.id is not None
            assert t.trigger_type == "external"
            # Activation filled in the real Composio trigger id.
            assert t.trigger_id
        finally:
            try:
                t.delete()
            except Exception:
                pass
