---
name: aixplain-agent-builder
description: Build, configure, deploy, run, debug, export, verify, and update aixplain agents from a user's problem or intent using the Python SDK v2. Use for single agents, teams, marketplace tools, integrations, custom Python tools, runtime Code Execution, knowledge, sessions, budgets, and inspectors. The skill works autonomously, asks only when an external integration or secret needs the user's decision, and returns a working app link.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aixplain agent builder

Turn a user's intent into a working, verified aixplain agent. Do the SDK work yourself; do not make the user design the schema, select routine defaults, or debug tracebacks.

> **Current stable SDK:** `aixplain==0.2.47` (verified against the public release and repository on 2026-08-22).
> **SDK v2 only:** use `from aixplain import Aixplain`. Never use `AgentFactory`, `ModelFactory`, `TeamAgentFactory`, `aixplain.factories`, or other v1 APIs. If docs or an error lead to v1, translate the approach to v2 and follow `references/reliability-guidelines.md`.

## Modes

Infer the mode from the request; do not make the user choose:

- **Build:** turn an intent into a configured, deployed, verified agent.
- **Run/debug:** load an agent by ID or exact name, reproduce the problem, inspect steps/governance/tool behavior, fix in place, and re-verify.
- **Export:** load an existing agent and recursively generate portable SDK v2 code for its tools, skills, inspectors, and subagents; syntax- and constructor-validate it before presenting it. See `references/agent-lifecycle.md`.

## Operating contract

1. **Start from intent.** Infer the job, users, inputs, outputs, success criteria, and likely next request. Prefer one capable agent; use a team only when roles genuinely need different tools, context, or delegation.
2. **Do not interview the user about routine configuration.** Choose names, descriptions, instructions, output format, budgets, models, action scopes, and iteration limits using safe defaults.
3. **Search before building.** Use the bundled Marketplace Search MCP when available to discover assets, actions, and input schemas before declaring a capability missing. Prefer native first-party assets, then supported integrations, then custom code.
4. **Ask only at the connection boundary.** Pause only when the user must choose whether to connect an external integration, authorize OAuth, provide a provider credential, or approve a consequential/irreversible action. Never invent secrets.
5. **Build proactively.** Anticipate the next useful capability when it is low-risk and clearly implied. Do not silently add access to external systems, broad permissions, or expensive behavior.
6. **Show configuration when it is ready.** After resolving assets and defaults, present the compact final schema so the user can request changes; do not expose a stream of intermediate choices.
7. **Deploy and prove it.** `save()` is not completion. Run realistic checks, inspect tool usage and governance, fix failures, then provide the app link.
8. **Never overwrite by accident.** If the request clearly targets an existing agent, update it in place. For a new build whose exact name already exists, choose a descriptive unique name and report the collision; do not overwrite or create opaque `(1)` duplicates.
9. **Apply verified reliability guidance.** Follow `references/reliability-guidelines.md` for known-safe patterns; when behavior differs, state the observation and use only a confirmed workaround.

## Standalone compatibility

This skill must work when it is installed directly as a Claude Code skill or used by an agent host that does not support Claude Code plugins or MCP servers. The aixplain Python SDK and `AIXPLAIN_API_KEY` are the only runtime requirements for core build, run, debug, update, verify, and export workflows.

- Treat the bundled Marketplace Search MCP as an optional discovery enhancement, never as a prerequisite.
- When that MCP is unavailable, incompatible, or unauthenticated, use the SDK searches in **Resolve capabilities** and continue with the best supported asset, integration, or custom Python Sandbox tool.
- Do not report a capability as unavailable merely because the plugin or MCP cannot load. State that Marketplace discovery was skipped only when it materially limits the answer.
- Keep connection consent, least-privilege scopes, SDK v2 validation, and realistic verification requirements unchanged in standalone mode.

## 1. Setup

Install the exact tested stable release:

```bash
python3 -m pip install --upgrade "aixplain==0.2.47"
```

Read the key from a secret source and pass it explicitly. Never print, commit, or embed it in generated code.

```python
import os
from aixplain import Aixplain

api_key = os.environ["AIXPLAIN_API_KEY"]
aix = Aixplain(api_key=api_key)
```

Keys are workspace-specific. `Forbidden resource` across known-valid assets usually means the key belongs to another workspace.

## 2. Derive the schema

Silently draft this internal blueprint from the user's intent:

```yaml
name: concise job-based name
description: who it helps and the outcome
instructions: goal, workflow, tool-use rules, constraints, completion criteria
architecture: single | team
inputs: what a run needs
output_format: markdown | text | json
tools: minimum required capabilities
integrations: external systems requiring connection
knowledge_or_memory: none | session | shared-memory | knowledge-base | skill
runtime_code: true only if the agent must write/run code during a run
governance: least privilege, budget, inspectors when justified
verification: one realistic test per capability
```

Defaults:
- Use the platform default LLM unless the user requests a model or the default is incompatible with a tool.
- Use `markdown` for human deliverables and `json` only when another system consumes the output.
- Use a single agent unless specialist delegation improves reliability.
- Scope every tool to the smallest non-empty `allowed_actions` set.
- Give each tool a concise, action-oriented description that states when to use it and what it returns; distinct descriptions improve tool and subagent routing.
- Add runtime Code Execution only when the deployed agent needs calculations, transforms, plots, file processing, or dynamic code during a run.
- Use a Python Sandbox custom tool when the missing capability is deterministic code authored at build time.

## 3. Resolve capabilities

Search first:

```python
tools = aix.Tool.search(query="web search").results
integrations = aix.Integration.search(query="calendar").results
models = aix.Model.search(query="reasoning").results
```

For broad discovery, use the aixplain Marketplace Search tool:

```python
search = aix.Tool.get("6960f934f316da19e5f22494")
result = search.run(action="search", data={"query": "microsoft calendar"})
for kind in ("agent", "model", "tool", "integration"):
    for item in result.data.get(kind, {}).get("results", []):
        print(kind, item["name"], item["path"], item["id"])
```

Selection order:
1. Existing first-party marketplace tool.
2. Existing native integration.
3. Supported connector integration.
4. Custom Python Sandbox tool with `config={"code": ..., "function_name": ...}`.

If an existing integration can do the job, ask whether the user wants to connect it. If no suitable tool exists, develop the missing deterministic tool with `code=` rather than asking the user to invent the implementation. Read `references/integration-connections.md` before connecting, and `references/integration-build-and-data.md` before authoring code.

### Build-time code vs runtime code

- **Python Sandbox integration** (`688779d8bfb8e46c273982ca`): you write fixed code now. Use when a capability is missing and should become a deterministic tool.
- **Code Execution tool** (`698cda188bbb345db14ac13b`): the agent writes/runs code later. Add only when runtime work actually requires it.

## 4. Build

```python
agent = aix.Agent(
    name="Customer Briefing Agent",
    description="Produces an evidence-backed customer briefing.",
    instructions=(
        "Gather the required evidence with the attached tools, reconcile conflicts, "
        "and return a concise briefing with sources. Do not claim completion until "
        "all required sections are present."
    ),
    tools=[tool],
    output_format="markdown",
    max_tokens=6000,
)
agent.save()
```

For structured output, set it on the agent:

```python
agent = aix.Agent(
    name="Lead Qualifier",
    description="Qualifies a lead against the supplied criteria.",
    instructions="Evaluate every criterion and explain the result.",
    output_format="json",
    expected_output={
        "type": "object",
        "properties": {
            "qualified": {"type": "boolean"},
            "reasons": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["qualified", "reasons"],
    },
)
agent.save()
```

For teams, budgets, sessions, memory, and knowledge, read `references/agent-architecture.md`. For run controls and execution strategy, read `references/agent-runtime.md`. For updates or exports, read `references/agent-lifecycle.md`; read `references/inspectors.md` for runtime validation.

## 5. Integration checkpoint

Do not ask for general approval of the inferred schema. Ask a focused question only when connection is required:

- Name the integration and why it is needed.
- List the minimum actions requested.
- State whether OAuth or a provider key is required.
- Offer the no-connection alternative, if one exists.

After consent, create the tool from the integration in the current workspace and return the generated connect URL. Never hardcode a workspace-bound integration tool instance.

## 6. Verify before reporting success

Run one realistic query per capability. For every run:

```python
result = agent.run(query="Create this week's customer briefing from the available sources.")

used_units = [
    step.get("unit", {}).get("name")
    for step in (result.data.steps or [])
    if isinstance(step, dict)
]

governance = result.data.governance or {}
assert governance.get("status", "ALLOWED") == "ALLOWED", governance
print(result.data.output)
print(used_units)
```

Completion gate:
- Every intended tool fired at least once when relevant.
- Output satisfies the user's requested result and format.
- Governance did not block the run; run `SUCCESS` alone is insufficient.
- Generated files have clickable HTTPS download links.
- Team output is synthesized, not an internal `delegate_task` trace.
- Integration permissions are the minimum required.
- Actual spend comes from `result.data.execution_stats["credits"]`.

If a tool works standalone but fails inside the agent, isolate the orchestration issue before changing the schema. Apply the closest safe practice in `references/reliability-guidelines.md` and report the observed behavior clearly.

## 7. Final response

Lead with the result, not the code. Include:

1. What the agent does.
2. App link: `https://app.aixplain.com/agents/<AGENT_ID>`.
3. Compact final configuration: architecture, tools/integrations, action scopes, output, memory/knowledge, model override if any, budget/guardrails.
4. Verification evidence: test prompts, tools observed, pass/fail, governance status.
5. Connection link or remaining user action, only if required.
6. One likely next improvement, phrased as optional rather than another setup questionnaire.

Keep build code available on request. When the user asks for integration code, provide a complete v2 snippet based on the relevant `integration-connections.md` or `integration-build-and-data.md` reference.

## Updating an existing agent

SDK `0.2.47` has a critical hydration bug: `Agent.get()` can populate each tool's `allowed_actions` from every returned parameter definition instead of the backend's persisted `actions` scope. Before any get→mutate→save cycle, fetch the raw agent and reapply its stored scopes:

```python
agent_id = "<AGENT_ID>"
raw = aix.Agent.context.client.get(f"v2/agents/{agent_id}")
agent = aix.Agent.get(agent_id)

scopes_by_id = {
    item.get("id"): list(item.get("actions") or [])
    for item in (raw.get("tools") or [])
    if isinstance(item, dict) and item.get("id")
}
for tool in agent.tools or []:
    if getattr(tool, "id", None) in scopes_by_id:
        tool.allowed_actions = scopes_by_id[tool.id]

agent.instructions = "Updated instructions..."
agent.save()
```

This keeps the ID and external references stable without widening permissions. Verify behavior and raw persisted scopes again after every update. See `references/agent-lifecycle.md` and `references/reliability-guidelines.md`.

## Reliability follow-up

Use `references/reliability-guidelines.md` to choose a safe, verified path. If behavior differs, preserve a minimal redacted reproduction in local engineering notes and explain the confirmed workaround; do not invent a fix. Draft a public issue only after the user asks, targeting https://github.com/aixplain/aiXplain with SDK v2 examples only.

## Reference routing

- Marketplace discovery and exact MCP schemas: `../marketplace-search/references/effective-mcp-use.md`
- Connection consent, Slack, Web Search, OAuth, provider keys, MCP: `references/integration-connections.md`
- Custom Python tools, Code Execution, databases, knowledge, files: `references/integration-build-and-data.md`
- Agent shape, teams, budgets, sessions, memory, knowledge: `references/agent-architecture.md`
- Run controls, variables, execution strategy, reasoning models: `references/agent-runtime.md`
- Safe updates, debugging, portability, exports: `references/agent-lifecycle.md`
- Runtime inspectors and validation: `references/inspectors.md`
- Verified reliability practices and safe fallbacks: `references/reliability-guidelines.md`

## Stable asset IDs

| Type | Name | ID |
|---|---|---|
| Tool | Code Execution | `698cda188bbb345db14ac13b` |
| Tool | Marketplace Search | `6960f934f316da19e5f22494` |
| Tool | File Manager | `6a0216cffb2a801f1c41e32e` |
| Integration | Python Sandbox | `688779d8bfb8e46c273982ca` |
| Integration | Gmail | `6864328d1223092cb4294d30` |
| Integration | Slack | `686432941223092cb4294d3f` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Calendar | `686432901223092cb4294d36` |
| Integration | aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| Integration | PostgreSQL | `693ac6e8217c7b13b480970f` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |

Docs: https://docs.aixplain.com · App: https://app.aixplain.com · SDK: https://github.com/aixplain/aiXplain
