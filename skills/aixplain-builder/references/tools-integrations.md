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

### Pre-fill action arguments (`.actions` / `.inputs`)

Pin an action's arguments at build time so the agent doesn't have to supply them. `tool.actions[...]` is case-insensitive; the values live on the action's **`.inputs`** mapping:

```python
tool.actions['SLACK_SEND_MESSAGE'].inputs.channel = '#general'    # dot notation
tool.actions['SLACK_SEND_MESSAGE'].inputs['text'] = 'Hello'       # item notation
tool.actions['SLACK_SEND_MESSAGE'].inputs.update(channel='#general', text='Hello')   # kwargs only

tool.set_inputs({                                   # bulk, across several actions
    'SLACK_SEND_MESSAGE': {'channel': '#general', 'text': 'Hello'},
    'SLACK_UPLOAD_FILE':  {'channels': '#general'},
})

inputs = tool.actions['SLACK_SEND_MESSAGE'].inputs
print(inputs.keys(), inputs.required)               # introspect the schema
inputs['channel'].reset()                           # clear one
inputs.reset()                                      # clear all
```

> Set the value on `.inputs`, **not** on the action itself — `tool.actions['X'].channel = '…'` silently sets a stray attribute and is ignored, and `tool.actions['X']['text'] = …` raises `TypeError`. `Integration` objects carry the same `.actions` proxy and `set_inputs()`. `tool.list_inputs(*actions)` still exists but is **deprecated** in favour of `.actions[...].inputs`. Models have no `.actions` — they use `model.inputs` directly.

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

Integration ID `688779d8bfb8e46c273982ca`. Config is `{"code": <source string>, "function_name": <name>}`. The schema is inferred from type hints when present — they're no longer enforced, but without them the inferred schema degrades, so keep writing them.

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

`code=` is also a first-class constructor parameter, not only a `config` key — handy for a one-off function:

```python
tool = aix.Tool(integration="688779d8bfb8e46c273982ca", code="def run(data): return data")
```

Most legacy authoring rules have been **relaxed** — top-level imports, missing type hints, multi-line `def` signatures, short parameter names, default values, helper functions in the same source, and zero-argument functions all work now. Only two hard constraints remain:

- **No `bool` parameters** — the serializer emits lowercase `true`/`false` → `NameError: name 'true' is not defined`. Use `int` (`0`/`1`) and coerce inside the function.
- **Avoid tuple returns / multi-value unpacking** — a tuple round-trips as its string repr (`"(2, 3)"`) rather than structured data. It no longer errors, it silently degrades. Return a `dict` or `list`.

Also still true:
- Return values must be JSON-serialisable (dicts, lists, strings, numbers).
- `function_name` must exactly match a function defined in `code`. Helper functions alongside it are fine — only the named one is registered.
- Only stdlib + commonly available packages; an unavailable import raises `ImportError` at call time.
- `inspect.getsource()` needs the function defined in a file or notebook cell (not a bare REPL). You can also read source from a file: `config={"code": open("fn.py").read(), ...}`.

### Code Execution vs Python Sandbox

Two ways to give an agent code abilities — pick by *when* the code is written:

- **Code Execution** (marketplace tool `698cda188bbb345db14ac13b`) — the agent **writes and runs arbitrary Python at runtime** in a secure cloud sandbox with internet access. Use for calculations, data transforms, visualizations, file processing, fetching from URLs/APIs. The agent should `print()` final results; if it generates files (plots, CSVs), it must print a JSON metadata list to stdout — `[{"name":"<display_name>","file":"<filename>"}]` — or the files are silently lost. Resolve it with `aix.Tool.search(query="code execution")` — the ID above is unverified as of 2026-09 (see the asset table) — then scope `allowed_actions`.
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
resource = aix.Resource(source="business.db", name=f"DB {int(time.time())}")
resource.save()                                # uploads to S3, sets resource.url
sqlite_tool = aix.Tool(name="Business Database", description="Company sales data.",
                       integration="689e06ed3ce71f58d73cc999", config={"url": resource.url})
sqlite_tool.save()
sqlite_tool.list_actions()                     # query, commit, schema
sqlite_tool.run(action="query", data="SELECT * FROM products")
```

Writes apply to an in-memory copy and are **not** persisted — re-upload to persist. `data` accepts either a bare SQL string or `{"query": "..."}` (same for PostgreSQL).

**`aix.Resource` signature — `(source=None, name=None, is_temp=True, **kwargs)`.** It is now a subclass of `aixplain.v2.file.File`, which changes two things:

- **`name` occupies the 2nd positional slot.** The old positional order blows up: `aix.Resource("DB", "business.db")` now sets `source="DB"` and raises. Always pass `source=`/`name=` by keyword.
- **`file_path` is a read-only property** — assigning after construction raises `AttributeError`. Keyword `file_path=` still works at construction as a deprecated compat alias (the docs' own SQLite examples still use it), but write new code with `source=`.

`source` also accepts an **HTTP(S) URL** (name inferred from the URL path; other schemes raise `ValidationError: Unsupported File URL scheme`) or a **directory** (`is_dir` becomes `True`). Validation is eager: a missing path raises `ValidationError: File source does not exist: …` at construction, before any upload, and `aix.Resource()` with no arguments raises too.

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

> **Don't use `enable_commit`.** The docs overview recommends `enable_commit=False` for read-only SQL tools, but it is a **v1 `SQLTool` parameter only** — it is not on `aix.Tool.__init__` in 0.2.48 and appears nowhere in the v2 SQLite or PostgreSQL pages. Read-only enforcement is credential-level (a Postgres `readonly_user`) plus instruction-level.

## Built-in utility tools (fetch by ID, no auth)

| Tool | ID / path | Key actions |
|---|---|---|
| File Manager | `6a0216cffb2a801f1c41e32e` | `save_content`, `save_files` |
| Web Search | `6a0c9044beac0e7cdc60122a` · `aixplain/aixplain-web-search/aixplain` | `search` |
| Marketplace Search / Browse | `6960f934f316da19e5f22494` · `aixplain/aixplain-browse/aixplain` | `search`, `search_models`, `search_tools`, `search_agents`, `search_integrations`, `get_asset_details`, `list_filters` |

### File Manager

```python
fm = aix.Tool.get("6a0216cffb2a801f1c41e32e")
fm.run(action="save_content", data={"contents": ["report text"], "names": ["q3.txt"]})
fm.run(action="save_files", data={"urls": ["https://.../report.pdf"], "names": ["report.pdf"]})
# returns [{id, name, signedUrl}] — time-limited presigned download links
```

`save_content` requires `contents` **and** `names` of equal length; both actions take an optional `tags` list. On failure the item comes back with an `error` field **instead of** `id`/`signedUrl` — e.g. `[{'url': ..., 'name': 'report.pdf', 'error': 'Failed to create file resource'}]`, typically an unreachable source URL. Check per item, not just the call. For content generated at runtime use `save_content`, not `save_files`.

### Web Search

One call does search + parallel scrape, replacing a search-tool + scraper pair.

| Input | Required | Default | Controls |
|---|---|---|---|
| `query` | yes | — | the search query |
| `num_results` | no | `5` | top-N results fetched **and scraped in parallel** |
| `word_limit` | no | `100` | max words kept per scraped page (token control) |
| `timeout` | no | — | per-URL scrape timeout (s); returns whatever finished |
| `result_type` | no | `answer` | `answer` = LLM-synthesized cited answer; `raw` = URLs + clean scraped text, no LLM step |
| `search_asset_id` | no | platform default | underlying engine (Google / Bing / DuckDuckGo) |
| `llm` | no | — | LLM asset used to synthesize (`answer` mode) |
| `max_answer_words` | no | — | caps the synthesized answer length |

Pick `answer` for the fewest moving parts; `raw` when the agent should read and cite sources itself — keep `num_results`/`word_limit` modest in `raw` mode so payloads don't bloat the agent's context.

### Marketplace Search

- Only **`search`** returns a `total` per asset type (`{agent, model, tool, integration}`, each `{items, total}`). The `search_models` / `search_tools` / `search_agents` / `search_integrations` actions **cap at 10 results and do not paginate** — use them for examples, never for counts.
- `search` **requires** `query`; pass `""` as a wildcard when you only want to filter or count.
- Optional array filters on `search` / `search_models` / `search_tools`: `categories` (LLM, Speech, Image, Video, OCR, Classification, Language), `developers`, `suppliers`, `hosts`, plus `function`.
- `get_asset_details` takes **`assetId`** (not `query`) → `asset_type`, `function`, `supplier`, `hosted_by`, `developed_by`, `supports_streaming`, `pricing {price, unitType}`, `status`. `list_filters` takes no data.
- Keyword matching is **literal** — retry with a single distinctive token before concluding an asset is absent.

## Attach tools to an agent

```python
agent = aix.Agent(name="...", description="...", instructions="...", tools=[tool1, tool2])
agent.tools.append(another_tool)   # add later
agent.save()
```

Tool names must be unique per agent (`Duplicate tool names found: [Tool Name]. Make sure all tool names are unique.`). Inspect with `tool.name`, `tool.description`, `tool.status`, `tool.id`.

## Event triggers — the tool-side hooks

An integration can expose events an agent fires on (a new email, a new file). Discovery lives on the tool/integration:

```python
integration.list_trigger_types()      # -> List[TriggerTypeSpec]; also on Tool
list(integration.triggers)            # discovery only: ['NEW_EMAIL', 'NEW_LABELED_EMAIL', ...]
tool.triggers["NEW_EMAIL"]            # -> TriggerEventOption, case-insensitive; needs a CONNECTED tool
```

Pass that option as `event=` to `aix.Trigger`. **See `references/agents.md` for the full Trigger API** (time and event triggers, schedules, save/pause/delete).

## Common asset IDs

| Type | Name | ID / path |
|------|------|----|
| Tool | Tavily Web Search | `tavily/tavily-search-api` · `6931bdf462eb386b7158def3` |
| Tool | Web Search | `6a0c9044beac0e7cdc60122a` · `aixplain/aixplain-web-search/aixplain` |
| Tool | Marketplace Search / Browse | `6960f934f316da19e5f22494` · `aixplain/aixplain-browse/aixplain` |
| Tool | File Manager | `6a0216cffb2a801f1c41e32e` |
| Tool | Scrape Website Tool | `69443180f2e6cb73e286ff16` · `crewai/scrape-website-tool/aixplain` |
| Tool | Code Execution (runtime Python) | `698cda188bbb345db14ac13b` ⚠️ |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` ⚠️ |
| Tool | Firecrawl API (scrape) | `69442021f2e6cb73e286ff0f` ⚠️ |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` ⚠️ |
| Model | GPT-5 Mini (default memory manager) | `6895d6d1d50c89537c1cf237` |
| Model | text-embedding-3-large | `699de0ad8be7bf2a80e80234` · `openai/text-embedding-3-large/openai` |
| Model | text-embedding-3-small | `699de0218be7bf2a80e80233` · `openai/text-embedding-3-small/openai` |
| Model | text-embedding-ada-002 | `6734c55df127847059324d9e` · `openai/text-embedding-ada-002/openai` |
| Integration | aiR Knowledge Base (vector DB) | `6904bcf672a6e36b68bb72fb` |
| Integration | Python Sandbox / Script | `688779d8bfb8e46c273982ca` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | PostgreSQL | `aixplain/postgresql` · `693ac6e8217c7b13b480970f` ⚠️ |
| Integration | Remote MCP Server | `aixplain/mcp-server` |
| Integration | Shared Memory | `aixplain/shared-memory/aixplain` · `69a59de88e25a303cbf1b8c6` |
| Integration | Slack (Composio) | `composio/slack` · `686432941223092cb4294d3f` |
| Integration | Gmail (Composio) | `composio/gmail` · `6864328d1223092cb4294d30` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |

> ⚠️ **Unverified as of 2026-09** — these IDs appear nowhere in the current docs tree and may be stale. They are kept because nothing contradicts them, but **resolve them with `aix.Tool.search(query="…")` before use** rather than hardcoding. (Code Execution is still named in prose as a capability, so the tool exists; only the ID is unconfirmed.)
>
> IDs change over time. Treat this whole table as a starting point and verify with `aix.*.search(...)` / `.get(...)`. If an ID 404s, search for the asset by name instead. `6736411cf127849667606689` is now **"Tavily Web Search (Legacy)"** — don't use it for new tools.
