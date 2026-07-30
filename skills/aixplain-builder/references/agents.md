# Agents & team agents

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
| `expected_output` | `""` | Schema (str/dict/Pydantic model). Required when `output_format="json"`. |
| `agents` | `[]` | Subagents — passing this makes it a **team**. |
| `tasks` | `[]` | Structured-workflow tasks (see Teams below). |
| `inspectors` | `[]` | Runtime guardrails (see `references/governance.md`). |
| `max_iterations` | `5` | Reasoning-loop cap. Raise for complex/team work. |
| `max_tokens` | `2048` | Caps **output** tokens. |

`max_iterations` / `max_tokens` are agent settings: set them in the constructor or as attributes, then `save()`. Passing them to `run()` has no effect.

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
```

> For the authoritative run cost, use `r.data.execution_stats["credits"]` — `r.used_credits` is frequently `0.0` on agent runs.

Useful `run()` parameters: `query` (str or dict), `session_id` (multi-turn memory), `history` (list of `{"role","content"}` to seed context), `variables` (dict substituted into `{{placeholders}}` in instructions/description), `run_response_generation` (set `True` for JSON output), `progress_format` (`"status"` | `"logs"`), `progress_verbosity` (1–3), `timeout` (default 300s), `wait_time` (poll interval). Some patterns also pass `content=[...]` to supply source material separately from `query`.

**Async:**
```python
ar = agent.run_async(query="...")
r = agent.sync_poll(ar.url)        # blocks until done; same shape as run()
print(r.data.output)
# or manual: while not (res := agent.poll(ar.url)).completed: time.sleep(5)
```

**JSON output** requires both `output_format="json"` + `expected_output=<schema>` on the agent, and `run_response_generation=True` at run time — otherwise the backend rejects with `AX-VAL-1000`.

## Session memory (multi-turn)

```python
session_id = agent.generate_session_id()      # or generate_session_id(history=[...])
agent.run(query="What is the capital of France?", session_id=session_id)
agent.run(query="What did I just ask?", session_id=session_id)   # remembers
```

For durable cross-session / cross-agent memory, use the Shared Memory tool — see `references/knowledge-memory.md`.

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

Give each subagent a **distinct `description`** — autonomous routing depends on it. Raise `team.max_iterations` (e.g. 30–50) for complex teams.

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
| "maximum number of iterations" | `agent.max_iterations = 20` (teams 50), then `save()`. |
| Output cut off | Raise `agent.max_tokens` (default 2048), or the LLM's `inputs.max_tokens`, then `save()`. |
| Agent ignores a tool | Inspect `r.data.steps`; sharpen the tool's `name`/`description`. Keep total tool params low. |
| Team subagent never used | Make each subagent `description` distinct; in structured mode confirm task assignment. |
| Tasks run out of order | Declare every `dependencies` edge — missing edges are the usual cause. |
| JSON rejected `AX-VAL-1000` | Need `output_format="json"` + `expected_output` + `run_response_generation=True`. |
| `name_already_exists` on save | Rename, or ask the user whether to update the existing agent. |
