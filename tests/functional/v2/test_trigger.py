"""Functional tests for v2 Triggers (aix.Trigger).

Time-trigger tests run with only TEAM_API_KEY/AIXPLAIN_API_KEY set (a temporary
agent is created and cleaned up). Event-trigger tests need two more things, and
neither is a secret:

- the Composio Gmail integration, fetched by its marketplace path
  (``COMPOSIO_GMAIL_PATH``, which resolves on every backend), for
  ``integration.triggers`` discovery;
- a connected tool that lists event-trigger types, found by
  ``resolve_trigger_connection`` (pin one with AIXPLAIN_TEST_TRIGGER_CONNECTION_ID),
  to activate a real event trigger end to end.

Both used to come from TEST_COMPOSIO_INTEGRATION_ID / TEST_CONNECTION_ID, and
skipped when unset, which meant the event-trigger half of this file had never
run in CI and nobody could tell (ENG-3684). A missing integration or connection
fails now: it is a broken environment, not a smaller test suite.
"""

import time
import uuid

import pytest

from aixplain import Trigger, TriggerEventOption
from aixplain import Page

from tests.functional._helpers import resolve_trigger_connection


# Far-future instant so a "once" trigger is valid/schedulable.
FUTURE_RUN_AT = "2099-01-26T12:00:00Z"

# Recurring triggers are created disabled. Teardown deletes them, but a PR run
# cancelled by a newer push (`cancel-in-progress`) can skip teardown, and an
# enabled recurring trigger left behind would keep running its agent on the
# shared backend. The schedule mapping these tests check does not depend on it.
RECURRING_ENABLED = False

#: The Composio integration whose event triggers these tests use, by marketplace
#: path: ``Integration.get`` resolves a path on every backend, so unlike an
#: ObjectId it needs no per-environment entry in tests/functional/_assets.py.
COMPOSIO_GMAIL_PATH = "composio/gmail"


@pytest.fixture(scope="module")
def test_agent(client, module_resource_tracker):
    """Create a temporary agent to attach triggers to, and clean it up."""
    agent = client.Agent(
        name=f"Trigger Functional Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        description="Temporary agent for trigger functional tests",
        instructions="You are a helpful test agent. Respond briefly.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


@pytest.fixture(scope="module")
def composio_integration_id(client):
    """The Composio Gmail integration's id on this backend, for event-discovery tests."""
    return client.Integration.get(COMPOSIO_GMAIL_PATH).id


@pytest.fixture(scope="module")
def connection_id(client, composio_integration_id):
    """A connected tool with event-trigger types, looked up once per module; fails the test when none exists."""
    return resolve_trigger_connection(client, composio_integration_id).id


# =============================================================================
# Time triggers
# =============================================================================


class TestTimeTriggerLifecycle:
    def test_create_once_trigger(self, client, test_agent, resource_tracker):
        """A one-off (run_at) trigger is created and enabled by default."""
        t = client.Trigger(
            name=f"once-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Remind the team about the launch.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        resource_tracker.append(t)

        assert t.id is not None
        assert t.trigger_type == "time"
        assert t.schedule_type == "once"
        assert t.enabled is True

    def test_create_daily_trigger(self, client, test_agent, resource_tracker):
        """A daily trigger maps at/timezone onto a daily schedule."""
        t = client.Trigger(
            name=f"daily-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Summarise today's AI news.",
            every="day",
            at="09:00",
            timezone="Europe/London",
            notifications=True,
            enabled=RECURRING_ENABLED,
        )
        t.save()
        resource_tracker.append(t)

        assert t.id is not None
        assert t.schedule_type == "daily"
        assert t.notifications is True

    def test_create_interval_and_weekly_and_monthly(self, client, test_agent, resource_tracker):
        """Interval, weekly, and monthly schedules all create successfully."""
        hourly = client.Trigger(
            name=f"hourly-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Check the queue.",
            every="hour",
            interval=2,
            enabled=RECURRING_ENABLED,
        )
        hourly.save()
        resource_tracker.append(hourly)
        assert hourly.schedule_type == "recurring"
        # The most frequent schedule here: make sure the backend stored it disabled.
        assert client.Trigger.get(hourly.id).enabled is False

        weekly = client.Trigger(
            name=f"weekly-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Compile the weekly report.",
            every="week",
            on=["mon", "thu"],
            at="17:00",
            enabled=RECURRING_ENABLED,
        )
        weekly.save()
        resource_tracker.append(weekly)
        assert weekly.schedule_type == "weekly"

        monthly = client.Trigger(
            name=f"monthly-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Generate invoices.",
            every="month",
            on=[1, 15],
            at="09:00",
            enabled=RECURRING_ENABLED,
        )
        monthly.save()
        resource_tracker.append(monthly)
        assert monthly.schedule_type == "monthly"

    def test_get_trigger(self, client, test_agent, resource_tracker):
        """Trigger.get(id) retrieves a created trigger."""
        t = client.Trigger(
            name=f"get-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Ping.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        resource_tracker.append(t)

        fetched = client.Trigger.get(t.id)
        assert fetched.id == t.id
        assert fetched.name == t.name
        assert fetched.trigger_type == "time"
        assert fetched.schedule_type == "once"

    def test_search_by_agent(self, client, test_agent, resource_tracker):
        """Trigger.search(agent=) returns a Page containing the agent's triggers."""
        t = client.Trigger(
            name=f"search-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Ping.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        resource_tracker.append(t)

        page = client.Trigger.search(agent=test_agent)
        assert isinstance(page, Page)
        ids = [item.id for item in page.results]
        assert t.id in ids
        for item in page.results:
            assert isinstance(item, Trigger)
            assert item.asset_id == test_agent.id

    def test_enable_disable_via_save(self, client, test_agent, resource_tracker):
        """Setting enabled=False and saving disables the trigger."""
        t = client.Trigger(
            name=f"toggle-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Ping.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        resource_tracker.append(t)
        assert t.enabled is True

        t.enabled = False
        t.save()
        assert client.Trigger.get(t.id).enabled is False

        t.enabled = True
        t.save()
        assert client.Trigger.get(t.id).enabled is True

    def test_delete_trigger(self, client, test_agent, resource_tracker):
        """delete() removes the trigger."""
        t = client.Trigger(
            name=f"delete-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Ping.",
            run_at=FUTURE_RUN_AT,
        )
        t.save()
        resource_tracker.append(t)
        trigger_id = t.id

        t.delete()
        resource_tracker.mark_cleaned(t)

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
    def test_create_and_delete_event_trigger(self, client, test_agent, connection_id, resource_tracker):
        """Create a real Composio event trigger from a connected tool and delete it."""
        tool = client.Tool.get(connection_id)

        slugs = list(tool.triggers)
        # The connection was chosen *because* it lists trigger types, so an
        # empty `triggers` here disagrees with the `list_trigger_types` probe.
        assert slugs, (
            f"Connected tool {tool.id} listed trigger types when it was resolved but exposes none "
            "through `tool.triggers`."
        )
        option = tool.triggers[slugs[0]]
        assert option.connection_id == tool.id  # connected tool carries the connection

        t = client.Trigger(
            name=f"event-{int(time.time())}-{uuid.uuid4().hex[:6]}",
            agent=test_agent,
            input="Handle this event.",
            event=option,
        )
        t.save()
        resource_tracker.append(t)
        assert t.id is not None
        assert t.trigger_type == "external"
        # Activation filled in the real Composio trigger id.
        assert t.trigger_id
