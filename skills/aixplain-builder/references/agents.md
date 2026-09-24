# Agents & team agents

[Create](#create-a-single-agent) · [Lifecycle](#lifecycle) · [Run](#run) · [Budget](#budget-cost--time--iteration-caps) · [Sessions](#sessions-multi-turn-memory) · [Skills](#skills) · [Triggers](#triggers-scheduled--event-driven-runs) · [Teams](#team-agents-multi-agent) · [Update](#update-a-deployed-agent) · [Troubleshooting](#troubleshooting)

An agent runs a **plan → act → observe → repeat** loop: it reads its instructions, picks tools, calls models/tools, and returns text, markdown, or JSON. A "team agent" is the **same `Agent` class** — passing `agents=[...]` is what makes it a team. There is no separate `TeamAgent` class.

## Create a single agent

```python
agent = aix.Agent(
    name="Research Assistant",            # required; unique in your workspace
    description="Answers questions with research and citations",  # used to route work in teams
    instructions="Always cite sources. Be concise but thorough.",  # behaviour / system prompt
    tools=[search_tool],                  # optional
    output_format="text",                 # "text" (default) | "markdown" | "json"
)
agent.save()                              # DRAFT -> ONBOARDED (persistent endpoint)
print(agent.run(query="What is ML?").data.output)
```

Constructor parameters (all verified against the SDK):

| Param | Default | Notes |
|---|---|---|
| `name` | — | Required. Reusing a name raises `name_already_exists`. |
| `description` | — | User-facing purpose; in teams the Planner uses it to route work. |
| `instructions` | `None` | Internal guidance, not shown to users. Supports `{{placeholders}}`. |
| `tools` | `[]` | Marketplace tools, models-as-tools, integrations, KB index tools. |
| `llm` | platform default | A `Model` or model id/path. **Omit unless the user asks for a specific model.** |
| `output_format` | `"text"` | `"text"` \| `"markdown"` \| `"json"`. |
| `expected_output` | `None` | Schema (str/dict/Pydantic model). Required when `output_format="json"`. |
| `agents` | `[]` | Subagents — passing this makes it a **team**. |
| `tasks` | `[]` | Structured-workflow tasks (see Teams below). |
| `inspectors` | `[]` | Runtime guardrails (see `references/governance.md`). |
| `skills` | `[]` | `aix.Skill` objects or ids — each must be `save()`d first (see Skills). |
| `files` | `[]` | `aix.File` objects/dicts/ids permanently attached to the agent — each must be `save()`d first. |
| `budget` | `Budget(None, None, None)` | Cost / duration / iteration caps. Always present; all-`None` means no enforcement. |
| `context_overflow_strategy` | `None` | `"truncate"` (engine default) \| `"summarize"` — how the working context is trimmed. |
| `planner` / `supervisor` / `response_generator` | `None` | LLM overrides for the coordination micro-agents. A `Model`, model id str, or dict. (Renamed from `planner_id` / `supervisor_id`; `response_generator` is new and serializes to the wire key `responder`.) |
| `max_iterations` | `None` | **Deprecated.** Constructor value is folded into `budget.max_iterations` with a `DeprecationWarning`. |
| `max_tokens` | `2048` | Caps **output** tokens. |

`max_tokens` is an agent setting: set it in the constructor or as an attribute, then `save()`. Passing it to `run()` has no effect. For the reasoning-loop cap use `agent.budget.max_iterations` — **assigning `agent.max_iterations` after construction is a silent no-op** (see Budget).

## Lifecycle

| State | Meaning |
|---|---|
| `DRAFT` | Not yet saved. Temporary endpoint, **expires in 24h**. |
| `ONBOARDED` | Saved — persistent, versioned, production endpoint. |
| `DELETED` | Removed. |

```python
agent.save()                       # promote DRAFT -> ONBOARDED
agent.description = "new purpose"   # mutate then re-save to persist
agent.save()
agent.delete()
```

`save()` is the deploy step — there is no separate `agent.deploy()`. After saving, share the Studio links (see SKILL.md).

## Run

```python
r = agent.run(query="Search for AI news")
r.data.output        # final answer
r.status             # "SUCCESS" | "FAILED" | "IN_PROGRESS"
r.completed          # bool
r.error_message      # None on success
r.used_credits       # float — NOTE: often 0.0 for agents; read cost from execution_stats instead
r.run_time           # seconds
r.request_id         # backend run id — quote this in support tickets
r.session_id         # set when the run went through a session
r.diagnostic_error_codes
r.data.artifacts     # files the run produced (id, name, mime_type, url, sha256, byte_size, …)
r.data.critiques     # inspector feedback
r.data.governance    # budget/policy verdict — see below
```

> For the authoritative run cost, use `r.data.execution_stats["credits"]` — `r.used_credits` is frequently `0.0` on agent runs.

Useful `run()` parameters: `query` (str or dict), `session` (multi-turn — a `Session` or session id), `attachments` (URLs or local paths; local files are auto-uploaded), `history` (list of `{"role","content"}` to seed context), `variables` (dict substituted into `{{placeholders}}` in instructions/description), `run_response_generation` (set `True` for JSON output), `execution_params` (per-run overrides, e.g. `{"context_overflow_strategy": "truncate"}`), `criteria`, `evolve`, `identifier`, `progress_format` (`"status"` | `"logs"`), `progress_verbosity` (1–3), `progress_truncate`, `run_retries` / `run_retry_wait` (extra submission attempts; total = 1 + n), `timeout` (default 300s), `wait_time` (poll interval).

> **`session_id=` is dead.** `generate_session_id()` and `create_session()` have been **removed** from `Agent`, and a `session_id=` kwarg passed to `run()` is **silently stripped from the payload** — the run executes statelessly with no error and no warning. Old code keeps "working" while quietly losing all memory. Use `session=` (see Sessions).

**Async:**
```python
ar = agent.run_async(query="...")
r = agent.sync_poll(ar.url)        # blocks until done; same shape as run()
print(r.data.output)
# or manual: while not (res := agent.poll(ar.url, timeout=600)).completed: time.sleep(5)
```

`poll()` takes an optional `timeout` (seconds) and accepts a bare execution id as well as a full URL.

**JSON output** requires both `output_format="json"` + `expected_output=<schema>` on the agent, and `run_response_generation=True` at run time — otherwise the backend rejects with `AX-VAL-1000`.

> **Privacy:** every run payload auto-attaches a `metaData` block built by the SDK carrying the caller's **IP address, latitude/longitude, timezone, locale/region and user agent**. Flag this for privacy-sensitive deployments.

## Budget (cost / time / iteration caps)

```python
from aixplain.v2.agent import Budget

agent = aix.Agent(name="Governed", description="...",
                  budget=Budget(max_cost=0.5, max_duration_seconds=120, max_iterations=12))
agent.budget.max_cost = 1.0          # or set field-by-field, then save()
```

Every agent always has a `budget` object; leaving its fields `None` means no enforcement. Do **not** assume an SDK-side default of `5` iterations — that is a backend default, not the SDK's.

> **Silent no-op:** `agent.max_iterations = 30` after construction never reaches the save payload — the value is lost without an error. Only `agent.budget.max_iterations = 30` works. (The constructor kwarg `max_iterations=` still works but is deprecated; if both are given, `budget` wins with a `UserWarning`.)

A per-run `execution_params={"budget": {...}}` is **overwritten** by the agent's own budget whenever that budget has any field set. To vary a budget per run, mutate `agent.budget.<field>` before `run()` (not persisted unless you `save()`).

Reading the verdict:

```python
r = agent.run("...")
r.data.governance.get("status")      # e.g. "BLOCKED_BY_BUDGET"
```

> **Two gotchas.** A budget-blocked run still reports `r.status == "SUCCESS"`. And `data.governance` is *always* a dict — when the backend sends nothing it is `{'status': None, 'source': None, 'reason': None}`, which is truthy. Test `r.data.governance.get("status")`, never `if r.data.governance:`.

## Sessions (multi-turn memory)

```python
session = aix.Session(agent=agent, name="Review Chat")
session.save()
agent.run("My name is Adam.", session=session)
agent.run("What is my name?", session=session)     # remembers; or session=session.id
```

`session=` accepts a `Session` object or an id string. Save payload is `{'agentId', 'name', 'status'}` (+ `executionConfig` if set); statuses are `active | completed | failed | archived`.

Persist per-session run config instead of repeating it on every call:

```python
from aixplain.v2 import ExecutionConfig
cfg = ExecutionConfig(execution_params={"max_tokens": 1024, "output_format": "text"},
                      criteria="Be concise.", identifier="support-desk")   # also: evolve, run_response_generation, budget
aix.Session(agent=agent, name="Configured", execution_config=cfg)
```

Message management: `session.messages()`, `add_message(role, content, attachments=[...])`, `get_message(id)`, `delete_message(id)`, `react(message_id, reaction)`; plus `aix.Session.get/search(agent=, status=, …)`, `clone()`, `delete()`.

**Constraints (enforced in the SDK):**

- These run kwargs raise `ValueError` when combined with `session=`: `tasks`, `prompt`, `inspectors`, `history`, `variables`.
- `query` must be a plain string, and a query or `attachments` is required.
- `run_async(session=...)` raises `NotImplementedError` — session runs are sync-only.
- Passing `execution_params` alongside `session=` warns and **mutates and re-saves the session's `executionConfig`**, affecting every later message on that session.

For durable cross-session / cross-agent memory, use the Shared Memory tool — see `references/knowledge-memory.md`.

## Skills

A skill packages reusable expertise as a Claude-style folder (`SKILL.md` plus optional `scripts/` and `resources/`) uploaded as one asset. The frontmatter is parsed locally at construction time.

```python
skill = aix.Skill(file_path="pdf-filler/", tags=["forms"], privacy=aix.Privacy.PRIVATE)
skill.name            # from frontmatter `name`
skill.description     # the ONLY field the agent sees for routing — make it specific
skill.required_tools  # from frontmatter `requires:`
skill.save()          # uploads the whole tree

agent = aix.Agent(name="Forms Assistant", description="...", skills=[skill])   # Skill object or id str
```

An unsaved skill raises `ValueError: All skills must be saved before saving the agent.` Same rule for `files=[...]` (`aix.File`). Other methods: `Skill.get/search`, `download()`, `clone()`, `update()`, `refresh()`, `list_files()`, `as_tool()`, `delete()`.

## Triggers (scheduled / event-driven runs)

`aix.Trigger` fires an agent with a fixed `input` on a schedule or on an integration event. The SDK derives the schedule type from readable kwargs — no raw cron.

```python
aix.Trigger(name="Daily digest", agent=agent, input="Summarise today's AI news.",
            every="day", at="09:00", timezone="Europe/London").save()
```

| SDK call | `schedule_type` |
|---|---|
| `run_at="<iso>"` | `once` |
| `every="minute"` / `"hour"` (+ `interval`) | `recurring` |
| `every="day", at="HH:MM"` | `daily` |
| `every="week", on=["mon","thu"], at=` | `weekly` |
| `every="month", on=[1, 15], at=` | `monthly` |

Event triggers fire on something happening in a connected integration. Browse options with `integration.triggers` (the SDK also exposes `Integration.list_trigger_types()`), then pass one from the *connected tool*:

```python
aix.Trigger(name="Triage inbox", agent=agent,
            input="Triage this email and flag anything urgent.",
            event=tool.triggers["NEW_EMAIL"]).save()
```

Other kwargs: `notifications` (default `False`), `enabled` (default `True`). Standard `get`/`search`/`delete`.

> The docs say time triggers report `trigger_type="scheduled"`; the SDK actually emits **`"time"`** (`triggerType: 'time'` in the save payload). Event triggers report `external` and carry a `trigger_id`.

## Debug: inspect the reasoning trace

```python
r = agent.run(query="...")
for step in r.data.steps or []:
    print(step.get("agent"), step.get("thought"))
    print(step.get("unit"), step.get("input"), str(step.get("output"))[:200], step.get("error"))

stats = r.data.execution_stats or {}
print(stats.get("runtime"), stats.get("api_calls"), stats.get("credits"), stats.get("assets_used"))
```

You can also analyze a finished run with the Debugger meta-agent — `aix.Debugger().debug_response(r)` returns a plain-English `.analysis` (see `references/governance.md`).

## Team agents (multi-agent)

Compose specialists into a team. The built-in coordination micro-agents handle the rest: **Planner/Mentalist** decomposes the goal, **Orchestrator** routes tasks to subagents, **Inspector** validates quality, **Response Generator** synthesizes the final answer.

```python
researcher = aix.Agent(name="Researcher", description="Finds and gathers information", tools=[search_tool])
writer     = aix.Agent(name="Writer", description="Writes clear reports", output_format="markdown")

team = aix.Agent(name="Research Team", description="Researches topics and writes reports",
                 agents=[researcher, writer])
team.save(save_subcomponents=True)     # REQUIRED for teams — saves subagents first, then the team
print(team.run(query="Research quantum computing and write a summary").data.output)
```

Give each subagent a **distinct `description`** — autonomous routing depends on it. Raise `team.budget.max_iterations` (e.g. 30–50) for complex teams, then `save()`.

### Structured workflow (deterministic task graph)

Use `Task` objects for explicit dependencies instead of autonomous planning. Dependencies must form a DAG. **If any subagent has a task, every subagent must have at least one.**

```python
find = aix.Agent.Task(name="find_leads", instructions="Find EdTech companies",
                      expected_output="List of companies with contact info")
analyze = aix.Agent.Task(name="analyze_leads", instructions="Prioritise leads",
                         expected_output="Qualified list", dependencies=[find])

finder   = aix.Agent(name="Lead Finder",   description="Finds leads",   tools=[search_tool], tasks=[find])
analyzer = aix.Agent(name="Lead Analyzer", description="Qualifies leads", tasks=[analyze])

team = aix.Agent(name="Lead Gen Team", description="Generates and qualifies leads",
                 agents=[finder, analyzer])
team.save(save_subcomponents=True)
```

## Update a deployed agent

Deployed agents are mutable — never recreate one to change behaviour. Load it, mutate fields, and `save()`; the agent ID, history, and external references stay intact.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.llm = "<MODEL_ID>"     # swap the LLM — assign to .llm (model id string or Model object)
agent.save()
```

> **`.llm` not `.llm_id`:** assign the model to `agent.llm`. The attribute `agent.llm_id` exists but assigning it does **not** propagate to the save payload — `save()` silently keeps the old model.

You can also update an attached tool in place (no detach/reattach) — change its `description` or `allowed_actions`, call `tool.save()`, and the agent picks it up on the next run:

```python
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated scope: includes 2026 docs."
kb_tool.save()
```

To branch off a copy instead of mutating the original, `agent.duplicate(duplicate_subagents=False, name=None)` makes a server-side copy. (SDK-only — not in the docs pages.)

## Export a deployed agent to a standalone script

Rebuild any deployed agent as portable Python using the SDK — no raw REST. `Agent.get()` returns the full config; serialize it and recurse into subagents.

```python
agent = aix.Agent.get("<AGENT_ID>")
config = agent.to_dict()     # full config: name, description, instructions, output_format, llm, tools, max_tokens, inspectors
subs   = agent.subagents     # subagent objects for a team — recurse the same way
```

Then map those fields to constructor args and emit a `.py` that loads the key from `AIXPLAIN_API_KEY` and rebuilds the agent: `aix.Agent(name=..., description=..., instructions=..., tools=[aix.Tool.get(...)], llm=..., output_format=...)` (recreate inspectors per `references/governance.md`), ending with `.save()`. This gives the user a reproducible, version-controllable definition of a Studio-built or previously-deployed agent.

## List & inspect

```python
for a in aix.Agent.search()["results"]:
    print(a.name, a.id)
agent = aix.Agent.get("YOUR_AGENT_ID")
print(agent.name, agent.status, agent.tools)
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| "maximum number of iterations" | `agent.budget.max_iterations = 20` (teams 50), then `save()`. **`agent.max_iterations = 20` is a silent no-op.** |
| Multi-turn agent has no memory | You passed `session_id=` — it is silently dropped. Use `session=` with an `aix.Session`. |
| `ValueError: session=… runs do not support legacy run kwargs` | Drop `tasks`/`prompt`/`inspectors`/`history`/`variables`, or run without a session. |
| Output cut off | Raise `agent.max_tokens` (default 2048), or the LLM's `inputs.max_tokens`, then `save()`. |
| Agent ignores a tool | Inspect `r.data.steps`; sharpen the tool's `name`/`description`. Keep total tool params low. |
| Team subagent never used | Make each subagent `description` distinct; in structured mode confirm task assignment. |
| Tasks run out of order | Declare every `dependencies` edge — missing edges are the usual cause. |
| JSON rejected `AX-VAL-1000` | Need `output_format="json"` + `expected_output` + `run_response_generation=True`. |
| `name_already_exists` on save | Rename, or ask the user whether to update the existing agent. |
