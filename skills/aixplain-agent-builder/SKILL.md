---
name: aixplain-agent-builder
description: A skill to build, deploy, and run production-grade AI agents on aiXplain.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Agent Builder

Build, deploy, run, and manage aiXplain agents — single agents, team agents, tools, and OAuth integrations.

## How It Works

This skill accepts the following commands:

- **Build agent** — plan, search tools, create tools, assemble and save the agent
- **Deploy agent** — save and share Studio links for visual editing and analytics
- **Run agent** — execute sync or async and return the output
- **Debug agent** — diagnose tool, action, OAuth, or runtime issues
- **Export agent** — generate a standalone Python script from a deployed agent

## 1. Setup

Always install/upgrade to the latest SDK before doing anything: `pip install --upgrade aixplain`.

This skill is verified against **SDK v0.2.44**. If the installed version differs, tell the user.

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from aixplain import Aixplain

env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path.write_text("# Get your key from https://platform.aixplain.com → Settings → API Keys\nAIXPLAIN_API_KEY=\n")
    print(f"Created {env_path.resolve()} — paste your API key, then re-run.")
    raise SystemExit(1)

api_key = os.getenv("AIXPLAIN_API_KEY") or os.getenv("AIXPLAIN_KEY_NUR")
if not api_key:
    print(f"No API key found. Open {env_path.resolve()} and paste your key.")
    raise SystemExit(1)

os.environ["AIXPLAIN_API_KEY"] = api_key
aix = Aixplain(api_key=api_key)
```

## 2. Plan

Before building, present a plan to the user covering: agent name, description, instructions, which tools/integrations to use, and whether it's a single or team agent. Wait for approval before proceeding.

**Always search before creating or hardcoding a tool or integration.** `Tool`, `Model`, and `Integration` all support `.search(query=...).results`. Never say "not available" without searching first.

```python
results = aix.Tool.search(query="web search").results
# Names may be concatenated (e.g. "Googledrive"). Normalize before comparing.
```

If a needed capability has no marketplace tool or integration, announce you'll build it as a **Python Sandbox** function (see `references/integration-playbooks.md § 4`).

## 3. Create Tools

Three paths, in order of preference:

```python
# Path A: Marketplace tool by ID
tool = aix.Tool.get("698cda188bbb345db14ac13b")  # Code Execution

# Path B: Non-OAuth integration (KB, SQLite)
# READ references/integration-playbooks.md for config payloads.
# Ask the user for any missing inputs — never invent placeholders.
# Always create fresh; do not reuse by name unless explicitly asked.
tool = aix.Tool(name="KB Search", description="Search product docs",
    integration="6904bcf672a6e36b68bb72fb", allowed_actions=["search", "get"]).save()

# Path C: OAuth integration (Gmail, Slack, Jira, Google Drive)
# READ references/integration-playbooks.md § 5 for full workflow.
# (1) integration = aix.Integration.get("<ID>")
# (2) integration.list_actions() → discover action names
# (3) Create tool with allowed_actions in constructor
# (4) User completes OAuth via redirect URL emitted at .save()
# (5) Attach in-memory tool object to agent and save

# Path D: Python Sandbox (last resort)
# READ references/integration-playbooks.md § 4 for config shape.
```

## 4. Build Agent

Agents use the platform default LLM — do not specify `llm` unless the user requests a specific model.

```python
agent = aix.Agent(
    name="My Agent", description="...", instructions="...",
    tools=[tool], output_format="markdown",
).save()
```

If `save()` raises `name_already_exists`, ask the user: update existing or create with a new name.

## 5. Deploy & Run

After deploy, share these links with the user:
- **Visual builder:** `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- **Analytics:** `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

```python
# Sync
result = agent.run(query="...", executionParams={"maxTokens": 6000}, runResponseGeneration=True)
print(result.data.output)

# Async polling
import requests, time
ar = agent.run_async(query="...")
for _ in range(30):
    time.sleep(10)
    raw = requests.get(ar.url, headers={"x-api-key": api_key}).json()
    if raw.get("status", "").upper() in ("SUCCESS", "FAILED"):
        print(raw["data"]["output"]); break
```

## 6. Debugging

### Inspect Intermediate Steps

```python
result = agent.run(query="...")

# Step-by-step trace: thought, action, tool used, input/output, tokens
for step in result.data.steps:
    print(step['thought'], step['action'], step['unit']['name'])

# Aggregate costs and timing
stats = result.data.execution_stats
print(stats['credits'], stats['runtime'], stats['api_calls'])
```

Or view traces visually in Studio: `https://studio.aixplain.com/build/<AGENT_ID>/schema`

## Quick Asset IDs

| Type | Name | ID |
|------|------|----|
| Tool | Tavily Web Search | `6931bdf462eb386b7158def3` |
| Tool | Code Execution | `698cda188bbb345db14ac13b` |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` |
| Tool | Firecrawl API | `69442021f2e6cb73e286ff0f` |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` |
| Integration | Gmail | `6864328d1223092cb4294d30` |
| Integration | Slack | `686432941223092cb4294d3f` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |
| Integration | aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| Integration | PostgreSQL | `693ac6e8217c7b13b480970f` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | Python Sandbox | `688779d8bfb8e46c273982ca` |

## Reference Files

- `references/integration-playbooks.md` — config payloads, file upload, authoring constraints, and OAuth workflow for all integration types
- `references/agent-patterns.md` — team agents, updating deployed agents, inspectors, export to Python, Code Execution vs Python Sandbox
- `references/inspector-analytics.md` — inspector policies and analytics schema

## External Links

- **Docs:** https://docs.aixplain.com
- **Pricing:** https://aixplain.com/pricing
- **Studio:** https://studio.aixplain.com
