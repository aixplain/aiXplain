# Agent runtime (SDK v2)

Read this for per-run controls, stateful or stateless execution, execution strategy, and model reasoning configuration.

## Invocation and runtime controls

Configure tools, model, `output_format`, `expected_output`, and the default `agent.budget` on the agent. `run()` controls one execution:

```python
# Stateless reusable run: variables are currently unreliable; validate the result.
result = agent.run(
    query="Create the customer briefing for Acme from the supplied context.",
    variables={"account_name": "Acme"},
    identifier="customer-123",
    attachments=["/absolute/path/to/brief.pdf"],
    criteria="Include sources and flag unsupported claims.",
)

# Stateful conversation: resolve non-secret values into the query; do not pass variables.
follow_up = agent.run(
    query="For Acme, turn the prior briefing into an executive summary.",
    session=session,
)
```

| Need | `run()` controls | Notes |
|---|---|---|
| Conversation | `query`, `session` | `session` accepts a `Session` or ID; do not combine it with `variables`. |
| Per-run input | `variables`, `identifier`, `attachments` | Variables are currently unreliable. For stateful runs, resolve non-secret values into `query`; use `attachments`, not deprecated `files`. |
| Quality and oversight | `criteria`, `inspectors` | Add inspectors only for consequential output checks. |
| Progress display | `progress_format`, `progress_verbosity`, `progress_truncate` | Use `status` or `logs`; leave unset in normal production runs. |
| Advanced execution | `tasks`, `prompt`, `history`, `execution_params`, `evolve` | Use only when the execution strategy requires them. `execution_params.max_iterations` is deprecated. |
| Transport | `timeout`, `wait_time`, `run_retries`, `run_retry_wait` | Client wait/retry controls, not agent behavior. |

There is no `output_format=`, `expected_output=`, or `budget=` run override in SDK `0.2.47`. Set output contracts on `Agent`; set limits through `agent.budget` before running. `run_response_generation` is deprecated/ignored; do not use it in new builds.

## Reusable run variables

SDK `0.2.47` exposes `variables=`, but current platform substitution is unreliable and the SDK rejects `session=...` combined with `variables=...`. Until that is repaired, do not promise placeholder substitution.

For a stateless run, use `variables=` only when a focused verification proves substitution occurred. For a stateful run—or whenever correctness matters—resolve non-secret values into the per-run query instead:

```python
account_name = "Acme"  # Never resolve secrets into prompts.
query = f"Create a customer briefing for {account_name} from the supplied context."
result = agent.run(query=query, session=session)
```

Pass credentials only through approved integration/auth flows.

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
