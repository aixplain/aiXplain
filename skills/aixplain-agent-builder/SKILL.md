---
name: aixplain-agent-builder
description: Build, deploy, run, debug, export, and manage aiXplain v2 agents via the Python SDK and REST API.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Agent Builder

Build, deploy, run, debug, export, and manage aiXplain v2 agents. Handles single agents, team agents, inspectors, tools, and OAuth integrations.

## Capabilities

- Create and update single and team agents with tools, integrations, and inspectors
- Run agents synchronously or with async polling
- Export existing agents to reproducible Python scripts
- Wire OAuth integrations (Gmail, Slack, Jira, Google Drive) via REST
- Connect non-OAuth integrations (Knowledge Base, PostgreSQL, SQLite, Python Sandbox, MCP)
- Add inspector policies (ABORT, ADAPTIVE, RERUN) with validation matrix

## Setup

**Always install/upgrade to the latest aiXplain SDK before doing anything**: `pip install --upgrade aixplain`. This skill is verified against **aiXplain SDK v0.2.44**. At the start of every session, check the installed version and:

- If older than 0.2.44 → run `pip install --upgrade aixplain` and tell the user it has been upgraded.
- If newer than 0.2.44 → tell the user explicitly: *"This skill was authored against aiXplain v0.2.44 but you are running v<X.Y.Z>. Some behaviors (especially OAuth tool action discovery and search indexing) may have changed."* Then proceed cautiously and verify each step.

```python
import importlib.metadata
SKILL_VERIFIED_VERSION = "0.2.44"
installed = importlib.metadata.version("aixplain")
if installed != SKILL_VERIFIED_VERSION:
    print(f"NOTE: aiXplain {installed} installed; this skill is verified against {SKILL_VERIFIED_VERSION}.")
```

Also requires an aiXplain API key set as `AIXPLAIN_API_KEY` (or `TEAM_API_KEY`).

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from aixplain import Aixplain

for env_path in [Path.home() / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(env_path)
        break

api_key = os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")
os.environ["TEAM_API_KEY"] = api_key
os.environ["AIXPLAIN_API_KEY"] = api_key
aix = Aixplain(api_key=api_key)
```

## Search First (Core Principle)

**Always search before you create, hardcode, or claim something is missing.** `Agent`, `Tool`, `Model`, and `Integration` all expose the same `.search()` syntax. Use it before falling back to the Quick Asset IDs table or announcing that an asset is unavailable.

```python
# Unified syntax — works for Agent, Tool, Model, Integration
results = aix.Agent.search(query="My Agent").results
results = aix.Tool.search(query="web search").results
results = aix.Model.search(query="gpt-5").results
results = aix.Integration.search(query="google drive").results

# Filter client-side. Names may be concatenated (e.g. "Googledrive", "Googlesheets").
# Normalize whitespace before comparing.
def _norm(s): return "".join(s.lower().split())
match = next((r for r in results if _norm(r.name) == "googledrive"), None)
print(match.id, match.name)
```

When the user asks for an integration/tool/model that isn't in the Quick Asset IDs table, **run the matching `.search()` first**. Only report "not found" after the search returns no match.

## Build Agent

Apply the search-first principle:

```python
name = "My Agent"
match = next((r for r in aix.Agent.search(query=name).results if r.name == name), None)
if match:
    agent = aix.Agent.get(match.id)
    agent.instructions = "Updated instructions."
    agent.save()
else:
    agent = aix.Agent(
        name=name, description="...", instructions="...",
        tools=[tool], output_format="markdown",
    ).save()
```

## Run Agent

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

### REST / cURL (on-demand, language-agnostic)

Once an agent is deployed it can be invoked over plain HTTP — no SDK required. `sessionId` is optional; pass the same value across calls to get multi-turn memory.

```bash
curl -X POST 'https://platform-api.aixplain.com/sdk/agents/<AGENT_ID>/run' \
  -H 'x-api-key: <YOUR_API_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "<USER_QUERY>",
    "sessionId": "<OPTIONAL_SESSION_ID_FOR_MULTI_TURN>"
  }'

# Response:
# { "requestId": "...", "sessionId": "...",
#   "data": "https://platform-api.aixplain.com/sdk/agents/<requestId>/result" }
#
# Then GET the `data` URL with the same x-api-key header to poll for the result.
```

## Update a Deployed Agent (in place)

**Deployed agents are mutable.** Never recreate to change behavior — load the existing agent, mutate, and `save()`. The agent ID, history, and any external references stay intact.

You can update on the live agent:

- `agent.instructions` — system prompt
- `agent.description` — public-facing summary
- `agent.tools` — add, remove, or replace tools (the agent itself is not detached/recreated)
- `agent.output_format` — `"markdown"` / `"text"` / `"json"`
- `agent.llm_id` — swap the underlying LLM (see Quick Asset IDs for model IDs)

You can also update **attached tools without detaching them** from the agent — e.g. change a tool's `description`, add a new file to a Knowledge Base tool, or change `allowed_actions`. Mutate the tool object and call `tool.save()`; the agent will pick up the change on its next run.

```python
agent = aix.Agent.get("<AGENT_ID>")
agent.instructions = "New system prompt..."
agent.output_format = "json"
agent.llm_id = "698c87701239a117fd66b468"  # Claude Opus 4.6
agent.save()

# Update an attached tool in place (no detach/reattach):
kb_tool = next(t for t in agent.tools if t.name == "Product KB")
kb_tool.description = "Updated KB scope: includes 2026 docs."
kb_tool.save()
```

## After Deploy: Share Visual Links

Whenever you deploy or update an agent, share these Studio links with the user so they can edit, trace, and monitor it visually:

- **Visual builder / trace viewer:** `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- **Analytics dashboard:** `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

## External References

- **Docs:** https://docs.aixplain.com
- **Pricing:** https://aixplain.com/pricing
- **Studio (visual builder + analytics):** https://studio.aixplain.com

## Create Tools

```python
# Path A: Integration-backed (KB, SQLite, Python Sandbox, MCP)
# IMPORTANT: Only the Knowledge Base connects with just `integration` + `allowed_actions`.
# SQLite, Python Sandbox, and MCP each require a `config={...}` payload (uploaded
# .db URL, code+function_name, mcp URL, etc.). BEFORE building any non-OAuth tool,
# READ references/integration-playbooks.md — it documents the exact `config` shape,
# authoring constraints (Python Sandbox), and file-upload steps (SQLite) per
# integration. Do not guess the shape. If a required input is missing (KB source
# file, SQLite .db path, Python script body, MCP URL + API token), ASK THE USER —
# do not invent placeholders. Always create a fresh connected tool; do not reuse
# by name unless the user explicitly asks you to.
tool = aix.Tool(name="KB Search", description="Search product docs",
    integration="6904bcf672a6e36b68bb72fb", allowed_actions=["search", "get"]).save()

# Path B: Marketplace tool by ID
tool = aix.Tool.get("698cda188bbb345db14ac13b")

# Path C: OAuth (Gmail, Slack, Jira, Google Drive)
# Step 1 — create the OAuth tool via the Models execute endpoint.
import requests
MODELS_RUN_URL = "https://models.aixplain.com/api/v2/execute"
H = {"x-api-key": api_key, "Content-Type": "application/json"}
resp = requests.post(f"{MODELS_RUN_URL}/{INTEGRATION_ID}", headers=H,
    json={"name": "GDrive Writer", "description": "Write files to Drive."}).json()
tool_id = resp["data"]["id"]
redirect_url = resp["data"].get("redirectURL")  # CRITICAL: user must visit this

# Step 2 — STOP and have the user complete OAuth at redirect_url before continuing.
# Until OAuth is authorized, tool.actions will be empty and any agent run that
# touches the tool will hang/timeout.
print(f"Authorize: {redirect_url}")

# Step 3 — after OAuth, load the tool via the SDK and set allowed_actions.
oauth_tool = aix.Tool.get(tool_id)              # SDK handles OAuth tools fine
assert len(list(oauth_tool.actions)) > 0, "OAuth not yet completed"
oauth_tool.allowed_actions = ["GOOGLEDRIVE_CREATE_FILE"]  # pick from .actions

# Step 4 — pass the SDK Tool object directly to the agent's tools=[].
# No manual dict shaping needed; the SDK serializes via tool.as_tool().
```

## Team Agent

```python
sub1 = aix.Agent(name="Researcher", instructions="Search and summarize.", tools=[search_tool]).save()
sub2 = aix.Agent(name="Writer", instructions="Write the final report.").save()
team = aix.Agent(name="Team Lead", instructions="Route to specialists.", subagents=[sub1, sub2]).save()
```

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

## Export Agent to Python

1. `GET https://platform-api.aixplain.com/sdk/agents/{ID}` with `x-api-key`
2. Recurse `agents[].assetId` for subagents
3. Map API fields to SDK constructor args
4. Generate standalone `.py` with env-based key loading

## Constraints

- Always search before creating, hardcoding, or declaring an asset missing — `Agent`, `Tool`, `Model`, and `Integration` all support `.search(query=...).results`. Never silently duplicate, and never announce "not in skill" without running the relevant search first
- When an agent already exists and the user asks for changes, **mutate the existing instance and call `agent.save()`** — never recreate. Recreating loses the ID, breaks any references, and risks `err.name_already_exists`
- `Agent.search()` is eventually-consistent and can miss recently-created agents. If lookup-by-name fails but `save()` later raises `name_already_exists`, fall back to `GET /sdk/agents` and match by exact name
- Set both `TEAM_API_KEY` and `AIXPLAIN_API_KEY` env vars
- OAuth tool **creation** requires REST (POST to `/api/v2/execute/{integration_id}`); the create response includes a `redirectURL` the user MUST visit to authorize before the tool has any actions
- OAuth tools can be **loaded** via `aix.Tool.get(tool_id)` and passed directly into `agent.tools=[...]` — the SDK serializes them via `as_tool()`. No manual dict/REST payload shaping is required
- An OAuth tool with empty `.actions` means OAuth is not yet completed; agent runs touching the tool will hang and time out. Always assert `len(list(tool.actions)) > 0` after fetch
- **Save vs Run validation asymmetry**: agents can be **saved/deployed** with unconnected integrations or with tools/integrations that have no `allowed_actions` selected — but they **cannot be run** unless every attached integration/tool has at least one action selected. Always set `allowed_actions` before invoking `agent.run()`. **Exception**: some integrations validate at save-time, not run-time — notably **MCP Server** (calls the remote server to verify the URL/token) and **SQLite** (rejects non-`.db` file types). A bad MCP URL or wrong file extension will fail `tool.save()` immediately, not defer to runtime
- The SDK's `tool.list_actions()` can return `[]` even when actions exist (stale `actions_available` flag). To verify auth + discover actions reliably, POST `{"action": "LIST_ACTIONS", "data": {}}` to `/api/v2/execute/{tool_id}`
- OAuth tools live at `/sdk/models/` not `/sdk/tools/` (relevant only if hitting the REST API directly)
- `runResponseGeneration=False` requires `output_format="text"`
- Tool descriptions < 200 chars, instructions < 1000 chars
- `.search()` returns `.results` not `.items` — filter client-side for exact match
- Prefer single agents over team agents (orchestrator dispatch has known failures)
- After adding inspectors, validate with 3 prompts: allowed, denied, ambiguous

## Quick Asset IDs

| Asset | Name | ID |
|---|---|---|
| Model | GPT-5.4 | `69b7e5f1b2fe44704ab0e7d0` |
| Model | GPT-4.1 Nano | `67fd9e2bef0365783d06e2f0` |
| Model | Claude Opus 4.6 | `698c87701239a117fd66b468` |
| Tool | Tavily Web Search | `6931bdf462eb386b7158def3` |
| Tool | Code Execution | `698cda188bbb345db14ac13b` |
| Integration | aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| Integration | PostgreSQL | `693ac6e8217c7b13b480970f` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | Python Sandbox | `688779d8bfb8e46c273982ca` |
| Integration | MCP Server | `686eb9cd26480723d0634d3e` |
| Integration | Gmail | `6864328d1223092cb4294d30` |
| Integration | Slack | `686432941223092cb4294d3f` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |

## Reference Files

- `references/asset-ids.md` — full model/integration/tool ID tables
- `references/integration-playbooks.md` — **REQUIRED READ** before wiring any non-OAuth integration (KB / SQLite / Python Sandbox / MCP). Contains the exact `config={...}` payloads, file-upload helpers, authoring constraints, and per-integration allowed_actions defaults. SKILL.md's "Create Tools" example only covers the KB shape — everything else needs this file
- `references/inspector-analytics.md` — inspector policies and analytics schema
