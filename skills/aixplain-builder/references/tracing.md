# Tracing & monitoring

Every agent run returns a full trace — the steps it took, the units it called, credits spent and time elapsed. Tracing is **on by default**; there is nothing to enable. Read it off the run result, watch it live while the run happens, or open it in the dashboard.

## Read the trace

```python
r = agent.run("What are the most popular programming languages this year?")

print(r.status)                                        # SUCCESS | FAILED | IN_PROGRESS
print([s["unit"]["name"] for s in r.data.steps])       # ['GPT-5.4', 'Tavily Web Search', 'GPT-5.4']
print(r.data.execution_stats["credits"], r.run_time)
```

> `r.data.steps` defaults to `[]` (never `None` on a decoded response), but `r.data.execution_stats` defaults to **`None`** — use `(r.data.execution_stats or {}).get(...)`. And on **model** runs `r.data` is a plain string, not an `AgentResponseData`; guard with `isinstance` in shared helper code.

## Step shape

`r.data.steps` is a list of plain dicts — one per model or tool call, in execution order. Each step says *who* ran it (`agent`) and *what* it called (`unit`).

```python
for n, step in enumerate(r.data.steps, 1):
    print(f"{n}. {step['agent']['name']} -> {step['unit']['name']} ({step['unit']['type']})")
    print("  ", step.get("thought"))
    print("   credits:", step["used_credits"], "| time:", step["run_time"], "| status:", step["status"])
```

| Field | What it holds |
|---|---|
| `agent` | Dict with `id`, `name` — the agent that ran the step. In a team this is the subagent or the inspector. Also carries `is_system_agent` (the SDK's own progress renderer marks those with `⚙`). |
| `unit` | Dict with `id`, `name`, `type` — `"model"` or `"tool"`. |
| `input` / `output` | What the unit received and returned (JSON strings for tool calls). |
| `thought` | The LLM's reasoning before the step, when it emits one. |
| `status` | Step outcome, e.g. `completed`. |
| `used_credits`, `api_calls` | Per-step cost and API-call count. |
| `input_tokens`, `output_tokens`, `total_tokens` | Token counts on model steps. |
| `start_time`, `end_time`, `run_time` | Step timing. |
| `action` | Inspector steps only: `continue` \| `rerun` \| `edit` \| `abort` — see `references/governance.md`. |
| `error`, `diagnostic_error_codes` | Set when the step failed. |

> Steps are **raw backend JSON**, not a typed object — always use `.get()`. The SDK itself reads `agent`, `unit`, `input`, `output`, `thought`, `action`, `task`, `step_id`, `used_credits`, `api_calls` and the token fields; `start_time` / `end_time` are documented but nothing in the SDK consumes them, so treat their presence as backend-version-dependent.

## Execution metrics

`r.data.execution_stats` is the run-level rollup.

```python
stats = r.data.execution_stats or {}
stats["api_calls"]    # total API calls
stats["credits"]      # authoritative run cost
stats["runtime"]      # seconds
stats["session_id"]   # e.g. 'Traced research agent_20261005055925'
stats["request_id"]   # e.g. '1-2f7e719f-86a0-49e5-b24c-7995eb6f31e3'
```

> **Read cost from `execution_stats["credits"]`, not `r.used_credits`** — the top-level field is frequently `0.0` on agent runs. The SDK's own `_extract_run_time_and_used_credits` backfills `run_time` / `used_credits` from `executionStats.runtime` / `.credits` exactly for this reason, but only when the top-level value is missing or zero.

Keep `request_id` (also on `r.request_id`) when you file a support ticket about a run. `execution_stats` may additionally carry `assets_used`, `runtime_breakdown` and `credit_breakdown` on backends that emit them — the evaluator reads them as optional.

## Tracing subagents

A team (`aix.Agent(..., agents=[...])` — see `references/agents.md`) returns **one** trace covering every subagent. The `agent` field on each step is what tells them apart; `unit` names only the model or tool.

```python
r = team.run("Give me a short summary of how the Eiffel Tower was built.")

for step in r.data.steps:
    print(step["agent"]["name"], "->", step["unit"]["name"])
# Traced research team -> delegate_task      <- parent routing
# Trace researcher     -> actions_search     <- subagent doing the work
# Trace writer         -> GPT-5.4

print(sorted({s["agent"]["name"] for s in r.data.steps}))   # who participated
```

Parent-level coordination shows up as `delegate_task` steps on the parent; a subagent that never appears in that set was never routed to — usually an overlapping `description`.

## Watch a run live

Pass `progress_format` to `run()` to render progress as it happens.

| Run kwarg | Type | Default | Effect |
|---|---|---|---|
| `progress_format` | `str` | `None` | `"status"` = one updating line; `"logs"` = step timeline; `"none"` = nothing. |
| `progress_verbosity` | `int` | `1` | `1` steps · `2` adds thoughts · `3` adds full inputs/outputs. |
| `progress_truncate` | `bool` | `True` | Shorten long text in the display. |

```python
r = agent.run("What is the latest stable Python release?", progress_format="logs", progress_verbosity=2)
# ✓ Step  1 · ⏱ 00:02.29 · API  1 · $0.002710 · ↓634 ↑75 (709) · Research agent ⧈ GPT-5.4
# ✓ Step  2 · ⏱ 00:02.38 · API  1 · $0.000750 · Research agent ⚒ Tavily Web Search
# ✓ Completed 3 steps · ⏱ 00:25.26 · API 3 · $0.013750 · ↓3652 ↑258 (3910)
```

> **`run_async()` ignores `progress_format`** — it returns as soon as the run is submitted, logs a warning, and displays nothing. Watch an async run on the poll instead: `agent.sync_poll(ar.url, progress_format="logs")`. The value is coerced via `ProgressFormat(...)`, so a typo (`"verbose"`) raises `ValueError`, not a silent fallback.

Driving the tracker directly (`aixplain.v2.agent_progress.AgentProgressTracker`) is only needed for a custom poll loop:

```python
from aixplain.v2.agent_progress import AgentProgressTracker, ProgressFormat

tracker = AgentProgressTracker(poll_func=agent.poll, poll_interval=0.5, max_polls=None,
                               force_display=True)          # True/False overrides TTY detection
final = tracker.stream_progress(ar.url, format=ProgressFormat.LOGS, verbosity=2, timeout=300)
```

> `stream_progress` has `timeout=300` and **raises `TimeoutError`** on expiry rather than returning an `IN_PROGRESS` response (pass `None` for unbounded). Its interval starts at `poll_interval` and backs off 10% per poll with jitter, capped at 60s. Use `start()`/`update()`/`finish()` instead when you own the poll loop — there the caller owns the interval and `poll_interval` is unused. Always `stop()` on an error path: `finish()` both stops the repaint thread and prints the summary, so skipping the summary on a failed run leaks a thread that repaints 20×/second forever.

## Monitor in the dashboard

Every run — SDK, REST or Studio — also lands in the aiXplain app dashboard at **https://app.aixplain.com/dashboard**, with its steps, cost and status. Use it to watch usage and cost across agents and to open the trace of any single run without re-running it.

Log the run's identifiers so you can find that row later — there is no documented per-run deep link, so you match on the id:

```python
stats = r.data.execution_stats or {}
print(r.request_id or stats.get("request_id"))   # '1-2f7e719f-86a0-49e5-b24c-7995eb6f31e3'
print(r.session_id or stats.get("session_id"))   # only set when the run went through a session
print("https://app.aixplain.com/dashboard")
```

`request_id` / `session_id` are declared fields on `AgentRunResult` (wire keys `requestId` / `sessionId`); the `execution_stats` copies come from the backend and may be absent — read those with `.get()`.

See `references/agents.md` for the agent/run lifecycle and `references/governance.md` for how inspector steps and `data.governance` read in the trace.
