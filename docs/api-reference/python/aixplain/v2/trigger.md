---
sidebar_label: trigger
title: aixplain.v2.trigger
---

Trigger management module for the aiXplain v2 API.

A :class:`Trigger` fires an agent with an ``input`` (the query) either on a time
schedule (once / daily / weekly / monthly / interval) or on an external event
(e.g. a Composio integration event such as a new Gmail email).

Time triggers map straight onto ``POST/GET/PUT/DELETE /v1/triggers``. Event
triggers are orchestrated over the existing endpoints: the SDK activates the
Composio trigger on a connected tool via the model-execute endpoint (the same
mechanism used by ``integration.actions``), then persists the returned trigger id
through ``/v1/triggers``.

### TriggerRepeatRule Objects

```python
@dataclass_json

@dataclass
class TriggerRepeatRule()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L98)

Interval rule for a ``recurring`` schedule (e.g. every 2 hours).

### TriggerConfiguration Objects

```python
@dataclass_json

@dataclass
class TriggerConfiguration()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L107)

Structured time-schedule configuration (mirrors the backend config).

### TriggerSearchParams Objects

```python
class TriggerSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L120)

Search parameters for triggers (filter by agent).

### TriggerGetParams Objects

```python
class TriggerGetParams(BaseGetParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L126)

Get parameters for triggers.

### TriggerDeleteParams Objects

```python
class TriggerDeleteParams(BaseDeleteParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L132)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L140)

A schedule/event trigger that fires an agent with a fixed input.

Time trigger examples::

    aix.Trigger(name=&quot;Launch reminder&quot;, agent=agent, input=&quot;Remind the team.&quot;,
                run_at=&quot;2026-01-26T12:00:00Z&quot;).save()                       # once
    aix.Trigger(name=&quot;Daily digest&quot;, agent=agent, input=&quot;Summarise the news.&quot;,
                every=&quot;day&quot;, at=&quot;09:00&quot;, timezone=&quot;Europe/London&quot;).save()   # daily
    aix.Trigger(name=&quot;Hourly check&quot;, agent=agent, input=&quot;Check the queue.&quot;,
                every=&quot;hour&quot;, interval=2).save()                            # every 2 hours
    aix.Trigger(name=&quot;Weekly report&quot;, agent=agent, input=&quot;Compile the report.&quot;,
                every=&quot;week&quot;, on=[&quot;mon&quot;, &quot;thu&quot;], at=&quot;17:00&quot;).save()         # weekly
    aix.Trigger(name=&quot;Invoice run&quot;, agent=agent, input=&quot;Generate invoices.&quot;,
                every=&quot;month&quot;, on=[1, 15], at=&quot;09:00&quot;).save()               # monthly

Event trigger example (requires a connected tool)::

    gmail = aix.Integration.get(&quot;composio/gmail&quot;)
    tool = gmail.connect(...)
    aix.Trigger(name=&quot;Triage inbox&quot;, agent=agent, input=&quot;Triage this email.&quot;,
                event=tool.triggers[&quot;NEW_EMAIL&quot;]).save()

Manage::

    t = aix.Trigger.get(&quot;&lt;id&gt;&quot;)
    aix.Trigger.search(agent=agent)     # -&gt; Page
    t.enabled = False; t.save()         # disable (re-enable with True)
    t.delete()

#### PAGINATE\_ITEMS\_KEY

bare array response

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L218)

Translate friendly construction kwargs into backend-shaped fields.

Skipped when rehydrating from the backend (``id`` already set), so that
``from_dict`` in get/search/create is left untouched.

#### before\_save

```python
def before_save(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L339)

Activate the Composio trigger before persisting a new event trigger.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L345)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L386)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L421)

Convenience wrapper returning the results list directly.

#### delete

```python
def delete(*args: Any, **kwargs: Any) -> DeleteResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L429)

Delete the trigger (deactivating the Composio trigger for events).

#### schedule\_type

```python
@property
def schedule_type() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L502)

The schedule type (once/daily/weekly/monthly/recurring), if a time trigger.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/trigger.py#L506)

Return a concise representation.

