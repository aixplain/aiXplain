# Agent lifecycle and portability (SDK v2)

Read this to update, debug, export, or present an existing aixplain agent without changing its identity or widening access.

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

`0.2.47` fixed the earlier `Agent.get()`/`save()` default-LLM overwrite. If behavior suggests a regression, compare the backend model before/after and follow `reliability-guidelines.md` rather than adding a permanent workaround without evidence.

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
- Generate `llm=...`, never unsupported `llm_id=...`; keep iteration limits in `agent.budget`, never top-level `max_iterations`.
- Before presenting an export, run `python -m py_compile <generated_file>`, inspect constructor arguments against SDK `0.2.47`, and ensure save/run side effects are guarded by `if __name__ == "__main__":`.
- Run the generated script in a clean workspace when practical and compare the resolved schema before calling the export portable.
