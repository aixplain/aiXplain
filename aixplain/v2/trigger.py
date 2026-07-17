"""Trigger management module for the aiXplain v2 API.

A :class:`Trigger` fires an agent with an ``input`` (the query) either on a time
schedule (once / daily / weekly / monthly / interval) or on an external event
(e.g. a Composio integration event such as a new Gmail email).

Time triggers map straight onto ``POST/GET/PUT/DELETE /v1/triggers``. Event
triggers are orchestrated over the existing endpoints: the SDK activates the
Composio trigger on a connected tool via the model-execute endpoint (the same
mechanism used by ``integration.actions``), then persists the returned trigger id
through ``/v1/triggers``.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config as dj_config
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .resource import (
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    DeleteResult,
    Page,
    BaseSearchParams,
    BaseGetParams,
    BaseDeleteParams,
)
from .exceptions import ResourceError

if TYPE_CHECKING:
    from .core import Aixplain


# Backend-accepted string values (see platform-backend src/trigger/enums).
_SCHEDULE_TYPES = {"once", "daily", "weekly", "monthly", "recurring"}
_TIME_UNITS = {"minute", "hour", "day", "week"}  # NOTE: no "month" unit on the backend
_WEEKDAYS = {"sun", "mon", "tue", "wed", "thu", "fri", "sat"}
_WEEKDAY_ALIASES = {
    "sunday": "sun",
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
}


def _strip_none(data: Any) -> Any:
    """Recursively drop ``None`` values from dicts/lists for clean payloads."""
    if isinstance(data, dict):
        return {k: _strip_none(v) for k, v in data.items() if v is not None}
    if isinstance(data, list):
        return [_strip_none(v) for v in data]
    return data


def _normalize_weekdays(value: Any) -> List[str]:
    """Normalize ``on=`` weekdays to backend codes (``mon``..``sun``)."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    days: List[str] = []
    for raw in value:
        key = str(raw).strip().lower()
        key = _WEEKDAY_ALIASES.get(key, key[:3])
        if key not in _WEEKDAYS:
            raise ValueError(f"Invalid weekday {raw!r}; use one of {sorted(_WEEKDAYS)} (or full names).")
        days.append(key)
    return days


def _normalize_monthdays(value: Any) -> List[int]:
    """Normalize ``on=`` days-of-month to ints in ``1..31``."""
    if value is None:
        return []
    if isinstance(value, (int, str)):
        value = [value]
    days: List[int] = []
    for raw in value:
        try:
            day = int(raw)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid day-of-month {raw!r}; expected an integer 1-31.")
        if not 1 <= day <= 31:
            raise ValueError(f"Invalid day-of-month {day}; must be between 1 and 31.")
        days.append(day)
    return days


@dataclass_json
@dataclass
class TriggerRepeatRule:
    """Interval rule for a ``recurring`` schedule (e.g. every 2 hours)."""

    every: Optional[int] = None
    unit: Optional[str] = None


@dataclass_json
@dataclass
class TriggerConfiguration:
    """Structured time-schedule configuration (mirrors the backend config)."""

    type: Optional[str] = None
    time: Optional[str] = None
    timezone: Optional[str] = None
    days_of_week: Optional[List[str]] = field(default=None, metadata=dj_config(field_name="daysOfWeek"))
    days_of_month: Optional[List[int]] = field(default=None, metadata=dj_config(field_name="daysOfMonth"))
    run_at: Optional[str] = field(default=None, metadata=dj_config(field_name="runAt"))
    start_at: Optional[str] = field(default=None, metadata=dj_config(field_name="startAt"))
    repeat: Optional[TriggerRepeatRule] = None


class TriggerSearchParams(BaseSearchParams):
    """Search parameters for triggers (filter by agent)."""

    pass


class TriggerGetParams(BaseGetParams):
    """Get parameters for triggers."""

    pass


class TriggerDeleteParams(BaseDeleteParams):
    """Delete parameters for triggers."""

    pass


@dataclass_json
@dataclass(repr=False)
class Trigger(
    BaseResource,
    SearchResourceMixin[TriggerSearchParams, "Trigger"],
    GetResourceMixin[TriggerGetParams, "Trigger"],
    DeleteResourceMixin[TriggerDeleteParams, DeleteResult],
):
    """A schedule/event trigger that fires an agent with a fixed input.

    Time trigger examples::

        aix.Trigger(name="Launch reminder", agent=agent, input="Remind the team.",
                    run_at="2026-01-26T12:00:00Z").save()                       # once
        aix.Trigger(name="Daily digest", agent=agent, input="Summarise the news.",
                    every="day", at="09:00", timezone="Europe/London").save()   # daily
        aix.Trigger(name="Hourly check", agent=agent, input="Check the queue.",
                    every="hour", interval=2).save()                            # every 2 hours
        aix.Trigger(name="Weekly report", agent=agent, input="Compile the report.",
                    every="week", on=["mon", "thu"], at="17:00").save()         # weekly
        aix.Trigger(name="Invoice run", agent=agent, input="Generate invoices.",
                    every="month", on=[1, 15], at="09:00").save()               # monthly

    Event trigger example (requires a connected tool)::

        gmail = aix.Integration.get("composio/gmail")
        tool = gmail.connect(...)
        aix.Trigger(name="Triage inbox", agent=agent, input="Triage this email.",
                    event=tool.triggers["NEW_EMAIL"]).save()

    Manage::

        t = aix.Trigger.get("<id>")
        aix.Trigger.search(agent=agent)     # -> Page
        t.enabled = False; t.save()         # disable (re-enable with True)
        t.delete()
    """

    RESOURCE_PATH = "v1/triggers"

    # Simple list endpoint: GET /v1/triggers?agentId=  (no /paginate suffix)
    PAGINATE_PATH = ""
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None  # bare array response

    # --- Backend-shaped, persisted fields (round-tripped via from_dict/to_dict) ---
    input: Optional[str] = None
    asset_id: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    asset_type: Optional[str] = field(default="agent", metadata=dj_config(field_name="assetType"))
    trigger_type: Optional[str] = field(default=None, metadata=dj_config(field_name="triggerType"))
    trigger_id: Optional[str] = field(default=None, metadata=dj_config(field_name="triggerId"))
    configuration: Optional[TriggerConfiguration] = None
    enabled: Optional[bool] = None
    notifications: Optional[bool] = None
    retry_count: Optional[int] = field(default=None, metadata=dj_config(field_name="retryCount"))

    # Read-only backend fields (never sent; excluded from payload).
    next_run_at: Optional[str] = field(default=None, metadata=dj_config(field_name="nextRunAt", exclude=lambda x: True))
    last_run_at: Optional[str] = field(default=None, metadata=dj_config(field_name="lastRunAt", exclude=lambda x: True))
    enqueued: Optional[bool] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    created_at: Optional[str] = field(default=None, metadata=dj_config(field_name="createdAt", exclude=lambda x: True))
    updated_at: Optional[str] = field(default=None, metadata=dj_config(field_name="updatedAt", exclude=lambda x: True))

    # Local-only fields for the event lifecycle (not returned by the REST DTO).
    connection_id: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    trigger_slug: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))

    # --- Friendly, init-only kwargs (never serialized; translated in __post_init__) ---
    agent: Optional[Any] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    run_at: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    every: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    interval: int = field(default=1, metadata=dj_config(exclude=lambda x: True))
    at: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    on: Optional[Any] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    timezone: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    start_at: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    event: Optional[Any] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    event_config: Optional[Dict[str, Any]] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    connection: Optional[Any] = field(default=None, metadata=dj_config(exclude=lambda x: True))

    def __post_init__(self) -> None:
        """Translate friendly construction kwargs into backend-shaped fields.

        Skipped when rehydrating from the backend (``id`` already set), so that
        ``from_dict`` in get/search/create is left untouched.
        """
        if self.id is not None:
            return  # rehydration path — nothing to translate

        # Resolve the target agent -> assetId.
        if self.agent is not None and not self.asset_id:
            self.asset_id = getattr(self.agent, "id", None) or self.agent
            self.asset_type = "agent"

        # New triggers default to enabled so they fire on schedule.
        if self.enabled is None:
            self.enabled = True
        if self.notifications is None:
            self.notifications = False

        if self.event is not None:
            self._configure_from_event()
        elif self.run_at is not None or self.every is not None or self.start_at is not None:
            self.trigger_type = "time"
            self.configuration = self._build_configuration()

    # ------------------------------------------------------------------
    # Event configuration
    # ------------------------------------------------------------------

    def _configure_from_event(self) -> None:
        """Capture slug / config / connection from an event option."""
        self.trigger_type = "external"
        self.trigger_slug = getattr(self.event, "slug", None) or getattr(self.event, "name", None)
        if not self.trigger_slug:
            raise ValueError("event= must be a trigger option from integration.triggers/tool.triggers.")
        if self.event_config is None:
            self.event_config = getattr(self.event, "values", None) or {}
        # Resolve a connection id for activation.
        if self.connection is not None:
            self.connection_id = getattr(self.connection, "id", None) or self.connection
        if not self.connection_id:
            self.connection_id = getattr(self.event, "connection_id", None)

    # ------------------------------------------------------------------
    # Schedule mapping (friendly kwargs -> backend configuration)
    # ------------------------------------------------------------------

    def _build_configuration(self) -> TriggerConfiguration:
        """Map the schedule kwargs to a backend ``TriggerConfiguration``.

        Uses the *semantic* schedule types (daily/weekly/monthly) whenever a
        time-of-day (``at``) or day selection (``on``) is given, because the
        backend scheduler only honours those on the semantic types; the generic
        ``recurring`` type ignores them and has no ``month`` unit.
        """
        tz = self.timezone
        if self.run_at is not None:
            return TriggerConfiguration(type="once", run_at=self.run_at, timezone=tz)

        every = (self.every or "").strip().lower()
        interval = int(self.interval or 1)
        if not every:
            raise ValueError("Provide run_at=... for a one-off trigger, or every=... for a recurring one.")

        if every in ("minute", "hour"):
            return TriggerConfiguration(
                type="recurring",
                timezone=tz,
                start_at=self.start_at,
                repeat=TriggerRepeatRule(every=interval, unit=every),
            )

        if every == "day":
            if self.at is not None and interval == 1:
                return TriggerConfiguration(type="daily", time=self.at, timezone=tz)
            if self.at is not None and interval > 1:
                warnings.warn(
                    "`at` (time-of-day) is ignored for every='day' with interval>1; "
                    "the backend fires every N days relative to creation time.",
                    stacklevel=2,
                )
            return TriggerConfiguration(
                type="recurring",
                timezone=tz,
                start_at=self.start_at,
                repeat=TriggerRepeatRule(every=interval, unit="day"),
            )

        if every == "week":
            if interval > 1:
                warnings.warn(
                    "`on`/`at` are ignored for every='week' with interval>1; "
                    "the backend fires every N weeks relative to creation time.",
                    stacklevel=2,
                )
                return TriggerConfiguration(
                    type="recurring",
                    timezone=tz,
                    start_at=self.start_at,
                    repeat=TriggerRepeatRule(every=interval, unit="week"),
                )
            days = _normalize_weekdays(self.on)
            if not days:
                raise ValueError('Weekly triggers require on=[...] weekdays, e.g. on=["mon", "thu"].')
            return TriggerConfiguration(type="weekly", days_of_week=days, time=self.at, timezone=tz)

        if every == "month":
            if interval > 1:
                raise ValueError("Monthly triggers don't support interval>1 (the backend has no month interval unit).")
            days = _normalize_monthdays(self.on)
            if not days:
                raise ValueError("Monthly triggers require on=[...] day numbers, e.g. on=[1, 15].")
            return TriggerConfiguration(type="monthly", days_of_month=days, time=self.at, timezone=tz)

        raise ValueError(f"Unknown every={self.every!r}; use one of minute/hour/day/week/month.")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def before_save(self, *args: Any, **kwargs: Any) -> None:
        """Activate the Composio trigger before persisting a new event trigger."""
        if not self.id and self.trigger_type == "external" and not self.trigger_id:
            self._activate_event()
        return None

    def build_save_payload(self, **kwargs: Any) -> Dict[str, Any]:
        """Build the whitelisted payload for ``POST``/``PUT`` /v1/triggers.

        The backend uses ``forbidNonWhitelisted`` validation, so only the fields
        accepted by ``TriggerInput`` are sent (never read-only fields).
        """
        trigger_type = self.trigger_type or "time"
        payload: Dict[str, Any] = {
            "name": self.name,
            "input": self.input,
            "assetType": self.asset_type or "agent",
            "triggerType": trigger_type,
            "enabled": bool(self.enabled),
            "notifications": bool(self.notifications),
        }
        if self.id:
            payload["id"] = self.id
        if self.description is not None:
            payload["description"] = self.description
        if self.asset_id:
            payload["assetId"] = self.asset_id
        if self.retry_count is not None:
            payload["retryCount"] = self.retry_count

        if trigger_type == "external":
            payload["triggerId"] = self.trigger_id
        elif self.configuration is not None:
            payload["configuration"] = _strip_none(self.configuration.to_dict())
        else:
            raise ValueError(
                "A time trigger needs a schedule. Pass run_at=... (one-off) or "
                "every=... (recurring) when constructing the Trigger."
            )

        return payload

    # ------------------------------------------------------------------
    # Search (GET /v1/triggers?agentId=)
    # ------------------------------------------------------------------

    @classmethod
    def search(cls, agent: Optional[Any] = None, agent_id: Optional[str] = None, **kwargs: Any) -> Page["Trigger"]:
        """List triggers for the team, optionally filtered by agent.

        Args:
            agent: An Agent instance (or anything with ``.id``) to filter by.
            agent_id: An agent id string to filter by.
            **kwargs: Additional options forwarded to page building (e.g. ``page_number``).

        Returns:
            Page[Trigger]
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for resource listing")

        resolved_agent_id = agent_id
        if resolved_agent_id is None and agent is not None:
            resolved_agent_id = getattr(agent, "id", None) or agent

        request_kwargs: Dict[str, Any] = {}
        if resolved_agent_id:
            request_kwargs["params"] = {"agentId": resolved_agent_id}

        response = context.client.get(cls.RESOURCE_PATH, **request_kwargs)
        kwargs.setdefault("page_number", 0)
        return cls._build_page(response, context, **kwargs)

    @classmethod
    def _build_page(cls, response: Any, context: "Aixplain", **kwargs: Any) -> Page["Trigger"]:
        """Build a Page from the bare-array list response (single page)."""
        page = super()._build_page(response, context, **kwargs)
        page.page_total = 1
        return page

    @classmethod
    def list(cls, **kwargs: Any) -> List["Trigger"]:
        """Convenience wrapper returning the results list directly."""
        return cls.search(**kwargs).results

    # ------------------------------------------------------------------
    # Delete (deactivate Composio trigger first, then remove the record)
    # ------------------------------------------------------------------

    def delete(self, *args: Any, **kwargs: Any) -> DeleteResult:
        """Delete the trigger (deactivating the Composio trigger for events)."""
        if self.trigger_type == "external":
            if self.connection_id and self.trigger_id:
                try:
                    self._deactivate_event()
                except Exception as e:  # best-effort; still remove the record
                    warnings.warn(f"Failed to deactivate the Composio trigger: {e}", stacklevel=2)
            elif not self.connection_id:
                warnings.warn(
                    "Deleting the trigger record only; the Composio trigger was not deactivated "
                    "because the connection is unknown (re-fetched event triggers don't carry it).",
                    stacklevel=2,
                )
        return super().delete(*args, **kwargs)

    # ------------------------------------------------------------------
    # Composio activation helpers (via the model-execute endpoint)
    # ------------------------------------------------------------------

    def _execute_action(self, connection_id: str, action: str, data: Any) -> Any:
        """POST a connector action to the model-execute endpoint and resolve data."""
        url = f"{self.context.model_url}/{connection_id}"
        payload: Dict[str, Any] = {"action": action, "data": data}
        if action == "activate_trigger":
            payload["enable"] = True
            payload["toolkit_versions"] = "latest"
        response = self.context.client.request("post", url, json=payload)
        return self._poll_for_data(response)

    @staticmethod
    def _poll_for_data(response: dict) -> Any:
        """Return the ``data`` field, polling the URL if the call is async."""
        import time

        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(response, dict):
            return None
        if response.get("completed", True) or not isinstance(data, str) or not data.startswith("http"):
            return data
        # Not expected for trigger actions, but handle async just in case.
        return data

    def _activate_event(self) -> None:
        """Register the Composio trigger and capture its real trigger id."""
        if not self.connection_id:
            raise ValueError(
                "Event triggers require a connection. Create one via integration.connect() and use "
                "tool.triggers[...], or pass connection=<tool> to Trigger(...)."
            )
        data = self._execute_action(
            self.connection_id,
            "activate_trigger",
            {"slug": self.trigger_slug, "config": self.event_config or {}},
        )
        trigger_id = None
        if isinstance(data, dict):
            trigger_id = data.get("trigger_id") or data.get("triggerId")
        if not trigger_id:
            raise ResourceError(
                f"Failed to activate event trigger for slug={self.trigger_slug!r} on connection {self.connection_id}."
            )
        self.trigger_id = trigger_id

    def _deactivate_event(self) -> None:
        """Deactivate the Composio trigger for this event trigger."""
        self._execute_action(self.connection_id, "delete_trigger", {"trigger_id": self.trigger_id})

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def schedule_type(self) -> Optional[str]:
        """The schedule type (once/daily/weekly/monthly/recurring), if a time trigger."""
        return self.configuration.type if self.configuration else None

    def __repr__(self) -> str:
        """Return a concise representation."""
        return f"Trigger(id={self.id}, name={self.name!r}, type={self.trigger_type})"
