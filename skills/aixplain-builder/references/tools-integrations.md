# Tools & integrations

Tools are what an agent calls to act. Three kinds:

1. **Marketplace tools** — pre-built (web search, scraping, PDF parsing). Fetch with `aix.Tool.get(path|id)`.
2. **Integrations** — connect external systems (Slack, Gmail, databases, MCP servers). Create with `aix.Tool(integration=..., config=...)`.
3. **Python Sandbox** — wrap your own Python function as a sandboxed tool.

Models can also act as tools via `model.as_tool()` (see `references/models.md`).

## Golden rule: scope `allowed_actions`

A tool from `.get()` exposes **all** its actions by default — that is over-privileged and degrades the agent's reasoning. Always narrow to the minimum the task needs before attaching:

```python
tool = aix.Tool.get("<id>")
print(tool.list_actions())                 # discover available actions
tool.allowed_actions = ["search", "get"]   # scope to task
```

Setting `allowed_actions = None` or `[]` exposes everything — only do that deliberately and tell the user.

## Marketplace tools

```python
tool = aix.Tool.get("tavily/tavily-search-api")     # by path
tool = aix.Tool.get("6931bdf462eb386b7158def3")     # by ID

# Test before attaching (optional)
print(tool.run({"query": "AI news today", "num_results": 2}).data)

results = aix.Tool.search(query="web search").results   # discover by keyword
```

## Search the marketplace from the SDK

`aix.Tool.search(...)`, `aix.Model.search(...)`, and `aix.Integration.search()["results"]` all let you find assets. **Always search before saying something isn't available, and before hardcoding an ID.** Asset names can be concatenated (e.g. "Googledrive") — normalize before comparing.

## `tool.run(...)` call forms

```python
tool.run(data={"a": 4, "b": 6}, action="add_numbers")          # data + explicit action
tool.run({"text": "Hi", "channel": "x"}, action="SLACK_...")    # positional data
tool.run({"text": "Hi", "channel": "x"})                        # implicit (only if ONE allowed_action)
tool.run(action="query", data="SELECT * FROM products")         # data as plain string (SQL tools)
```

Read the result via `result.data`. If multiple actions are allowed and you omit `action`, it errors.

## Integrations — connect external systems

```python
integration = aix.Integration.get("composio/gmail")    # or by ID
integration.list_actions()                              # discover action names
```

Then create a connected tool with `aix.Tool(integration=..., config=...)` and `.save()`. The `integration=` field accepts an ID, a path (`"composio/slack"`, `"aixplain/postgresql"`), or an `Integration` object.

### Authentication schemes

| Scheme | How to connect | `config` payload |
|---|---|---|
| OAuth2 / OAuth1 | Browser redirect | none — authorize in browser (see below) |
| API key | SDK | `{"api_key": "..."}` (some use `{"token": "..."}`) |
| Bearer token | SDK | `{"token": "..."}` |
| Basic | SDK | `{"username": "...", "password": "..."}` |
| No auth | SDK | none |

Exact credential field names are per-integration — confirm in Studio → Discover → Integrations, or ask the user. Never invent placeholder credentials.

### OAuth workflow (Gmail, Slack, Jira, Google Drive…)

Saving an OAuth tool returns a `redirect_url`. The user must open it and authorize before the tool works:

```python
gmail_tool = aix.Tool(name="Gmail Tool", description="Reads and sends email.",
                      integration="composio/gmail")
gmail_tool.save()
print(gmail_tool.redirect_url)   # -> user opens this, completes OAuth
gmail_tool.allowed_actions = ["GMAIL_SEND_EMAIL"]
```

On some SDK builds the redirect URL is emitted as a **warning** at `save()` rather than (or in addition to) `tool.redirect_url`. Capture it robustly like this — scope `allowed_actions` in the constructor, then hand the user the link:

```python
import warnings
integration = aix.Integration.get("6864328d1223092cb4294d30")   # Gmail (numeric id also works)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gmail_tool = aix.Tool(name="My Gmail Tool", description="Send emails.",
                          integration=integration, allowed_actions=["GMAIL_SEND_EMAIL"]).save()
    oauth_url = getattr(gmail_tool, "redirect_url", None) or \
                next((str(x.message) for x in w if "http" in str(x.message)), None)
print(f"Connect Gmail: {oauth_url}")     # user opens this, authorizes, then the tool is usable
agent = aix.Agent(name="Gmail Agent", instructions="Use Gmail to send emails.",
                  tools=[gmail_tool], output_format="markdown").save()
```

### API-key integration (no browser)

```python
slack_tool = aix.Tool(name="Slack Notifier", description="Sends Slack messages.",
                      integration="composio/slack", config={"token": "YOUR_SLACK_TOKEN"})
slack_tool.allowed_actions = ["SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"]
slack_tool.save()
slack_tool.run({"text": "Hello :)", "channel": "general"},
               action="SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL")
```

Commercial integrations span 230+ services via Composio: Communication (Slack, Teams, Discord), CRM (Salesforce, HubSpot), PM (Jira, Asana, Trello), Storage (S3, Google Drive, Dropbox), Databases, Calendars.

## Python Sandbox — wrap a Python function

Integration ID `688779d8bfb8e46c273982ca`. Config is `{"code": <source string>, "function_name": <name>}`. The function's schema is inferred from type hints.

```python
import inspect, time

def calculate_bmi(weight_kg: float, height_m: float) -> dict:
    """Calculate Body Mass Index."""
    bmi = weight_kg / (height_m ** 2)
    category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight" if bmi < 30 else "obese"
    return {"bmi": round(bmi, 2), "category": category}

bmi_tool = aix.Tool(
    name=f"BMI Tool {int(time.time())}",          # timestamp keeps the name unique
    integration="688779d8bfb8e46c273982ca",
    config={"code": inspect.getsource(calculate_bmi), "function_name": "calculate_bmi"},
)
bmi_tool.save()
print(bmi_tool.run(data={"weight_kg": 70, "height_m": 1.75}, action="calculate_bmi").data)
```

Sandbox constraints (work around these):
- **No `bool` parameters** — the serializer emits lowercase `true`/`false` → `NameError`. Use `int` (`0`/`1`).
- **No tuple returns / multi-value unpacking** — return a `dict` or `list`. Return values must be JSON-serialisable.
- Imports must be **inside the function body** (it runs in isolation).
- `inspect.getsource()` needs the function defined in a file or notebook cell (not a bare REPL). You can also read source from a file: `config={"code": open("fn.py").read(), ...}`.
- Only stdlib + commonly available packages; an unavailable import raises `ImportError` at call time.

### Code Execution vs Python Sandbox

Two ways to give an agent code abilities — pick by *when* the code is written:

- **Code Execution** (marketplace tool `698cda188bbb345db14ac13b`) — the agent **writes and runs arbitrary Python at runtime** in a secure cloud sandbox with internet access. Use for calculations, data transforms, visualizations, file processing, fetching from URLs/APIs. The agent should `print()` final results; if it generates files (plots, CSVs), it must print a JSON metadata list to stdout — `[{"name":"<display_name>","file":"<filename>"}]` — or the files are silently lost. Attach with `aix.Tool.get("698cda188bbb345db14ac13b")` and scope `allowed_actions`.
- **Python Sandbox** (integration `688779d8bfb8e46c273982ca`, above) — a **fixed function authored at build time**, not written at runtime. Use for deterministic tools with known inputs/outputs when no marketplace tool fits.

> Separately, `aix.Utility` (custom utility code) has its own parser rules and requires a `def main(...)` entry point — don't confuse it with the Python Sandbox integration.

## MCP servers

### Remote MCP (cloud)

```python
mcp_tool = aix.Tool(integration="aixplain/mcp-server", name="Remote MCP Tool",
                    config={"url": "https://remote.mcpservers.org/fetch/mcp"})
mcp_tool.save()
mcp_tool.allowed_actions = ["fetch"]
print(mcp_tool.list_actions())
mcp_tool.run(data={"url": "https://www.aixplain.com"})
```

Config key is `"url"`. Transports: HTTP (`.../mcp`, stateless) and SSE (`.../sse`, streaming). Keep to ~10 actions per server.

### Local MCP — on-prem only (STDIO)

Dockerize the MCP server, `docker save`/`docker load` onto the on-prem aiXplain host, then register it in `mcpservers.json`:

```json
{"mcpServers": {"math_tools": {"command": "docker", "args": ["run","-i","--rm","aixplain-mcp_math:1.0.1"]}}}
```

It auto-loads within ~30s.

## SQL databases

### SQLite — integration `689e06ed3ce71f58d73cc999`

Upload the `.db` file as a Resource first (keep it < 100 MB), then point the tool at the resource URL.

```python
import time
resource = aix.Resource(name=f"DB {int(time.time())}", file_path="business.db")
resource.save()                                # uploads to S3, sets resource.url
sqlite_tool = aix.Tool(name="Business Database", description="Company sales data.",
                       integration="689e06ed3ce71f58d73cc999", config={"url": resource.url})
sqlite_tool.save()
sqlite_tool.list_actions()                     # query, commit, schema
sqlite_tool.run(action="query", data="SELECT * FROM products")
```

Writes apply to an in-memory copy and are **not** persisted — re-upload to persist.

### PostgreSQL — integration `aixplain/postgresql`

Connects to a live DB via connection string (no upload).

```python
pg = aix.Tool(name="Postgres Tool", integration="aixplain/postgresql",
              config={"url": "postgresql://user:password@host:5432/mydb"})
pg.save()
pg.list_actions()                              # schema, query
pg.run(action="query", data={"query": "SELECT * FROM customers LIMIT 3"})
```

Use read-only DB credentials when possible and reinforce read-only in the agent's `instructions`.

## Built-in utility tools (fetch by ID, no auth)

| Tool | ID | Key actions |
|---|---|---|
| File Manager | `6a0216cffb2a801f1c41e32e` | `save_content`, `save_files` |
| Web Search | `6a0c9044beac0e7cdc60122a` | `search` |
| Marketplace Search / Browse | `6960f934f316da19e5f22494` | `search`, `search_models`, `search_tools`, `search_agents`, `search_integrations`, `get_asset_details`, `list_filters` |

```python
fm = aix.Tool.get("6a0216cffb2a801f1c41e32e")
fm.run(action="save_content", data={"contents": ["report text"], "names": ["q3.txt"]})
fm.run(action="save_files", data={"urls": ["https://.../report.pdf"], "names": ["report.pdf"]})
# returns [{id, name, signedUrl}] — time-limited presigned download links
```

## Attach tools to an agent

```python
agent = aix.Agent(name="...", description="...", instructions="...", tools=[tool1, tool2])
agent.tools.append(another_tool)   # add later
agent.save()
```

Tool names must be unique per agent (duplicate names → error). Inspect with `tool.name`, `tool.description`, `tool.status`, `tool.id`.

## Common asset IDs

| Type | Name | ID / path |
|------|------|----|
| Tool | Tavily Web Search | `tavily/tavily-search-api` · `6931bdf462eb386b7158def3` |
| Tool | Code Execution (runtime Python) | `698cda188bbb345db14ac13b` |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` |
| Tool | Firecrawl API (scrape) | `69442021f2e6cb73e286ff0f` |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` |
| Integration | aiR Knowledge Base (vector DB) | `6904bcf672a6e36b68bb72fb` |
| Integration | Python Sandbox / Script | `688779d8bfb8e46c273982ca` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | PostgreSQL | `aixplain/postgresql` · `693ac6e8217c7b13b480970f` |
| Integration | Remote MCP Server | `aixplain/mcp-server` |
| Integration | Shared Memory | `aixplain/shared-memory/aixplain` |
| Integration | Slack (Composio) | `composio/slack` · `686432941223092cb4294d3f` |
| Integration | Gmail (Composio) | `composio/gmail` · `6864328d1223092cb4294d30` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |

> IDs change over time. Treat this table as a starting point and verify with `aix.*.search(...)` / `.get(...)`. If an ID 404s, search for the asset by name instead.
