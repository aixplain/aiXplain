# Run metadata

Agent runs issued by the aiXplain SDK send a `metaData` object alongside your query.
This page is the complete disclosure of what that object contains, why it is collected,
where it goes, and what happens when the lookup behind it fails. [Which calls send
it](#which-calls-send-it) below is the exact list — notably, v2 runs routed through a
session do not carry it.

`metaData` is built by
[`aixplain.utils.user_info_utils.build_run_metadata()`](../aixplain/utils/user_info_utils.py).
It is not related to the header-only run metadata (`x-session-id`, `x-agent`) that the
v2 runnables emit for tracing.

---

## What is sent

| `metaData` key | Type | Source | Example |
|---|---|---|---|
| `userAgent` | string | constant `"sdk"` | `"sdk"` |
| `region` | string \| null | `ipinfo.country` + the territory's primary official language (Babel) | `"en-US"` |
| `language` | string \| null | primary official language of `ipinfo.country` | `"en"` |
| `ipAddress` | string \| null | `ipinfo.ip` — the public IP of the machine running the SDK | `"192.0.2.10"` |
| `latitude` | number \| null | first half of `ipinfo.loc` — city-level, derived from the IP | `37.7749` |
| `longitude` | number \| null | second half of `ipinfo.loc` — city-level, derived from the IP | `-122.4194` |
| `timezone` | string \| null | `ipinfo.timezone` (IANA name) | `"America/Los_Angeles"` |

Every key is always present. `userAgent` is always `"sdk"`; every other key is `null`
when the lookup did not supply it.

The run payload looks like this on the wire:

```json
{
  "id": "68d0...",
  "query": "...",
  "executionParams": { "...": "..." },
  "metaData": {
    "userAgent": "sdk",
    "region": "en-US",
    "language": "en",
    "ipAddress": "192.0.2.10",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "timezone": "America/Los_Angeles"
  }
}
```

The coordinates are city-level estimates inferred from the IP address. They are not
device GPS: the SDK never asks the operating system for a location.

---

## Why it is collected

- **`region`, `language`, `timezone`** — locale-aware agent execution. The platform uses
  them to adapt a run to the caller's locale; this is the stated purpose of the lookup.
- **`userAgent`** — distinguishes SDK traffic from console and direct-API traffic.
- **`ipAddress`, `latitude`, `longitude`** — collected as part of the same lookup and
  forwarded with the run. They are named here explicitly rather than folded into a
  vaguer phrase, because a disclosure that understates what leaves your machine is
  not a disclosure.

---

## Where it goes

Two destinations, both worth stating separately:

1. **ipinfo.io** — the SDK makes one `GET https://ipinfo.io/json` request from the
   machine running it. That request carries no API key, no query text, and no agent
   data; ipinfo.io sees only that your host asked about itself. See the
   [ipinfo.io privacy policy](https://ipinfo.io/privacy-policy) for what they retain.
2. **The aiXplain backend** — the resulting values are POSTed inside the run payload's
   `metaData` field to `BACKEND_URL` (default `https://platform-api.aixplain.com`),
   over TLS, with your API key. See the
   [aiXplain Security page](https://aixplain.com/security/).

---

## When it happens

The lookup runs **once per Python process**, on your first agent run, and is cached by
`functools.lru_cache(maxsize=1)`. It is bounded by a **2-second timeout**.

That means the first agent run in a process can be up to ~2 seconds slower than the
rest in an environment with restricted egress. Subsequent runs in that process pay
nothing: the cache also memoises failures, so a blocked lookup is attempted once and
never retried.

## When it fails

Any failure — timeout, DNS failure, blocked egress, non-2xx response, unparseable body
— is swallowed and logged at `DEBUG` level. The run then proceeds normally: `metaData`
is still sent, with `userAgent: "sdk"` and every other field `null`. **A run never
fails because of this lookup.**

If you see `latitude: null` in a trace, this is why.

---

## Which calls send it

| Surface | Call site | When |
|---|---|---|
| v2 `Agent.build_run_payload` | `aixplain/v2/agent.py` | every direct v2 agent run (`agent.run` / `agent.run_async`) |
| v1 `Agent.run_async` | `aixplain/v1/modules/agent/__init__.py` | every v1 agent run (`run` delegates to `run_async`) |
| v1 `Agent.generate_session_id` | `aixplain/v1/modules/agent/__init__.py` | v1 session bootstrap |
| v1 `TeamAgent.run_async` | `aixplain/v1/modules/team_agent/__init__.py` | every v1 team-agent run |
| v1 `TeamAgent.generate_session_id` | `aixplain/v1/modules/team_agent/__init__.py` | v1 team-agent session bootstrap |

Direct v2 agent runs reach the single v2 call site through
`RunnableResourceMixin._post_and_handle_run`, which calls `build_run_payload`. A v2 run
routed through a session (`agent.run(query, session=…)`) does not go through
`build_run_payload` at all — see below.

**These do _not_ send `metaData`:**

- v2 session messages — `agent.run(query, session=...)` posts to
  `/v1/sessions/{id}/messages` with `role`, `content`, `requestId`, `attachments` and
  `tools` only.
- Model runs and pipeline runs.
- Every non-run endpoint: create, list, search, get, update, delete.

---

## If you do not want the lookup

There is no SDK flag or environment variable that disables it today; the platform uses
these fields for agent execution, so the behaviour is intentional and on by default.

What you can do:

- **Block egress to `ipinfo.io`** from the host running the SDK. The lookup fails
  closed after one 2-second attempt, `ipAddress`/`latitude`/`longitude`/`region`/
  `language`/`timezone` arrive as `null`, and runs continue. The only functional loss
  is locale inference — agents fall back to platform defaults.
- **Talk to us** at [care@aixplain.com](mailto:care@aixplain.com) if you need a
  contractual or deployment-level opt-out, or have a data-protection question about
  the IP and coordinate fields.

---

## Related

- Source: [`aixplain/utils/user_info_utils.py`](../aixplain/utils/user_info_utils.py)
- [Data handling and deployment](README.md#data-handling-and-deployment)
- Arabic version: [`run-metadata.ar.md`](run-metadata.ar.md)
