---
sidebar_label: trigger
title: aixplain.v2.trigger
---

`from aixplain import Trigger, TriggerConfiguration, TriggerConfigurationDict, TriggerRepeatRule, TriggerRepeatRuleDict`


Trigger management module for the aiXplain v2 API.

A `Trigger` fires an agent with an ``input`` (the query) either on a time
schedule (once / daily / weekly / monthly / interval) or on an external event
(e.g. a Composio integration event such as a new Gmail email).

Time triggers map straight onto ``POST/GET/PUT/DELETE /v1/triggers``. Event
triggers are orchestrated over the existing endpoints: the SDK activates the
Composio trigger on a connected tool via the model-execute endpoint (the same
mechanism used by ``integration.actions``), then persists the returned trigger id
through ``/v1/triggers``.

### TriggerRepeatRuleDict Objects

```python
class TriggerRepeatRuleDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L98)

The dict form of `TriggerRepeatRule`, on the same field names.

### TriggerConfigurationDict Objects

```python
class TriggerConfigurationDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L105)

The dict form of `TriggerConfiguration`, on the same field names.

``repeat`` takes a `TriggerRepeatRuleDict` or a
`TriggerRepeatRule`; ``next_run_at`` is reported by the backend and
never sent.

### TriggerRepeatRule Objects

```python
@dataclass_json

@dataclass
class TriggerRepeatRule()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L126)

Interval rule for a ``recurring`` schedule (e.g. every 2 hours).

### TriggerConfiguration Objects

```python
@dataclass_json

@dataclass
class TriggerConfiguration()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L135)

Structured time-schedule configuration (mirrors the backend config).

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L148)

Coerce a dict ``repeat`` into a `TriggerRepeatRule`.

On every assignment rather than in ``__post_init__`` alone: reading
``configuration.repeat`` has to give an object with attributes whichever
way it was set, or ``_hydrate_schedule_fields`` (``config.repeat.unit``)
fails with ``AttributeError`` on a dict assigned after construction.
Mirrors how `Trigger` coerces ``configuration``.

### TriggerSearchParams Objects

```python
class TriggerSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L173)

Search parameters for triggers (filter by agent).

### TriggerGetParams Objects

```python
class TriggerGetParams(BaseGetParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L179)

Get parameters for triggers.

### TriggerDeleteParams Objects

```python
class TriggerDeleteParams(BaseDeleteParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L185)

Delete parameters for triggers.

### Trigger Objects

```python
@dataclass_json

@dataclass(repr=False)
class Trigger(BaseResource, SearchResourceMixin[TriggerSearchParams,
                                                "Trigger"],
              GetResourceMixin[TriggerGetParams, "Trigger"],
              DeleteResourceMixin[TriggerDeleteParams, DeleteResult])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L193)

A schedule/event trigger that fires an agent with a fixed input.

Time trigger examples:

```python
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
```


Event trigger example (requires a connected tool):

```python
gmail = aix.Integration.get("composio/gmail")
tool = gmail.connect(...)
aix.Trigger(name="Triage inbox", agent=agent, input="Triage this email.",
            event=tool.triggers["NEW_EMAIL"]).save()
```


Manage:

```python
t = aix.Trigger.get("<id>")
aix.Trigger.search(agent=agent)     # -> Page
t.enabled = False; t.save()         # disable (re-enable with True)
t.delete()
```



#### PAGINATE\_ITEMS\_KEY

bare array response

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L273)

Coerce a dict ``configuration`` into a `TriggerConfiguration`.

Here rather than in ``__post_init__`` so a later
``trigger.configuration = {...}`` behaves the same as passing it to the
constructor, and reading it back always gives an object with attributes.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L286)

Translate friendly construction kwargs into backend-shaped fields.

When rehydrating from the backend (``id`` already set), populate the
friendly schedule fields from ``configuration`` without rebuilding it.

#### before\_save

```python
def before_save(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L436)

Activate the Composio trigger before persisting a new event trigger.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L442)

Build the whitelisted payload for ``POST``/``PUT`` /v1/triggers.

The backend uses ``forbidNonWhitelisted`` validation, so only the fields
accepted by ``TriggerInput`` are sent (never read-only fields).

#### search

```python
@classmethod
def search(cls,
           agent: Optional[Any] = None,
           agent_id: Optional[str] = None,
           **kwargs: Any) -> Page["Trigger"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L488)

List triggers for the team, optionally filtered by agent.

**Arguments**:

- `agent` - An Agent instance (or anything with ``.id``) to filter by.
- `agent_id` - An agent id string to filter by.
- `**kwargs` - Additional options forwarded to page building (e.g. ``page_number``).
  

**Returns**:

  Page[Trigger]

#### list

```python
@classmethod
def list(cls, **kwargs: Any) -> List["Trigger"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L523)

Convenience wrapper returning the results list directly.

#### delete

```python
def delete(*args: Any, **kwargs: Any) -> DeleteResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L531)

Delete the trigger (deactivating the Composio trigger for events).

#### schedule\_type

```python
@property
def schedule_type() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L604)

The schedule type (once/daily/weekly/monthly/recurring), if a time trigger.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L608)

Return a concise representation.

