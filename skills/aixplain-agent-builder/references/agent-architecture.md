# Agent architecture (SDK v2)

Read this for agent shape, teams, budgets, sessions, memory, knowledge, or choosing build-time versus runtime code.

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

## Sessions (one conversation)

```python
session = aix.Session(agent=agent, name="customer-thread").save()
first = agent.run("My company is Acme.", session=session)
second = agent.run("Which company did I mention?", session=session)
```

Sessions are synchronous. `run_async(..., session=...)` is not supported.

## Choose the right context mechanism

| Need | Use | Do not use it for |
| --- | --- | --- |
| A self-contained request | no retained context | facts needed only for one run |
| Continuity in one active conversation | `Session` | durable preferences or cross-conversation recall |
| Confirmed user or account context across conversations | Shared Memory | a large document corpus, secrets, or unverified model inferences |
| Retrieval from many documents by relevance | aiR Knowledge Base | durable per-user preferences or conversation state |
| A stable policy, procedure, or playbook always needed by the agent | `aix.Skill` | mutable customer facts or personal history |

## Shared memory (across conversations)

Use Shared Memory only when the agent must recall **confirmed, useful context** for the same user, customer, or account in a later conversation—for example, a reporting preference, approved account facts, or an agreed working convention.

Before enabling it:

1. Confirm that cross-conversation retention is required by the request; do not persist context merely because it might be useful later.
2. Explain the retained scope when it includes personal or customer information, and ask before enabling retention when that choice is not already clear from the request.
3. Store the minimum durable fact. Never store API keys, credentials, access tokens, payment data, or unverified model conclusions.
4. Use a stable, explicit `identifier` for the user/customer/account. Never use a global/default identity in a multi-user agent.
5. In teams, verify that every memory read and write carries the same intended identity, then test that one identity cannot retrieve another identity's context.

```python
memory = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Stores confirmed, durable account context for the current account only.",
    config={
        "max_memory_size": 256,
        "size_management_policy": "summarize",
    },
    allowed_actions=["insert", "get"],
).save()

account_id = "customer-123"
memory.run(
    action="insert",
    data={"identifier": account_id, "content": "Prefers weekly summaries."},
)
```

Use a `Session` instead when the context belongs only to the current conversation. Use a Knowledge Base when the agent must search a larger source corpus rather than recall durable account-specific facts.

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

Use Code Execution (`698cda188bbb345db14ac13b`) when the agent must write and execute arbitrary code at runtime. Use Python Sandbox (`688779d8bfb8e46c273982ca`) when you can define the deterministic function during the build. See `integration-build-and-data.md`.
