# Agent Patterns

Advanced agent patterns — team agents, updating deployed agents, inspectors, export, and tool details.
Linked from the main skill — consult when needed.

---

## Team Agent

```python
sub1 = aix.Agent(name="Researcher", instructions="Search and summarize.", tools=[search_tool]).save()
sub2 = aix.Agent(name="Writer", instructions="Write the final report.").save()
team = aix.Agent(name="Team Lead", instructions="Route to specialists.", subagents=[sub1, sub2]).save()
```

---

## Update a Deployed Agent

Deployed agents are mutable. Never recreate to change behavior — load, mutate, and `save()`. The agent ID, history, and external references stay intact.

Updatable fields:
- `agent.instructions` — system prompt
- `agent.description` — public-facing summary
- `agent.tools` — add, remove, or replace tools
- `agent.output_format` — `"markdown"` / `"text"` / `"json"`
- `agent.llm` — swap the underlying LLM. **Always assign to `.llm` (accepts the model ID string or a Model object). Never use `.llm_id` — that attribute exists but assigning it does NOT propagate to the save payload, so `save()` silently keeps the old model.**

You can also update attached tools without detaching them — change a tool's `description`, add files to a KB tool, or change `allowed_actions`. Mutate the tool object, call `tool.save()`, and the agent picks up the change on next run.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.llm = "<MODEL_ID>"   # correct — use `.llm`, NOT `.llm_id`
agent.save()

# Update an attached tool in place (no detach/reattach):
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated KB scope: includes 2026 docs."
kb_tool.save()
```

---

## Add Inspector

Inspectors attach to **team agents**. Use the **v2** inspector API (`aixplain.v2.inspector`) — it matches the v2 `Aixplain` client used everywhere in this skill. Do **not** import from `aixplain.modules.team_agent.inspector`; that path resolves to the v1 module and its `Inspector(auto=..., policy=...)` shape will fail with `ImportError`/`TypeError` under SDK v0.2.44.

```python
from aixplain.v2.inspector import (
    Inspector, InspectorActionConfig, InspectorAction,
    EvaluatorConfig, EvaluatorType, InspectorTarget, AUTO_DEFAULT_MODEL_ID,
)

inspector = Inspector(
    name="Content Gate",
    action=InspectorActionConfig(type=InspectorAction.ABORT),  # CONTINUE | RERUN | ABORT | EDIT
    evaluator=EvaluatorConfig(
        type=EvaluatorType.ASSET,
        asset_id=AUTO_DEFAULT_MODEL_ID,            # default LLM judge; or pass your own model ID
        prompt="Validate output meets policy. Fail if non-compliant.",
    ),
    targets=[InspectorTarget.OUTPUT],              # INPUT | STEPS | OUTPUT
)
team.inspectors = [inspector]
team.inspector_targets = [InspectorTarget.OUTPUT]
team.save()
```

Notes:
- `action=RERUN` is the only type that accepts `max_retries` / `on_exhaust` on `InspectorActionConfig`; any other type raises if you set them.
- `action=EDIT` requires an `editor=EditorConfig(...)`.
- For a function-based judge instead of an LLM, use `EvaluatorConfig(type=EvaluatorType.FUNCTION, function=<callable or source>)`.

After adding inspectors, validate with 3 prompts: allowed, denied, ambiguous. See `references/inspectors.md` for the full validation matrix.

---

## Export Agent to Python

Use the SDK — no raw REST. `Agent.get()` already returns the full config; serialize it and read `subagents` directly.

```python
agent = aix.Agent.get("<AGENT_ID>")
config = agent.to_dict()          # full agent config as a dict
subs = agent.subagents            # list of subagent objects (recurse the same way)
```

1. `aix.Agent.get(ID)` — load the agent (and read `.subagents` for team agents).
2. Read fields from the object or `agent.to_dict()` (name, description, instructions, output_format, llm, tools, max_tokens, inspectors).
3. Map those fields to SDK constructor args (`aix.Agent(...)`, `aix.Tool.get(...)`, inspector objects per § Add Inspector).
4. Generate a standalone `.py` that loads the key from env (`AIXPLAIN_API_KEY`) and rebuilds the agent with those args.

---

## Code Execution vs Python Sandbox

**Code Execution** (marketplace tool `698cda188bbb345db14ac13b`) — the agent writes and runs arbitrary Python at runtime. Secure cloud sandbox with internet access. Use for calculations, data transformations, visualizations, file processing, and fetching data from URLs/APIs.

- Use `print()` to return final results.
- If code generates files (plots, CSVs), print a JSON metadata list to stdout: `[{"name":"<display_name>","file":"<filename>"}]`. Without this, generated files are silently lost.

**Python Sandbox** (integration `688779d8bfb8e46c273982ca`) — same sandbox but with a pre-defined script authored at build time, not runtime. Use for deterministic tools with fixed inputs/outputs when no marketplace tool covers the capability. See `references/integration-playbooks.md § 4` for config shape and authoring constraints.
