"""Unit tests for the v2 Trigger module (aixplain.v2.trigger)."""

import warnings
import pytest
from unittest.mock import Mock

from aixplain.v2.trigger import (
    Trigger,
    TriggerConfiguration,
    TriggerRepeatRule,
    _normalize_weekdays,
    _normalize_monthdays,
    _strip_none,
)
from aixplain.v2.integration import TriggerTypeSpec, TriggerEventOption, TriggerTypes
from aixplain.v2.resource import Page


AGENT_ID = "66a060000000000000000000"
MODEL_URL = "https://models.aixplain.com/api/v2/execute"


class FakeAgent:
    """Minimal agent stand-in with an id."""

    id = AGENT_ID


def make_context(client=None):
    """Build a mock Aixplain context with a client and model_url."""
    ctx = Mock()
    ctx.model_url = MODEL_URL
    ctx.client = client or Mock()
    return ctx


def bound_trigger_class(context):
    """Return a Trigger subclass bound to a context (as core.init_resources does)."""
    return type("Trigger", (Trigger,), {"context": context})


# =============================================================================
# Helpers
# =============================================================================


class TestNormalizers:
    def test_weekdays_codes_and_full_names(self):
        assert _normalize_weekdays(["mon", "Thursday", "SUN"]) == ["mon", "thu", "sun"]

    def test_weekdays_single_string(self):
        assert _normalize_weekdays("fri") == ["fri"]

    def test_weekdays_invalid(self):
        with pytest.raises(ValueError):
            _normalize_weekdays(["funday"])

    def test_monthdays_ok(self):
        assert _normalize_monthdays([1, "15", 31]) == [1, 15, 31]

    def test_monthdays_out_of_range(self):
        with pytest.raises(ValueError):
            _normalize_monthdays([0])
        with pytest.raises(ValueError):
            _normalize_monthdays([32])

    def test_strip_none_nested(self):
        assert _strip_none({"a": 1, "b": None, "c": {"d": None, "e": 2}}) == {"a": 1, "c": {"e": 2}}


# =============================================================================
# Schedule mapping -> configuration (the five story examples)
# =============================================================================


class TestScheduleMapping:
    def _cfg(self, **kw):
        return Trigger(name="t", agent=FakeAgent(), input="q", **kw).configuration

    def test_once(self):
        cfg = self._cfg(run_at="2026-01-26T12:00:00Z")
        assert cfg.type == "once" and cfg.run_at == "2026-01-26T12:00:00Z"

    def test_daily(self):
        cfg = self._cfg(every="day", at="09:00", timezone="Europe/London")
        assert cfg.type == "daily" and cfg.time == "09:00" and cfg.timezone == "Europe/London"

    def test_interval_hours(self):
        cfg = self._cfg(every="hour", interval=2)
        assert cfg.type == "recurring" and cfg.repeat.every == 2 and cfg.repeat.unit == "hour"

    def test_weekly(self):
        cfg = self._cfg(every="week", on=["mon", "thu"], at="17:00")
        assert cfg.type == "weekly" and cfg.days_of_week == ["mon", "thu"] and cfg.time == "17:00"

    def test_monthly(self):
        cfg = self._cfg(every="month", on=[1, 15], at="09:00")
        assert cfg.type == "monthly" and cfg.days_of_month == [1, 15] and cfg.time == "09:00"

    def test_day_interval_gt1_uses_recurring(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = self._cfg(every="day", interval=3, at="09:00")
        assert cfg.type == "recurring" and cfg.repeat.unit == "day" and cfg.repeat.every == 3

    def test_week_interval_gt1_uses_recurring(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = self._cfg(every="week", interval=2, on=["mon"])
        assert cfg.type == "recurring" and cfg.repeat.unit == "week"

    def test_start_at_on_recurring(self):
        cfg = self._cfg(every="minute", interval=5, start_at="2026-01-01T00:00:00Z")
        assert cfg.start_at == "2026-01-01T00:00:00Z"

    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(every="month", interval=2, on=[1]),
            dict(every="week", at="09:00"),  # missing on
            dict(every="month", at="09:00"),  # missing on
            dict(every="fortnight"),
        ],
    )
    def test_invalid_combos_raise(self, kwargs):
        with pytest.raises(ValueError):
            Trigger(name="t", agent=FakeAgent(), input="q", **kwargs)


# =============================================================================
# Payload building
# =============================================================================


class TestBuildSavePayload:
    def test_time_payload_defaults_enabled_true(self):
        p = Trigger(name="Daily", agent=FakeAgent(), input="Sum", every="day", at="09:00").build_save_payload()
        assert p["triggerType"] == "time"
        assert p["assetId"] == AGENT_ID and p["assetType"] == "agent"
        assert p["enabled"] is True and p["notifications"] is False
        assert p["configuration"] == {"type": "daily", "time": "09:00"}
        assert "id" not in p

    def test_notifications_and_enabled_passthrough(self):
        p = Trigger(
            name="x", agent=FakeAgent(), input="q", run_at="2026-01-26T12:00:00Z",
            notifications=True, enabled=False,
        ).build_save_payload()
        assert p["notifications"] is True and p["enabled"] is False

    def test_update_payload_includes_id(self):
        t = Trigger(name="x", agent=FakeAgent(), input="q", run_at="2026-01-26T12:00:00Z")
        t.id = "abc123"
        p = t.build_save_payload()
        assert p["id"] == "abc123"

    def test_external_payload_uses_trigger_id(self):
        opt = TriggerEventOption(slug="NEW_EMAIL", connection_id="conn1")
        t = Trigger(name="Triage", agent=FakeAgent(), input="Triage", event=opt)
        t.trigger_id = "ti_real"  # normally filled by activation
        p = t.build_save_payload()
        assert p["triggerType"] == "external" and p["triggerId"] == "ti_real"
        assert "configuration" not in p

    def test_time_trigger_without_schedule_raises(self):
        t = Trigger(name="x", agent=FakeAgent(), input="q")
        with pytest.raises(ValueError):
            t.build_save_payload()

    def test_update_payload_excludes_nested_next_run_at(self):
        t = Trigger.from_dict(
            {
                "id": "trig1",
                "name": "Hourly",
                "triggerType": "time",
                "configuration": {
                    "type": "recurring",
                    "nextRunAt": "2026-01-01T02:00:00Z",
                    "repeat": {"every": 2, "unit": "hour"},
                },
            }
        )

        assert t.next_run_at == "2026-01-01T02:00:00Z"
        assert "nextRunAt" not in t.build_save_payload()["configuration"]


# =============================================================================
# Rehydration (get/search deserialization)
# =============================================================================


class TestRehydration:
    def _dto(self, **over):
        dto = {
            "id": "trig1", "name": "Daily digest", "description": "d",
            "triggerType": "time", "assetId": AGENT_ID, "assetType": "agent",
            "type": "daily", "input": "Sum", "enabled": True, "notifications": False,
            "nextRunAt": "2026-07-14T09:00:00Z", "lastRunAt": None, "failureCount": 0,
            "enqueued": False, "createdAt": "2026-07-13T00:00:00Z", "updatedAt": "2026-07-13T00:00:00Z",
            "configuration": {"type": "daily", "time": "09:00", "timezone": "Europe/London", "repeat": None},
        }
        dto.update(over)
        return dto

    def test_from_dict_maps_fields(self):
        t = Trigger.from_dict(self._dto())
        assert t.id == "trig1" and t.asset_id == AGENT_ID and t.trigger_type == "time"
        assert t.schedule_type == "daily" and t.configuration.time == "09:00"
        assert t.timezone == "Europe/London" and t.at == "09:00"
        assert t.every == "day" and t.interval == 1
        assert t.next_run_at == "2026-07-14T09:00:00Z"

    @pytest.mark.parametrize(
        ("configuration", "expected"),
        [
            (
                {"type": "once", "runAt": "2026-01-01T00:00:00Z", "timezone": "UTC"},
                {"run_at": "2026-01-01T00:00:00Z", "timezone": "UTC"},
            ),
            (
                {"type": "weekly", "time": "17:00", "daysOfWeek": ["mon", "thu"]},
                {"every": "week", "at": "17:00", "on": ["mon", "thu"]},
            ),
            (
                {"type": "monthly", "time": "09:00", "daysOfMonth": [1, 15]},
                {"every": "month", "at": "09:00", "on": [1, 15]},
            ),
            (
                {
                    "type": "recurring",
                    "startAt": "2026-01-01T00:00:00Z",
                    "nextRunAt": "2026-01-01T02:00:00Z",
                    "repeat": {"every": 2, "unit": "hour"},
                },
                {
                    "every": "hour",
                    "interval": 2,
                    "start_at": "2026-01-01T00:00:00Z",
                    "next_run_at": "2026-01-01T02:00:00Z",
                },
            ),
        ],
    )
    def test_from_dict_hydrates_flat_schedule_fields(self, configuration, expected):
        t = Trigger.from_dict(self._dto(configuration=configuration, nextRunAt=None))

        assert t.schedule_type == configuration["type"]
        for attribute, value in expected.items():
            assert getattr(t, attribute) == value

    def test_rehydration_preserves_backend_enabled_value(self):
        # Rehydration must not apply the defaults used for locally constructed triggers.
        t = Trigger.from_dict(self._dto(enabled=False))
        assert t.enabled is False

    def test_external_rehydration_roundtrips_trigger_id(self):
        t = Trigger.from_dict(self._dto(triggerType="external", triggerId="ti_x", configuration=None, type=None))
        p = t.build_save_payload()
        assert p["triggerType"] == "external" and p["triggerId"] == "ti_x"


# =============================================================================
# search() -> GET /v1/triggers?agentId=
# =============================================================================


class TestSearch:
    def test_search_by_agent_sends_agentId_param(self):
        client = Mock()
        client.get.return_value = [
            {"id": "t1", "name": "a", "triggerType": "time", "assetId": AGENT_ID,
             "configuration": {"type": "once", "runAt": "2026-01-01T00:00:00Z"}},
            {"id": "t2", "name": "b", "triggerType": "time", "assetId": AGENT_ID,
             "configuration": {"type": "daily", "time": "09:00"}},
        ]
        cls = bound_trigger_class(make_context(client))
        page = cls.search(agent=FakeAgent())

        client.get.assert_called_once_with("v1/triggers", params={"agentId": AGENT_ID})
        assert isinstance(page, Page)
        assert page.total == 2 and page.page_total == 1
        assert [t.id for t in page.results] == ["t1", "t2"]

    def test_search_no_agent_omits_params(self):
        client = Mock()
        client.get.return_value = []
        cls = bound_trigger_class(make_context(client))
        page = cls.search()
        client.get.assert_called_once_with("v1/triggers")
        assert page.total == 0

    def test_search_agent_id_string(self):
        client = Mock()
        client.get.return_value = []
        cls = bound_trigger_class(make_context(client))
        cls.search(agent_id="deadbeef")
        client.get.assert_called_once_with("v1/triggers", params={"agentId": "deadbeef"})


# =============================================================================
# External activation on save + deactivation on delete
# =============================================================================


class TestEventLifecycle:
    def test_activation_called_on_create(self):
        client = Mock()
        # 1st call: activate_trigger -> returns composio trigger_id; 2nd: POST /v1/triggers
        client.request.side_effect = [
            {"completed": True, "data": {"trigger_id": "ti_activated"}},
            {"id": "trigNew", "name": "Triage", "triggerType": "external", "triggerId": "ti_activated"},
        ]
        ctx = make_context(client)
        opt = TriggerEventOption(slug="NEW_EMAIL", connection_id="conn1")
        t = Trigger(name="Triage", agent=FakeAgent(), input="Triage", event=opt)
        t.context = ctx
        t.save()

        # First request = activation on the connection's execute URL
        first = client.request.call_args_list[0]
        assert first.args[0] == "post"
        assert first.args[1] == f"{MODEL_URL}/conn1"
        body = first.kwargs["json"]
        assert body["action"] == "activate_trigger"
        assert body["data"] == {"slug": "NEW_EMAIL", "config": {}}
        assert body["enable"] is True and body["toolkit_versions"] == "latest"

        # Second request = create on /v1/triggers with the real trigger id
        second = client.request.call_args_list[1]
        assert second.args[0] == "post" and second.args[1] == "v1/triggers"
        assert second.kwargs["json"]["triggerId"] == "ti_activated"
        assert t.trigger_id == "ti_activated" and t.id == "trigNew"

    def test_activation_without_connection_raises(self):
        opt = TriggerEventOption(slug="NEW_EMAIL")  # no connection_id
        t = Trigger(name="Triage", agent=FakeAgent(), input="Triage", event=opt)
        t.context = make_context()
        with pytest.raises(ValueError):
            t.save()

    def test_delete_deactivates_composio(self):
        client = Mock()
        client.request.return_value = {"completed": True, "data": {"deleted": True}}
        client.request_raw.return_value = Mock()
        ctx = make_context(client)
        t = Trigger.from_dict({"id": "trigX", "name": "e", "triggerType": "external", "triggerId": "ti_x"})
        t.context = ctx
        t.connection_id = "conn1"  # known in-session
        t.delete()

        deact = client.request.call_args_list[0]
        assert deact.kwargs["json"]["action"] == "delete_trigger"
        assert deact.kwargs["json"]["data"] == {"trigger_id": "ti_x"}
        client.request_raw.assert_called_once()
        assert client.request_raw.call_args.args[0] == "delete"

    def test_delete_external_without_connection_warns(self):
        client = Mock()
        client.request_raw.return_value = Mock()
        ctx = make_context(client)
        t = Trigger.from_dict({"id": "trigX", "name": "e", "triggerType": "external", "triggerId": "ti_x"})
        t.context = ctx
        with pytest.warns(UserWarning):
            t.delete()
        client.request.assert_not_called()  # no deactivation attempted


# =============================================================================
# Discovery collection (integration.triggers / tool.triggers)
# =============================================================================


class TestTriggerTypesCollection:
    def _specs(self):
        return [
            TriggerTypeSpec(slug="NEW_EMAIL", name="New email", description="fires on email"),
            TriggerTypeSpec(slug="NEW_LABEL", name="New label"),
        ]

    def test_getitem_case_insensitive(self):
        col = TriggerTypes(self._specs(), connection_id="conn1")
        opt = col["new_email"]
        assert isinstance(opt, TriggerEventOption)
        assert opt.slug == "NEW_EMAIL" and opt.connection_id == "conn1"

    def test_contains_and_len_and_iter(self):
        col = TriggerTypes(self._specs())
        assert "NEW_EMAIL" in col and "nope" not in col
        assert len(col) == 2
        assert set(iter(col)) == {"NEW_EMAIL", "NEW_LABEL"}

    def test_missing_raises_keyerror(self):
        col = TriggerTypes(self._specs())
        with pytest.raises(KeyError):
            col["DOES_NOT_EXIST"]

    def test_discovery_only_has_no_connection(self):
        col = TriggerTypes(self._specs())  # from an unconnected integration
        assert col["NEW_EMAIL"].connection_id is None
