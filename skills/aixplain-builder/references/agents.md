# Agents & team agents

[Create](#create-a-single-agent) · [Lifecycle](#lifecycle) · [Run](#run) · [Budget](#budget-cost--time--iteration-caps) · [Sessions](#sessions-multi-turn-memory) · [Skills](#skills) · [Files](#files-persistent-file--folder-assets) · [Triggers](#triggers-scheduled--event-driven-runs) · [Teams](#team-agents-multi-agent) · [Update](#update-a-deployed-agent) · [Troubleshooting](#troubleshooting)

An agent runs a **plan → act → observe → repeat** loop: it reads its instructions, picks tools, calls models/tools, and returns text, markdown, or JSON. A "team agent" is the **same `Agent` class** — passing `agents=[...]` is what makes it a team. There is no separate `TeamAgent` class. (The docs now say the same: "There is no separate team class"; the app still labels an agent with subagents a *team agent*.)

## Create a single agent

```python
agent = aix.Agent(
    name="Research Assistant",            # required; unique in your workspace
    description="Answers questions with research and citations",  # used to route work in teams
    instructions="Always cite sources. Be concise but thorough.",  # behaviour / system prompt
    tools=[search_tool],                  # optional
    output_format="text",                 # "text" (default) | "markdown" | "json"
).save()                                  # save() returns self -> DRAFT becomes ONBOARDED
print(agent.run("What is ML?").data.output)   # query is positional
```

Constructor parameters (all verified against the SDK):

| Param | Default | Notes |
|---|---|---|
| `name` | — | Required. Reusing a name raises `name_already_exists`. |
| `description` | — | User-facing purpose; in teams the Planner uses it to route work. |
| `instructions` | `None` | Internal guidance, not shown to users. Supports `{{placeholders}}`. |
| `tools` | `[]` | Marketplace tools, models-as-tools, integrations, KB index tools. |
| `llm` | GPT-5.4 (`69b7e5f1b2fe44704ab0e7d0`) | A `Model` object or a **model id** — an asset *path* string fails with `model.Invalid id`, so wrap paths in `aix.Model.get(path)`. Set `llm.inputs.temperature` / `reasoning_effort` on the `Model` before passing it; they are saved with the agent. **Omit unless the user asks for a specific model.** |
| `output_format` | `"text"` | `"text"` \| `"markdown"` \| `"json"`. |
| `expected_output` | `None` | Schema (str/dict/Pydantic model). Required when `output_format="json"`. |
| `agents` | `[]` | Subagents — passing this makes it a **team**. |
| `tasks` | `[]` | Structured-workflow tasks (see Teams below). |
| `inspectors` | `[]` | Runtime guardrails (see `references/governance.md`). |
| `skills` | `[]` | `aix.Skill` objects or ids — each must be `save()`d first (see Skills). |
| `files` | `[]` | `aix.File` objects/dicts/ids permanently attached to the agent — each must be `save()`d first (see Files). |
| `budget` | `Budget(None, None, None)` | Cost / duration / iteration caps. Always present; all-`None` means no enforcement. |
| `context_overflow_strategy` | `None` | `"truncate"` (engine default) \| `"summarize"` — how the working context is trimmed. |
| `planner` / `supervisor` / `response_generator` | `None` | LLM overrides for the coordination micro-agents. A `Model`, model id str, or dict — **not** an asset path (same `model.Invalid id` trap as `llm`). (Renamed from `planner_id` / `supervisor_id`; `response_generator` is new and serializes to the wire key `responder`.) |
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

Useful `run()` parameters: `query` (str or dict, **positional**), `session` (multi-turn — a `Session` or session id), `attachments` (images/audio for this run — URLs or local paths; local files are auto-uploaded), `history` (list of `{"role","content"}` to seed context; cannot be combined with `session`), `variables` (dict substituted into `{{placeholders}}` in instructions/description), `run_response_generation` (set `True` for JSON output), `execution_params` (per-run overrides, e.g. `{"context_overflow_strategy": "truncate"}`), `criteria`, `evolve`, `identifier`, `progress_format` (`None` = silent | `"status"` one line | `"logs"` step timeline), `progress_verbosity` (`1` steps, `2` + thoughts, `3` + full I/O), `progress_truncate` (default `True`), `run_retries` / `run_retry_wait` (extra submission attempts; total = 1 + n), `timeout` (default 300s — the SDK stops waiting, the server run continues), `wait_time` (poll interval, default 0.5s).

> **Not run parameters:** output length and the iteration cap are *agent* settings — `agent.max_tokens` and `agent.budget.max_iterations`, then `save()`. There is **no `budget=` run kwarg**: `build_run_payload` explicitly pops any stray `budget` key (verified), so passing one is silently ignored.

Attachment media must be reachable at run time — a URL behind a login or an expired signed link is not fetched — and the LLM must accept the media type. Passing a `session` as well stores the attachment on that turn so later turns can refer back to it.

> **Run-time `files=` ≠ constructor `files=`.** On `run()`, `files=` is a **deprecated alias for `attachments`** (per-run media, warns when used). On the constructor it means persistent File assets. Use `attachments=` for run inputs and reserve `files=` for the agent definition.

> **`session_id=` is dead.** Re-verified at 0.2.48: `generate_session_id()` and `create_session()` are **gone** from `Agent`, and `session_id` sits in `Agent._RUN_CONTROL_KEYS`, so it is stripped before the payload is built — a `session_id=` kwarg passed to `run()` never reaches the run body — it travels only as an `x-session-id` correlation header, so the run executes **statelessly** with no error and no warning. Old code keeps "working" while quietly losing all memory. Use `session=` (see Sessions).

**Async:**
```python
ar = agent.run_async(query="...")
r = agent.sync_poll(ar.url)        # blocks until done; same shape as run()
print(r.data.output)
# or manual: while not (res := agent.poll(ar.url, timeout=600)).completed: time.sleep(5)
```

`poll()` takes an optional `timeout` (seconds) and accepts a bare execution id as well as a full URL. The lower-level `AgentProgressTracker.stream_progress(url, …)` now takes `timeout` too (default **300s**, `None` for unbounded) and **raises `TimeoutError`** on expiry instead of returning an `IN_PROGRESS` response; its poll interval starts at 0.5s and backs off 10% per poll with jitter. `force_display=True/False` overrides TTY auto-detection, and `stop()` shuts the repaint thread down without printing a summary.

**JSON output** requires both `output_format="json"` + `expected_output=<schema>` on the agent, and `run_response_generation=True` at run time — otherwise the backend rejects with `AX-VAL-1000`.

> **Privacy:** every run payload auto-attaches a `metaData` block built by the SDK carrying the caller's **IP address, latitude/longitude, timezone, locale/region and user agent**. Flag this for privacy-sensitive deployments.

## Budget (cost / time / iteration caps)

```python
from aixplain.v2.agent import Budget

agent = aix.Agent(name="Governed", description="...",
                  budget=Budget(max_cost=0.5, max_duration_seconds=120, max_iterations=12))
agent.budget.max_cost = 1.0          # or set field-by-field, then save()
```

| Field | Meaning |
|---|---|
| `max_cost` | Credits for one run (1 credit = 1 USD). |
| `max_duration_seconds` | Wall-clock seconds before the run is blocked. |
| `max_iterations` | Reasoning steps in one run. |

Every agent always has a `budget` object; every field defaults to `None`, meaning **no cap until you set one** — and `0` is a cap of zero, not "unlimited". (The docs used to claim a default of `5` iterations for agents and teams; they now say `None` — don't rely on an implicit cap.) Limits are checked **between steps**: a blocked run stops planning and answers from the steps it already finished.

> **Silent no-op:** `agent.max_iterations = 30` after construction never reaches the save payload *or* the run payload — the value is lost without an error (re-verified at 0.2.48 against `build_save_payload()` / `build_run_payload()`). Only `agent.budget.max_iterations = 30` works. The docs now carry the same warning. (The constructor kwarg `max_iterations=` still works but is deprecated; if both are given, `budget` wins with a `UserWarning`.)

> **Field-verified (still not in the docs):** `max_cost` is **accepted and persisted but not enforced** at runtime — a run that exceeds it completed and billed normally. The docs get as far as admitting `used_credits` "can end above `max_cost`" because the final answer step still runs; our test saw no cut-off at all. Treat `max_cost` as advisory and bound runs with `max_duration_seconds` / `max_iterations`.

**Per-run override (verified in `build_run_payload`).** The agent's *current* budget is serialized into `executionParams.budget` on every run, and the backend merges it field-by-field over the persisted default. So mutate `agent.budget.<field>` after `save()` and before `run()` to change one run only — the saved budget is untouched. For the same reason a hand-written `execution_params={"budget": {...}}` is **overwritten** whenever the agent's own budget has any field set.

Reading the verdict:

```python
r = agent.run("...")
r.data.governance.get("status")   # "ALLOWED" | "BLOCKED_BY_BUDGET" | "BLOCKED_BY_INSPECTOR"
r.data.governance.get("source")   # "SYSTEM" (budget) | "INSPECTOR" | None when allowed
r.data.governance.get("reason")   # e.g. "Duration limit exceeded: 0.0s/0.0s"
```

> **Two gotchas.** A budget-blocked run still reports `r.status == "SUCCESS"` and still returns an answer. And `data.governance` is *always* a dict — when the backend sends nothing it is `{'status': None, 'source': None, 'reason': None}`, which is truthy. Test `r.data.governance.get("status")`, never `if r.data.governance:`.

## Sessions (multi-turn memory)

```python
session = aix.Session(agent=agent, name="Review Chat").save()
agent.run("My name is Adam.", session=session)
agent.run("What is my name?", session=session)     # remembers; or session=session.id
```

`session=` accepts a `Session` object or an id string — anything else raises `TypeError`. Sessions live on the server and are bound to one agent, so a fresh client (`aix.Agent.get(id)`) resumes the same conversation from `session.id` alone. Save payload is `{'agentId', 'name', 'status'}` (+ `executionConfig` if set); statuses are `active | completed | failed | archived`. Sessions are **never auto-deleted** — call `session.delete()` when done.

For one run's worth of prior turns *without* a stored session, pass `history=[{"role","content"}, …]` instead; nothing is persisted, and it cannot be combined with `session=`.

Persist per-session run config instead of repeating it on every call:

```python
from aixplain.v2 import Budget, ExecutionConfig
cfg = ExecutionConfig(execution_params={"max_tokens": 1024, "output_format": "text"},
                      criteria="Be concise.", identifier="support-desk",
                      budget=Budget(max_iterations=20))   # also: evolve, run_response_generation
aix.Session(agent=agent, name="Configured", execution_config=cfg)
```

`ExecutionConfig.budget` (a `Budget` or a dict) is the **session-scoped equivalent of `agent.budget`** — it serializes into `executionParams.budget`, so every message posted to the session runs under it. A deprecated `execution_params["max_iterations"]` is folded into that budget (the `Budget` wins) and never emitted on its own.

Message management: `session.messages()`, `add_message(role, content, attachments=[...], tools=[...])`, `get_message(id)`, `delete_message(id)`, `react(message_id, "LIKE"|"DISLIKE"|None)` (assistant messages only); plus `aix.Session.get(id)`, `clone()`, `save()` (rename) and `delete()`. Each run appends a `user` and an `assistant` message. A `SessionMessage` carries `sequence`, `role`, `content`, `reaction`, `request_id`, `attachments`, `created_at`; the session itself exposes `message_count`, `last_message_preview`, `last_message_at`, `run_status`. `content` may be empty when `attachments` carry the turn's input (e.g. an audio clip that *is* the prompt); each attachment entry is a URL string, a local path string (uploaded for you), or a dict with `url`/`path` plus optional `type`/`name`/`mimeType`.

`aix.Session.search(...)` is the **only** listing route — there is no `agent.list_sessions()` and no `Session.list()`. Filters: `agent` (object or id), `status`, `user_id`, `created_after` / `created_before` (datetime or ISO str), `memory_enabled`, `page_number` (0-based), `page_size` (20). It returns a `Page`, but the backend still answers with a bare JSON array, so the SDK synthesizes `page.total = len(results)` and `page_total = 1` — **`total` is the page size, not a real count**. The docs now claim `memory_enabled=True` returns sessions and `False` returns one-off runs; a previous field test found the SDK forwards `memoryEnabled` but the backend ignored it. Verify before relying on it.

**Constraints (enforced in the SDK):**

- These run kwargs raise `ValueError` when combined with `session=`: `tasks`, `prompt`, `inspectors`, `history`, `variables`.
- `query` must be a plain string, and a query or `attachments` is required.
- `run_async(session=...)` raises `NotImplementedError` — session runs are sync-only.
- Per-run overrides (`execution_params`, `criteria`, `evolve`, `identifier`, `run_response_generation`) alongside `session=` warn and **mutate and re-save the session's `executionConfig`**, affecting every later message on that session. The agent's own `budget` is seeded in the same way — it fills only the caps the session leaves unset — so a plain session run on a budgeted agent can emit that `UserWarning` and rewrite the session even when you passed no overrides at all. Expected; no action needed.

For durable cross-session / cross-agent memory, use the Shared Memory tool — see `references/knowledge-memory.md`.

## Skills

A skill is a **Claude-style `SKILL.md`** — YAML frontmatter plus markdown instructions, optionally alongside `scripts/` and `resources/` — registered as one aiXplain asset. Author it from a local folder containing `SKILL.md`, or from a single `.md` file that *is* the `SKILL.md`. The frontmatter is parsed locally at construction time; no network call happens until `save()`.

Routing works by **progressive disclosure**: the frontmatter `description` is the only signal the agent sees when deciding whether to use the skill; the body and resources load just-in-time at runtime. Make the `description` specific.

```python
skill = aix.Skill(file_path="pdf-filler/", tags=["forms"], privacy=aix.Privacy.PRIVATE)
skill = aix.Skill(file_path="calculator.md")    # ...or a single .md that IS the SKILL.md
skill.name            # frontmatter `name` (defaults to the folder name)
skill.description     # frontmatter `description` — the routing signal, the only required field
skill.required_tools  # frontmatter `requires:` (or `required_tools:`), a str or list of asset paths
skill.instructions    # the SKILL.md body
skill.status          # None locally; "completed" once saved
skill.save()          # uploads the whole tree

agent = aix.Agent(name="Forms Assistant", description="...", skills=[skill])   # Skill object or id str
```

Constructor `name=` / `description=` **override** whatever the frontmatter says (verified: they land in `build_save_payload()` unchanged) — handy for publishing two variants of one folder.

An unsaved skill raises `ValueError: All skills must be saved before saving the agent.` Same rule for `files=[...]` (`aix.File`).

- `save()` **re-parses `file_path` from disk on every call** — edit `SKILL.md` (or point `file_path` at new content) and re-save to push the change, including an edited frontmatter `name`/`description`. Caveat: the uploaded tree is added to and updated in place, so a file you **delete or rename locally is not removed** from the bundle.
- `update(path, name=None)` pushes a **single** file or subfolder without re-uploading everything — e.g. `skill.update("./helper.py", "scripts/helper.py")`. Pushing a `SKILL.md` also rewrites the asset's `description`. `name` defaults to `os.path.basename(path)`; `list_files()` shows the paths you can target.
- `Skill.get(id_or_path)` accepts an id or a workspace path (`"my-workspace/pdf-filler"`). `download(file_path=None)` writes the bundle to `./{name}.zip` by default. Also: `Skill.search(query, tags=, suppliers=, saved=)` → `Page`, `clone(name=…)` (then `save()` the copy), `refresh()`, `as_tool()` (wire type `"skill"`), `delete()`.
- Agents pick a skill up on their **next run** after `update()` — no agent re-save needed.

## Files (persistent file / folder assets)

`aix.File` is a **persistent** file or folder asset. Attach it once to an agent and every run can read it — no per-run upload. This is the opposite end from `attachments`, which are media for a single turn.

One class covers three sources: a local file, a **local directory uploaded as one asset with its full tree**, and a **public HTTP(S) URL streamed to the platform on `save()`**. The constructor performs no network calls — it only inspects the source and infers `name` and `file_type`; other URL schemes raise `ValidationError: Unsupported File URL scheme`.

```python
notes    = aix.File("reference/internal_notes.txt", name="internal-notes.txt")
handbook = aix.File("reference/policies", name="policy-handbook")   # whole tree, one asset
logo     = aix.File("https://example.com/assets/company-logo.png")  # fetched on save()

notes.save(); handbook.save()
notes.file_type   # aix.FileType.FILE | aix.FileType.FOLDER   (notes.is_dir is the shorthand)
notes.is_temp     # True until a successful save()
notes.id, notes.url, notes.path     # path = the encoded asset path, also accepted by get()
```

`save()` walks a directory and uploads every descendant under one root asset, preserving nested paths and empty folders. Root File names must be unique within a team. Local-only attributes: `extension`, `size` (both `None` for URL and folder sources). The first arg is `source`, but `file_path=` is accepted as an alias (as is `File.create_from_file(path)`), so Skill-style code still works.

```python
folder = aix.File.get(handbook.id)        # or an encoded asset path, or an instance id
folder.children                           # immediate children; full tree by default
aix.File.get(handbook.id, recursive=False)   # root + immediate children only

page = aix.File.search(query="policy", page_number=0, page_size=20,
                       file_type=aix.FileType.FOLDER)   # -> Page; also sort=[{"field","dir"}]
notes.download("downloads/internal_notes.txt")
folder.download("downloads/policy-handbook")   # one ZIP request, extracted for you
```

`download()` requires a saved asset; if the destination is an existing directory the asset's own name is appended.

Attach saved Files to an agent with the constructor's `files=` (objects or id strings). `agent.files` normalises to asset ids and survives a `save()` / `get()` round trip:

```python
agent = aix.Agent(name="Policy assistant", description="...",
                  instructions="Answer only from the attached reference files.",
                  files=[notes, handbook])
agent.save()
aix.Agent.get(agent.id).files        # ['6a3f…334', '6a3f…338']
```

At run time the agent reads attached Files with built-in file tools under a `reference_files/` folder — **say so in `instructions`** ("read the reference files attached to you before you answer") or it will often answer without opening them. Attaching a folder gives the agent every file inside it.

**Known limits:** there is **no `File.delete()`** in the SDK (confirmed — `delete` is absent from the class); `File.url` can be `None`, so read contents with `download()`; and a file **id is not accepted as a run input** — `run(attachments=[…])` takes URLs or local paths only.

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

`interval` defaults to `1` (used by `minute`/`hour`). `timezone` has **no SDK default** — it is simply omitted from the save payload when unset, and the backend then assumes UTC (verified via `build_save_payload()`); pass an IANA name to be explicit.

Event triggers fire on something happening in a connected integration. Browse the catalog with `aix.Integration.get("composio/gmail/composio").triggers` (the SDK also exposes `Integration.list_trigger_types()`), then pass one from the *connected tool*:

```python
aix.Trigger(name="Triage inbox", agent=agent,
            input="Triage this email and flag anything urgent.",
            event=tool.triggers["NEW_EMAIL"]).save()
```

Other kwargs: `notifications` (default `False`), `enabled` (default `True`). Management:

```python
t = aix.Trigger.get("<id>")
aix.Trigger.search(agent=agent)      # -> Page; also agent_id="…", page_number=…
aix.Trigger.list()                   # same, but returns the results list directly
t.schedule_type                      # once | daily | weekly | monthly | recurring (time triggers only)
t.enabled = False; t.save()          # disable in place; True re-enables
t.delete()                           # for an event trigger this also deactivates it upstream
```

> `trigger_type` is **`"time"`** for schedules (`triggerType: 'time'` in the save payload) and **`"external"`** for events, which also carry a `trigger_id` from the activated connection. The docs used to say `"scheduled"`; that was a docs bug and is now corrected — `"time"` is right. Only whitelisted fields are sent on save (the backend rejects anything else), so read-only attributes never round-trip.

## Debug: inspect the reasoning trace

```python
r = agent.run("...")
print([step["unit"]["name"] for step in r.data.steps])       # every model + tool call, in order
print(sorted({step["agent"]["name"] for step in r.data.steps}))   # which (sub)agent ran each step
print((r.data.execution_stats or {}).get("credits"))
```

`steps` entries are dicts whose `unit` and `agent` are themselves dicts — use `step["unit"]["name"]`, not `str(step["unit"])`. Checking `steps` is how you confirm a tool actually ran instead of inferring it from the answer.

**Full tracing — step timelines, `progress_format="logs"`, credits and run metrics — lives in `references/tracing.md`.** You can also analyze a finished run with the Debugger meta-agent — `aix.Debugger().debug_response(r)` returns a plain-English `.analysis` (see `references/governance.md`).

## Team agents (multi-agent)

Compose specialists into a team — an `aix.Agent` with `agents=[...]`, carrying every option on this page. Use subagents when one set of instructions would have to cover very different jobs. The built-in coordination micro-agents handle the rest: **Planner/Mentalist** decomposes the goal, **Orchestrator** routes tasks to subagents, **Inspector** validates quality, **Response Generator** synthesizes the final answer. (The dedicated `team-agents.md` docs page was deleted upstream; team guidance now lives in the main Agents page, and the micro-agents concept page is unlisted.)

```python
researcher = aix.Agent(name="Researcher", description="Finds and gathers information", tools=[search_tool])
writer     = aix.Agent(name="Writer", description="Writes clear reports", output_format="markdown")

team = aix.Agent(name="Research Team", description="Researches topics and writes reports",
                 instructions="Have the researcher gather facts first, then have the writer summarize.",
                 agents=[researcher, writer]).save(save_subcomponents=True)   # REQUIRED for teams
print(team.run("Research quantum computing and write a summary").data.output)
```

Without `save_subcomponents=True` you get `… must be saved before saving the agent`.

Give each subagent a **distinct `description`** — the parent routes on the subagent's `name` and `description` and **does not see the subagents' tools**, so a description that omits what the subagent can do makes it unroutable. Also note `name_already_exists` fires across the whole workspace, subagents included. Subagents take more steps than a single agent and teams have no default iteration cap, so **set** `team.budget.max_iterations` explicitly (e.g. 30–50) before saving.

To plan with a cheaper model than the team's own LLM, pass `planner=aix.Model.get("openai/gpt-4o-mini/openai")` — a `Model` or model id, never an asset path string.

### Structured workflow (deterministic task graph)

Use `Task` objects for explicit dependencies instead of autonomous planning. A task runs only after every task in its `dependencies` has finished, and the **last task produces the answer**. Dependencies must form a DAG. **If any subagent has a task, every subagent must have at least one.** Without tasks the parent plans at run time and adapts to intermediate results; with tasks the order is fixed and auditable.

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

> **Field-verified (not in the docs, not visible in signatures):** `agent.save()` can **reset the agent's LLM back to the platform default (GPT-5.4)**. After any save on an agent whose `llm` you set deliberately, re-read `agent.llm` and re-assign + re-save if it drifted. This has silently reverted model choices mid-project — always verify after the save, never before.

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
| Answer cut short | Raise `agent.max_tokens` (default 2048), then `save()`. |
| `model response was cut off because the maximum token limit was reached` | Different cause: the **LLM's** own cap. Set `llm.inputs.max_tokens`, re-assign `agent.llm`, then `save()`. |
| `model.Invalid id` on save | `llm` or `planner` got an asset *path* string. Pass `aix.Model.get(path)` or a model id. |
| `… must be saved before saving the agent` (subagents) | Save the team with `team.save(save_subcomponents=True)`. |
| Agent ignores a tool | Inspect `r.data.steps`; sharpen the tool's `name`/`description` and the agent's `instructions`. Keep total tool params low. |
| Team subagent never used | Make each subagent `description` distinct and self-describing — the parent cannot see its tools. In structured mode confirm task assignment. |
| Agent has Files attached but ignores them | Tell it to in `instructions` — attached files surface as `reference_files/`, and the agent often answers without opening them. |
| `UserWarning: Per-run execution overrides (budget …) were passed alongside session` | Expected: the agent's budget is being copied into the session's stored `executionConfig`. No action needed. |
| Tasks run out of order | Declare every `dependencies` edge — missing edges are the usual cause. |
| LLM reverted to the default (GPT-5.4) | Field-verified: `save()` can reset `agent.llm`. Re-read `agent.llm` **after** every save and re-assign + re-save if it drifted. |
| Run blew past `budget.max_cost` | Field-verified: `max_cost` is persisted but **not enforced**. Bound runs with `max_duration_seconds` / `max_iterations`. |
| `ValueError: All files must be saved before saving the agent` | `save()` each `aix.File` first — constructor `files=` takes saved assets only. |
| Agent can't see a file you passed to `run()` | Run-time `files=` is a deprecated alias for per-run `attachments`. For permanent material use constructor `files=` (see Files). |
| JSON rejected `AX-VAL-1000` | Need `output_format="json"` + `expected_output` + `run_response_generation=True`. |
| `name_already_exists` on save | Rename, or ask the user whether to update the existing agent. |
