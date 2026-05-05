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
- `agent.llm` — swap the underlying LLM (attribute name is `llm`, NOT `llm_id`)

You can also update attached tools without detaching them — change a tool's `description`, add files to a KB tool, or change `allowed_actions`. Mutate the tool object, call `tool.save()`, and the agent picks up the change on next run.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.save()

# Update an attached tool in place (no detach/reattach):
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated KB scope: includes 2026 docs."
kb_tool.save()
```

---

## Add Inspector

```python
from aixplain.modules.team_agent import InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy, InspectorAuto

inspector = Inspector(
    name="Content Gate",
    auto=InspectorAuto.ALIGNMENT,
    model_params={"prompt": "Validate output meets policy. Fail if non-compliant."},
    policy=InspectorPolicy.ABORT,
)
team.inspectors = [inspector]
team.inspector_targets = [InspectorTarget.OUTPUT]
team.save()
```

After adding inspectors, validate with 3 prompts: allowed, denied, ambiguous. See `references/inspector-analytics.md` for the full validation matrix.

---

## Export Agent to Python

1. `GET https://platform-api.aixplain.com/sdk/agents/{ID}` with `x-api-key`
2. Recurse `agents[].assetId` for subagents
3. Map API fields to SDK constructor args
4. Generate standalone `.py` with env-based key loading

---

## Code Execution vs Python Sandbox

**Code Execution** (marketplace tool `698cda188bbb345db14ac13b`) — the agent writes and runs arbitrary Python at runtime. Secure cloud sandbox with internet access. Use for calculations, data transformations, visualizations, file processing, and fetching data from URLs/APIs.

- Use `print()` to return final results.
- If code generates files (plots, CSVs), print a JSON metadata list to stdout: `[{"name":"<display_name>","file":"<filename>"}]`. Without this, generated files are silently lost.

**Python Sandbox** (integration `688779d8bfb8e46c273982ca`) — same sandbox but with a pre-defined script authored at build time, not runtime. Use for deterministic tools with fixed inputs/outputs when no marketplace tool covers the capability. See `references/integration-playbooks.md § 4` for config shape and authoring constraints.
