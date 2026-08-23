# Agent patterns (SDK v2)

Read this only for teams, updates, knowledge/memory, budgets, or portability.

## Single agent or team

Use one agent by default. Use a team when at least one is true:
- roles need different tools or permissions;
- specialist context would otherwise overload one prompt;
- work can be delegated with clear outputs;
- an independent reviewer materially improves reliability.

Do not create a team merely because the workflow has multiple steps.

## Team agent

```python
researcher = aix.Agent(
    name="Evidence Researcher",
    description="Finds and summarizes evidence from approved sources.",
    instructions="Use the search tool; return source-backed facts only.",
    tools=[search_tool],
).save()
researcher.budget.max_iterations = 30
researcher.save()

writer = aix.Agent(
    name="Briefing Writer",
    description="Turns validated evidence into a concise briefing.",
    instructions="Write only from supplied evidence; flag gaps.",
).save()

team = aix.Agent(
    name="Customer Briefing Team",
    description="Researches and writes a verified customer briefing.",
    instructions="Delegate evidence gathering, then synthesize the final answer.",
    agents=[researcher, writer],
).save()
team.budget.max_iterations = 15
team.save()
```

Subagent names and descriptions drive routing. Make them outcome-specific. Use `agents=`, not deprecated `subagents=`.

Typical iteration defaults:
- team lead: `12–15`;
- tool-heavy worker: `30–40`;
- toolless writer/reviewer: backend default is usually enough.

Exhaustion can return an internal `[Calling tool delegate_task ...]` trace while run status is `SUCCESS`; validate output shape and governance.

## Budgets

Every agent has `agent.budget`. Mutate it before `run()` for a one-off cap; save it to persist a default.

```python
agent.budget.max_cost = 0.25
agent.budget.max_duration_seconds = 120
agent.budget.max_iterations = 12
agent.save()
```

Do not pass `budget=` to `agent.run()` on `0.2.47`; it is silently ignored. `max_iterations=` as a standalone field/argument is deprecated.

A budget is a circuit breaker, not a billing ceiling: in-flight and subagent work can overshoot. Treat `result.data.execution_stats["credits"]` as actual spend. A budget block can still return run status `SUCCESS`; inspect `result.data.governance`.

## Update without changing the ID

SDK `0.2.47` `Agent.get()` can widen hydrated tool scopes. Load the raw backend definition first and reapply its persisted `actions` values before mutating or exporting:

```python
def load_agent_preserving_scopes(aix, agent_id: str):
    raw = aix.Agent.context.client.get(f"v2/agents/{agent_id}")
    agent = aix.Agent.get(agent_id)
    scopes = {
        item.get("id"): list(item.get("actions") or [])
        for item in (raw.get("tools") or [])
        if isinstance(item, dict) and item.get("id")
    }
    for tool in agent.tools or []:
        tool_id = getattr(tool, "id", None)
        if tool_id in scopes:
            tool.allowed_actions = scopes[tool_id]
    return agent, raw

agent, raw = load_agent_preserving_scopes(aix, "<AGENT_ID>")
agent.instructions = "Updated instructions..."
agent.description = "Updated description..."
agent.tools = updated_tools or agent.tools
agent.output_format = "markdown"
agent.save()
```

After saving, fetch `v2/agents/<ID>` again and assert each raw tool's `actions` equals the intended least-privilege scope. Do not trust hydrated `allowed_actions` until the bug is fixed.

Do not recreate by default. Verify the same capabilities after every update.

`0.2.47` fixed the earlier `Agent.get()`/`save()` default-LLM overwrite. If behavior suggests a regression, compare the backend model before/after and log it in `BUGS.md` rather than adding a permanent workaround without evidence.

## Sessions (one conversation)

```python
session = aix.Session(agent=agent, name="customer-thread").save()
first = agent.run("My company is Acme.", session=session)
second = agent.run("Which company did I mention?", session=session)
```

Sessions are synchronous. `run_async(..., session=...)` is not supported.

## Invocation and runtime controls

Configure tools, model, `output_format`, `expected_output`, and the default `agent.budget` on the agent. `run()` controls one execution:

```python
result = agent.run(
    query="Create the customer briefing from the supplied context.",
    session=session,  # omit for a stateless run
    variables={"account_name": "Acme"},
    identifier="customer-123",
    attachments=["/absolute/path/to/brief.pdf"],
    criteria="Include sources and flag unsupported claims.",
)
```

| Need | `run()` controls | Notes |
|---|---|---|
| Conversation | `query`, `session` | `session` accepts a `Session` or ID. |
| Per-run input | `variables`, `identifier`, `attachments` | Use `attachments`, not deprecated `files`; local paths upload automatically. |
| Quality and oversight | `criteria`, `inspectors` | Add inspectors only for consequential output checks. |
| Progress display | `progress_format`, `progress_verbosity`, `progress_truncate` | Use `status` or `logs`; leave unset in normal production runs. |
| Advanced execution | `tasks`, `prompt`, `history`, `execution_params`, `evolve` | Use only when the execution strategy requires them. `execution_params.max_iterations` is deprecated. |
| Transport | `timeout`, `wait_time`, `run_retries`, `run_retry_wait` | Client wait/retry controls, not agent behavior. |

There is no `output_format=`, `expected_output=`, or `budget=` run override in SDK `0.2.47`. Set output contracts on `Agent`; set limits through `agent.budget` before running. `run_response_generation` is deprecated/ignored; do not use it in new builds.

## Shared memory (across conversations)

Use only when long-term memory is required. Always isolate by user/customer identity.

```python
memory = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Stores durable account context.",
    config={
        "max_memory_size": 256,
        "size_management_policy": "summarize",
    },
    allowed_actions=["insert", "get"],
).save()

memory.run(
    action="insert",
    data={"identifier": "customer-123", "content": "Prefers weekly summaries."},
)
```

Never use a global/default identity for multi-user agents. Verify identity forwarding in teams.

## Knowledge base vs skill

- Use an aiR knowledge-base tool for a large corpus queried by relevance.
- Use `aix.Skill` for a bounded playbook/reference that should always be in context.

```python
skill = aix.Skill(
    name="Support Playbook",
    description="Approved support workflow and policies.",
    file_path="/absolute/path/to/playbook.md",
).save()

agent = aix.Agent(
    name="Support Agent",
    description="Answers support questions using the approved playbook.",
    instructions="Follow the attached playbook.",
    skills=[skill],
).save()
```

`Session`, `Budget`, and `Skill` require SDK `0.2.47` or later.

## Runtime Code Execution vs build-time Python Sandbox

Use Code Execution (`698cda188bbb345db14ac13b`) when the agent must write and execute arbitrary code at runtime. Use Python Sandbox (`688779d8bfb8e46c273982ca`) when you can define the deterministic function during the build. See `integration-playbooks.md`.

## Portability

A portable build must depend only on:
- the API key/environment;
- stable first-party marketplace asset IDs/paths;
- integration definitions from which workspace-local tools are created;
- inline custom code for agent-specific Python Sandbox tools.

Never hardcode a workspace-bound OAuth, connector, MCP, or custom tool instance ID in reusable build code.

## Final configuration summary

After deployment, show only the resolved configuration:

```yaml
architecture: single | team
model: platform default | explicit model
output: markdown | text | json
tools:
  - name: ...
    allowed_actions: [...]
integrations:
  - name: ...
    connection: connected | user action required
knowledge: none | session | shared memory | index | skill
runtime_code: enabled | disabled
budget:
  max_cost: ...
  max_duration_seconds: ...
  max_iterations: ...
inspectors: [...]
```

Then provide `https://app.aixplain.com/agents/<AGENT_ID>` and verification evidence.

## Run or debug an existing agent

Load by ID (preferred) or exact search match. Reproduce with the user's query before changing configuration.

```python
agent = aix.Agent.get("<AGENT_ID>")
result = agent.run(query="Reproduce the reported behavior.")

for step in result.data.steps or []:
    print(step.get("action"), step.get("unit", {}).get("name"))
print(result.data.governance)
print(result.data.output)
```

For long runs, use SDK polling rather than custom HTTP loops:

```python
started = agent.run_async(query="Run the full analysis.")
result = agent.sync_poll(started.url)
```

Fix the smallest responsible layer—tool, action scope, description, instructions, budget, or model—save in place, and rerun the same reproduction plus regression checks.

## Reusable run variables

SDK `0.2.47` supports `{{variable}}` placeholders in instructions and descriptions. Use them when one deployed agent should handle repeatable variants without cloning:

```python
agent = aix.Agent(
    name="Briefing Agent",
    description="Creates a {{briefing_type}} briefing.",
    instructions="Create a {{briefing_type}} briefing for {{audience}}.",
).save()

result = agent.run(
    query="Use the supplied context.",
    variables={"briefing_type": "customer", "audience": "account team"},
)
```

Do not use variables for secrets; pass credentials only through approved integration/auth flows.

## Export an existing agent to portable SDK v2 code

Use the SDK, not raw REST:

```python
agent = aix.Agent.get("<AGENT_ID>")
config = agent.to_dict()
members = agent.agents or []
```

Recursively map the root and each member to `aix.Agent(...)` constructor arguments. Preserve name, description, instructions, output format, expected output, model configuration, budget, skills, inspectors, and action scopes.

Portability rules for generated code:
- Read `AIXPLAIN_API_KEY` from the environment; never embed it.
- Fetch stable first-party marketplace assets by path/ID.
- Recreate OAuth, connector, MCP, database, and custom tools from their integration definitions; do not export workspace-bound tool-instance IDs as portable dependencies.
- Inline agent-specific Python Sandbox source using `config={"code": ..., "function_name": ...}`.
- Emit subagents before the root and attach them with `agents=[...]`.
- End with `.save()` and print `https://app.aixplain.com/agents/<AGENT_ID>`.
- Run the generated script in a clean workspace when practical and compare the resolved schema before calling the export portable.

## Choose the execution strategy

The schema selects the strategy; there is no separate `strategy=` flag:

| Configuration | Use when | Behavior |
|---|---|---|
| neither `planner` nor `tasks` | the next step depends on observations | adaptive plan/act/observe loop |
| `tasks=[...]` only | the workflow and dependencies are known | deterministic task graph |
| `planner=<model>` | the goal needs decomposition but execution should then be structured | planner creates the graph, then tasks execute |

Static task example:

```python
from aixplain.v2.agent import Task

collect = Task(
    name="collect",
    instructions="Collect the required account evidence.",
    expected_output="Evidence with sources",
)
summarize = Task(
    name="summarize",
    instructions="Create the final briefing from collected evidence.",
    expected_output="A concise markdown briefing",
    dependencies=[collect],
)
agent = aix.Agent(
    name="Static Briefing Agent",
    description="Runs a predictable evidence-to-briefing workflow.",
    instructions="Complete each task and preserve source attribution.",
    tasks=[collect, summarize],
).save()
```

Use a planner when task shape varies by request:

```python
agent = aix.Agent(
    name="Planning Analyst",
    description="Plans and executes multi-step analyses.",
    instructions="Plan the analysis, execute it, and verify the conclusion.",
    planner="<PLANNING_MODEL_ID>",
).save()
```

If both `planner` and `tasks` are present, treat the supplied tasks as seeds for the plan. Do not offer a “dynamic” strategy; it is not a stable v2 SDK mode.

## Reasoning effort and per-role models

Reasoning effort is model-specific. Check availability before setting it:

```python
llm = aix.Model.get("<MODEL_ID>")
if "reasoning_effort" in llm.inputs.keys():
    llm.inputs.reasoning_effort = "high"   # model-supported values only

agent = aix.Agent(name="Reasoning Agent", description="...", instructions="...", llm=llm)
```

For planned workflows, configure expensive reasoning only where it adds value:

```python
planner = aix.Model.get("<PLANNER_MODEL_ID>")
if "reasoning_effort" in planner.inputs.keys():
    planner.inputs.reasoning_effort = "high"

agent = aix.Agent(
    name="Planning Analyst",
    description="Plans and executes variable multi-step analyses.",
    instructions="Plan, execute, verify, then answer concisely.",
    planner=planner,
).save()
```

SDK `0.2.47` accepts and persists `llm`, `planner`, `supervisor`, and `response_generator`, but that does not mean the runtime applies every role. Freshly verified against `aixplain-agents` `1.3.0` (`028a81ac`): only `llm` and `planner` model-parameter buckets are applied. `supervisor`, `responder`, and `inspector` buckets emit “not applied yet” warnings. The dedicated second-LLM response-generator pass and `run_response_generation` are deprecated and ignored. Do not configure `response_generator` in new builds; treat the field as compatibility-only until runtime support is restored and verified.
