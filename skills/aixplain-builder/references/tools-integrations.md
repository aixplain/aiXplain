# Tools & integrations

Tools are what an agent calls to act. Three kinds:

1. **Marketplace tools** — pre-built (web search, scraping, PDF parsing). Fetch with `aix.Tool.get(path|id)`.
2. **Integrations** — connect external systems (Slack, Gmail, databases, MCP servers). Create with `aix.Tool(integration=..., config=...)`.
3. **Python Sandbox** — wrap your own Python function as a sandboxed tool.

Models can also act as tools via `model.as_tool()` (see `references/models.md`).

> **Asset paths are now three segments — `developer/name/host`** (`aixplain/python-sandbox/aixplain`, `composio/slack/composio`, `tavily/tavily-web-search/tavily`). The docs restructure rewrote nearly every path this way; older two-segment forms (`composio/slack`, `aixplain/postgresql`) still appear in the SDK and in older code. Prefer the three-segment path, and resolve with `.search()` if a `.get()` 404s.

## Golden rule: scope `allowed_actions`

A tool from `.get()` exposes **all** its actions by default — that is over-privileged and degrades the agent's reasoning. Always narrow to the minimum the task needs before attaching:

```python
tool = aix.Tool.get("<id>")
print(tool.list_actions())                 # discover available actions
tool.allowed_actions = ["search", "get"]   # scope to task
```

Setting `allowed_actions = None` or `[]` exposes everything — only do that deliberately and tell the user.

### Pre-fill action arguments (`.actions` / `.inputs`)

Pin an action's arguments at build time so the agent doesn't have to supply them. The rule, now stated explicitly in the docs: **action parameters always go via `.inputs` on the action; model parameters via `.inputs` on the model.** `tool.actions[...]` is case-insensitive and also reads in dot notation.

```python
tool.actions['SLACK_SEND_MESSAGE'].inputs.channel = '#general'    # dot notation
tool.actions['SLACK_SEND_MESSAGE'].inputs['text'] = 'Hello'       # item notation
tool.actions.slack_send_message.inputs.update(channel='#general', text='Hello')   # kwargs only

tool.set_inputs({                                   # bulk, across several actions
    'SLACK_SEND_MESSAGE': {'channel': '#general', 'text': 'Hello'},
    'SLACK_UPLOAD_FILE':  {'channels': '#general'},
})

inputs = tool.actions['SLACK_SEND_MESSAGE'].inputs
print(inputs.keys(), inputs.required)   # names; `.required` is a list of NAMES
print(dict(inputs.items()))             # {name: value} — shaped as an API payload
print(inputs.validate())                # list of error strings; [] means valid
inputs.reset('channel')                 # restore one to its backend default
inputs['channel'].reset()               # clear one to None (or `.reset(default)`)
inputs.reset()                          # restore all to their defaults
```

> **Set the value on `.inputs` — never on the action, never on the tool.** `tool.actions['X'].channel = '…'` silently sets an inert Python attribute that is dropped at save time, and `tool.actions['X']['text'] = …` raises `TypeError` (`Action` has no `__getitem__`). On a tool, `tool.inputs` itself raises `AttributeError: Tools have multiple actions — use tool.actions['action_name'].inputs instead`, on both read and write. Models are the mirror image: one implicit `run` action, so `model.inputs` directly and no `.actions` layer to disambiguate.

The hierarchy (`aixplain.v2.actions`) is `Actions → Action → Inputs → Input`:

| Level | Type | Surface |
|---|---|---|
| `tool.actions` | `Actions` — lazily fetched from the backend | `['NAME']` and `.name` (both case-insensitive), `in`, `len()`, iteration over names, `.refresh()` to drop the cache |
| `tool.actions['X']` | `Action` | read-only `.name`, `.description`, `.inputs` — nothing else on it is settable |
| `… .inputs` | `Inputs` | `['k']` / `.k` read+write, `.keys()`, `.values()`, `.items()`, `.get(k, default)`, `.update(**kw)`, `.copy()`, `.reset(k=None)`, `.required`, `.validate(data=None)` |
| `… .inputs['k']` | `Input` | `.name`, `.required`, `.type`, `.value`, `.description`, `.reset(default=None)`; compares by value, so `inputs['k'] == 'x'` works |

`keys()` / `values()` / `items()` operate on **raw values**, not `Input` objects — only `inputs['k']` / `inputs.get('k')` hand you the `Input` itself.

`Integration` objects carry the same `.actions` collection and `set_inputs()`. `list_actions()` and `list_inputs(*actions)` still exist and now return `ActionSpec` objects (renamed from `Action`) — `ActionSpec` lives in `aixplain.v2.integration`, **not** at the `aixplain.v2` top level — but `list_inputs` is formally **deprecated** in favour of `.actions[...].inputs`. `Input`, `Inputs`, `Action` and `Actions` *are* still exported from `aixplain.v2`; you just rarely need to import them.

> The stale docs example that showed `tool.actions['X'].channel = …` plus a `reset_input()` / `reset_all_inputs()` API has been **removed** in the restructure. Neither method exists on the SDK (verified) — it's `inputs['k'].reset()` / `inputs.reset()`. Follow the table above.

## Marketplace tools

```python
tool = aix.Tool.get("tavily/tavily-web-search/tavily")   # by path
tool = aix.Tool.get("6931bdf462eb386b7158def3")          # by ID

# Test before attaching (optional)
print(tool.run({"query": "AI news today", "num_results": 2}).data)

page = aix.Tool.search(query="web search", page_size=5)  # discover by keyword
print([t.path for t in page.results])
```

## Search the marketplace from the SDK

`aix.Tool.search(...)`, `aix.Model.search(...)` and `aix.Integration.search(...)` all return a `Page` with `.results`, `.total`, `.page_number`, `.page_total`, `.skipped` (item access — `page["results"]` — also works). **Always search before saying something isn't available, and before hardcoding an ID.** Asset names can be concatenated (e.g. "Googledrive") — normalize before comparing.

```python
tools  = aix.Tool.search(query="web search", page_size=5)
models = aix.Model.search(query="whisper", page_size=5)
print(tools.total, tools.page_total)
print([(t.name, t.path, t.id) for t in tools.results])     # .path may be None on older assets
print([(m.name, m.id) for m in models.results])

tool = aix.Tool.get(tools.results[0].path or tools.results[0].id)   # feed the hit straight back in
```

## `tool.run(...)` call forms

```python
tool.run(data={"a": 4, "b": 6}, action="add_numbers")          # data + explicit action
tool.run({"text": "Hi", "channel": "x"}, action="SLACK_...")    # positional data
tool.run({"text": "Hi", "channel": "x"})                        # implicit: see below
```

Read the result via `result.data`. Source-verified resolution order for an omitted `action`: one entry in `allowed_actions` → that one; else exactly one action on the tool at all (e.g. a Python Sandbox function) → that one; otherwise `ValueError: No action provided`.

`data` is forwarded verbatim — the SDK does **no** shape validation, so every "wrong payload" error you see is the backend's. Pass a dict keyed by the action's input names.

## Integrations — connect external systems

```python
integration = aix.Integration.get("composio/gmail/composio")   # or by ID
integration.list_actions()                                      # discover action names
```

Then create a connected tool with `aix.Tool(integration=..., config=...)` and `.save()`. The `integration=` field accepts an ID, a path (`"composio/slack/composio"`, `"aixplain/postgresql/aixplain"`), or an `Integration` object. Read it back with `tool.integration_path` — it returns `None` while `tool.integration` is still an unresolved ID string, so it tells you whether the integration has actually been fetched.

### Authentication schemes

**Don't guess the credential field names — read them off the integration:**

```python
itg = aix.Integration.get("composio/airtable/composio")
print(itg.attributes["auth_schemes"])        # e.g. ['OAUTH2', 'API_KEY']
print(itg.attributes["API_KEY-inputs"])      # [{"name": "generic_api_key", "displayName": …, "required": true}]
```

`attributes["<SCHEME>-inputs"]` gives the exact `config` keys for that scheme. (`itg.get_attribute(key, default)` is the safe accessor — `attributes` can be `None`.)

| Scheme | How to connect | `config` payload |
|---|---|---|
| `OAUTH2` / OAuth1 | Browser redirect | none — authorize in browser (see below) |
| `API_KEY` | SDK | whatever `attributes["API_KEY-inputs"]` names (e.g. `{"generic_api_key": "…"}`) |
| `BEARER_TOKEN` | SDK | `{"token": "..."}` |
| `BASIC` | SDK | the named fields, e.g. `{"subdomain": …, "username": …, "password": …}` |
| No auth | SDK | none |

Never invent placeholder credentials. `save()` does **not** validate the credential — a bad token fails on the first `run()` (e.g. `Slack API error: invalid_auth`), and a `config` key that doesn't match the scheme fails the save with `err.supplier_error`.

### OAuth workflow (Gmail, Slack, Jira, Google Drive…)

Saving an OAuth tool returns a `redirect_url`. The user must open it and authorize before the tool works:

```python
gmail_tool = aix.Tool(name="Gmail Tool", description="Reads and sends email.",
                      integration="composio/gmail/composio")
gmail_tool.save()
print(gmail_tool.redirect_url)   # -> user opens this, completes OAuth
gmail_tool.allowed_actions = ["GMAIL_SEND_EMAIL"]
```

On some SDK builds the redirect URL is emitted as a **warning** at `save()` rather than (or in addition to) `tool.redirect_url`. Capture it robustly like this — scope `allowed_actions` in the constructor, then hand the user the link:

```python
import warnings
integration = aix.Integration.get("composio/gmail/composio")   # a numeric id also works
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
                      integration="composio/slack/composio", config={"token": "YOUR_SLACK_TOKEN"})
slack_tool.allowed_actions = ["SLACK_SEND_MESSAGE"]
slack_tool.save()
slack_tool.run({"channel": "#general", "markdown_text": "Standup moves to 10:00."},
               action="SLACK_SEND_MESSAGE")
```

Commercial integrations span 230+ services via Composio (paths are `composio/<app>/composio`): Slack, Gmail, Outlook, Google Drive / Calendar, Salesforce, HubSpot, Jira, Notion, GitHub, Airtable, Zendesk… Apps expose a lot of actions (Slack >150, Zendesk 457) — `list_actions()`, then scope hard. Action names follow `<APP>_<VERB>_<NOUN>` (`GMAIL_SEND_EMAIL`, `JIRA_CREATE_ISSUE`, `GITHUB_CREATE_AN_ISSUE`, `NOTION_CREATE_NOTION_PAGE`) but Composio renames them over time — on `Action '...' not found`, copy the live name from `list_actions()`. Credentials are stored by the integration provider, not by aiXplain.

## Python Sandbox — wrap a Python function

Integration `aixplain/python-sandbox/aixplain` · `688779d8bfb8e46c273982ca`. Config is `{"code": <source string>, "function_name": <name>}`. The schema is inferred from type hints when present — they're no longer enforced, but without them the inferred schema degrades, so keep writing them.

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
tool = aix.Tool(code="def run(data): return data")   # integration= omitted entirely
```

Omitting `integration=` on a new tool is the documented shorthand: the constructor falls back to `Tool.DEFAULT_INTEGRATION_ID` (= `688779d8bfb8e46c273982ca`, verified) and resolves `function_name` from the source for you. It asserts `Code is required to create a (script) Tool` if neither `code=` nor `config["code"]` is present.

Source-verified name resolution (`_resolve_script_function_name`, client-side, before any network call): the code must parse (`code is not valid Python: …`); zero top-level functions → `No function found in code`; **more than one top-level function and no explicit `function_name` → `Multiple functions found in code: [...]`**. So helper functions are fine *only* when you name the entrypoint yourself. An explicit name that isn't there raises `Function '...' not found in code. Available functions: [...]`.

Most legacy authoring rules have been **relaxed** — top-level imports, missing type hints, multi-line `def` signatures, short parameter names, default values, helper functions in the same source, and zero-argument functions all work now. Only two hard constraints remain:

- **No `bool` parameters** — the serializer emits lowercase `true`/`false` → `NameError: name 'true' is not defined`. Use `int` (`0`/`1`) and coerce inside the function.
- **Avoid tuple returns / multi-value unpacking** — a tuple round-trips as its string repr (`"(2, 3)"`) rather than structured data. It no longer errors, it silently degrades. Return a `dict` or `list`.

> ⚠️ **Docs conflict, and the sandbox page is right.** `python-sandbox.md` says "Top-level imports, default values and multi-line signatures work"; `overview.md` still tells you to "Put imports inside the function". Top-level imports **do** work — the overview bullet is stale, and following it costs nothing but isn't required.

Also still true:
- Return values must be JSON-serialisable (dicts, lists, strings, numbers). They arrive at the caller as their **string form** inside `result.data["data"]`, e.g. `{'status': 'Success', 'data': "{'bmi': 22.86, …}"}`.
- Only stdlib + commonly available packages (e.g. `numpy`); an unavailable import surfaces as `status: "Failure"` with `ModuleNotFoundError` in `stderr`.
- **A numeric argument of `0` can arrive as `None`.** Defend inside the function: `b = b or 0`.
- Prefer returning an `{"error": "..."}` field over raising — the agent reads the message and can retry with different inputs.
- `inspect.getsource()` needs the function defined in a file or notebook cell (not a bare REPL). You can also read source from a file: `config={"code": open("fn.py").read(), ...}`.

**Updating a sandbox tool in place:** reassign `tool.config = {"code": …, "function_name": …}` and `save()` — the tool keeps its ID so attached agents pick up the change. (Note `save()` clears `tool.config`/`tool.code` back to `None` afterwards; that's bookkeeping, not data loss.)

### Code Execution vs Python Sandbox

Two ways to give an agent code abilities — pick by *when* the code is written:

- **Code Execution** (marketplace tool `698cda188bbb345db14ac13b`) — the agent **writes and runs arbitrary Python at runtime** in a secure cloud sandbox with internet access. Use for calculations, data transforms, visualizations, file processing, fetching from URLs/APIs. The agent should `print()` final results; if it generates files (plots, CSVs), it must print a JSON metadata list to stdout — `[{"name":"<display_name>","file":"<filename>"}]` — or the files are silently lost. Resolve it with `aix.Tool.search(query="code execution")` — the ID above is unverified as of 2026-09 (see the asset table) — then scope `allowed_actions`.
- **Python Sandbox** (integration `688779d8bfb8e46c273982ca`, above) — a **fixed function authored at build time**, not written at runtime. Use for deterministic tools with known inputs/outputs when no marketplace tool fits.

The sandbox side is the `calculate_bmi` snippet above. The Code Execution side is a plain marketplace tool — resolve it, scope it, attach it:

```python
code_exec = aix.Tool.search(query="code execution", page_size=5).results[0]   # don't hardcode the ID
actions = code_exec.list_actions()             # action names aren't published — read them here
code_exec.allowed_actions = [actions[0].name]  # scope to the run action only
analyst = aix.Agent(name="Analyst", description="Computes and charts from data you paste in",
    instructions="Write Python and run it. print() the final result; for files print the JSON metadata list.",
    tools=[code_exec])
analyst.save()
```

> Separately, `aix.Utility` (custom utility code) has its own parser rules and requires a `def main(...)` entry point — don't confuse it with the Python Sandbox integration. `Utility.run(**kwargs)` is an **instance** method (it was a classmethod in earlier builds — calling `aix.Utility.run(...)` on the class no longer works).

## MCP servers

### Remote MCP (cloud)

Integration `aixplain/mcp-server` · `686eb9cd26480723d0634d3e`.

```python
mcp_tool = aix.Tool(integration="aixplain/mcp-server", name="DeepWiki MCP",
                    description="Reads a public GitHub repo's documentation wiki.",
                    config={"url": "https://mcp.deepwiki.com/mcp"}).save()
print(mcp_tool.list_actions())                 # [ActionSpec(name='ask_wiki_question', inputs=[repoName, question]), …]
mcp_tool.allowed_actions = ["read_wiki_structure"]
r = mcp_tool.run(action="read_wiki_structure", data={"repoName": "aixplain/aiXplain"})
print(r.data["content"][0]["text"])            # MCP response: a `content` list of typed parts
```

Config key is `"url"`, and it must be the server's **Streamable HTTP** endpoint (usually `.../mcp`). The docs now treat that as the only supported transport: pointing at an SSE endpoint makes `save()` fail with `Method Not Allowed`, and an unreachable URL fails with `fetch failed` — `save()` connects and enumerates actions, so the server must be reachable from aiXplain at save time. Keep to ~10 actions per server.

> **MCP tools can't be deleted from the SDK:** `mcp_tool.delete()` raises `Asset is not a utility`. Delete via `DELETE https://platform-api.aixplain.com/sdk/models/<tool id>` with an `x-api-key` header.

### Local MCP — on-prem only (STDIO)

Dockerize the MCP server, `docker save`/`docker load` onto the on-prem aiXplain host, then register it in `mcpservers.json`:

```json
{"mcpServers": {"math_tools": {"command": "docker", "args": ["run","-i","--rm","aixplain-mcp_math:1.0.1"]}}}
```

It auto-loads within ~30s.

## SQL databases — SQLite & PostgreSQL

> The separate `sqlite.md` and `postgresql.md` docs pages were **deleted** and merged into one `databases.md`. Everything below is re-derived from it.

| | SQLite | PostgreSQL |
|---|---|---|
| Path · ID | `aixplain/sqlite/aixplain` · `689e06ed3ce71f58d73cc999` | `aixplain/postgresql/aixplain` · `693ac6e8217c7b13b480970f` |
| `config` | `{"url": <download link to a .db file>}` | `{"url": "postgresql://USER:PASS@HOST:5432/DB?sslmode=require"}` |
| Actions | `query`, `commit`, `schema` | `query`, `schema` — **no `commit`** |
| Writes | via `commit`, against the platform's copy; your local `.db` is untouched | via `query`, against the **live** DB, with the connection user's permissions |
| `query` returns | a Markdown table | a string of Python tuples, **no column names** — so select columns in the order you want to read them |
| `schema` returns | the `CREATE TABLE` statements | the tables and column names |
| Agents | supported | **not wired up yet** — call `pg.run(...)` from your own code |

### SQLite — upload the `.db` file first

```python
from aixplain.v2 import FileUploader

db_url = FileUploader(api_key="YOUR_API_KEY").upload("shop.db", return_download_link=True)

db = aix.Tool(name="Shop database", description="Products table: id, name, price.",
              integration="aixplain/sqlite/aixplain", config={"url": db_url}).save()

db.run(action="schema")
db.run(action="query",  data={"query": "SELECT name, price FROM products WHERE price < 300"})
db.run(action="commit", data={"query": "INSERT INTO products VALUES (4, 'Mouse', 25.00)"})
```

`FileUploader` (verified) is `FileUploader(backend_url=None, api_key=None, require_api_key=True)` with one method, `upload(file_path, tags=None, license="MIT", is_temp=True, return_download_link=False) -> str`. **`return_download_link=True` is required here** — the default return is the storage URL, not a link the tool can fetch. Keep the file under 100 MB and give it a `.db` extension (`Invalid file type. Only .db files are supported`). An empty `config["url"]` (e.g. an unset env var) fails with `Missing database url in data object`.

Writes via `commit` persist on the platform's copy and are visible to later `query` calls on the same tool; your local file is unchanged, so re-upload if you want them locally.

### PostgreSQL — live connection, no upload

```python
import os
pg = aix.Tool(name="Customer database", description="Read-only access to the customer database.",
              integration="aixplain/postgresql/aixplain",
              config={"url": os.environ["POSTGRES_URL"]}).save()
pg.run(action="query", data={"query": "SELECT version()"})
```

`save()` does **not** test the connection — a wrong host or password only surfaces on the first `run()` (`could not translate host name`, connection refused/timeout, or `permission denied for table`). URL-encode special characters in the password, and load the string from an env var or secrets manager, never from version control. Port 5432 must be reachable from aiXplain.

> **Pass SQL as a dict: `data={"query": "SELECT …"}`.** The docs now say a bare string is rejected with `Could not validate inputs for 'query'`. ⚠️ This reverses earlier guidance in this file (bare string *or* dict) — I can't re-test it without a network call, and the SDK forwards `data` unchanged, so this is backend-side. Use the dict.

> **There is still no `enable_commit`.** It was a v1 `SQLTool` parameter; it is not on `aix.Tool.__init__` in 0.2.48 (verified) and appears nowhere in the docs tree. A read-only workflow is `allowed_actions=["query", "schema"]` plus credential-level enforcement and a reinforcing instruction. For PostgreSQL that credential is the *only* real guard, because `query` runs writes too:
>
> ```sql
> CREATE USER readonly_user WITH PASSWORD '…';
> GRANT CONNECT ON DATABASE mydb TO readonly_user;
> GRANT USAGE ON SCHEMA public TO readonly_user;
> GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
> ```

> ⚠️ **Agent-side flakiness (SQLite).** An agent's *first* call to the SQLite tool can arrive without the SQL statement and fail, and the agent does not always retry — check `r.data.steps` for a failed `query` step before trusting an answer. Paste the output of the `schema` action into the agent's `instructions` so it never guesses column names.

### `aix.Resource` / `aix.File` — the SDK-side upload path

The docs dropped `aix.Resource` in favour of `FileUploader`, but it still works (verified) and hands you a **retrievable backend asset** rather than a bare URL — use it when you want the upload to stay addressable.

**`aix.Resource` signature — `(source=None, name=None, is_temp=True, **kwargs)`.** It is a subclass of `aixplain.v2.file.File`, which changes two things:

- **`name` occupies the 2nd positional slot.** The old positional order blows up: `aix.Resource("DB", "business.db")` now sets `source="DB"` and raises. Always pass `source=`/`name=` by keyword.
- **`file_path` is a read-only property** — assigning after construction raises `AttributeError: property 'file_path' of 'File' object has no setter` (verified). Keyword `file_path=` still works at construction as a compat alias (silently, no `DeprecationWarning`), but write new code with `source=`.

`source` also accepts an **HTTP(S) URL** (name inferred from the URL path; other schemes raise `ValidationError: Unsupported File URL scheme`) or a **directory** (`is_dir` becomes `True`). Validation is eager: a missing path raises `ValidationError: File source does not exist: …` at construction, before any upload, and `aix.Resource()` with no arguments raises too.

Because `aix.Resource` *is* an `aix.File`, the full File-asset surface comes with it — a saved upload is a retrievable backend asset, not just a URL:

```python
f = aix.File.get("<id>")                      # id, encoded asset path, or instance id; recursive=True by default
page = aix.File.search(query="business", page_size=20)   # also page_number=, sort=, **filters
f.download("/tmp/out")                        # folders stream down as one ZIP and are extracted safely
f.is_dir                                      # True for directory assets
```

Two upload behaviours worth knowing: every SDK HTTP call now carries a default `(connect, read)` timeout of `(10, 300)` seconds — previously it could hang forever on a silent peer — overridable per call with `timeout=` or globally via `AIXPLAIN_HTTP_CONNECT_TIMEOUT` / `AIXPLAIN_HTTP_READ_TIMEOUT`. And the presigned upload URL is validated against an allowed-host list (`*.amazonaws.com`, `*.aixplain.com`, extendable with `AIXPLAIN_UPLOAD_HOST_ALLOWLIST`) before any bytes are sent, raising `UnsafeURLError` (from `aixplain.utils.url_safety`, **not** the v2 `UntrustedURLError`) rather than a generic `FileUploadError`; https is required unless `AIXPLAIN_ALLOW_INSECURE_URLS=1`, and redirects are not followed.

## Built-in utility tools (fetch by path, no auth)

| Tool | Path · ID | Key actions |
|---|---|---|
| File Manager | `aixplain/aixplain-file-manager/aixplain` · `6a0216cffb2a801f1c41e32e` | `save_content`, `save_files` |
| Web Search | `aixplain/aixplain-web-search/aixplain` · `6a0c9044beac0e7cdc60122a` | `search` |
| Marketplace Search | `aixplain/aixplain-marketplace-search/aixplain` · `6960f934f316da19e5f22494` | `search`, `search_{models,tools,agents,integrations}`, `get_asset_details`, `list_filters`, `list_actions_<type>`, `list_inputs_<type>`, `run_<type>` |

All three are shared marketplace tools: nothing to connect, nothing to delete. `allowed_actions` applies to direct runs too, so re-`get()` a fresh copy when you want an action you scoped away.

### File Manager

```python
import uuid
fm = aix.Tool.get("aixplain/aixplain-file-manager/aixplain")
rid = f"q3-reports-{uuid.uuid4().hex[:5]}"      # lowercase letters, digits, hyphens
saved = fm.run(action="save_content", data={"requestid": rid,
               "contents": ["report text"], "names": ["reports/q3.txt"]}).data[0]
fm.run(action="save_files", data={"requestid": rid,
       "urls": [saved["signedUrl"]], "names": ["archive/q3.txt"]})
# each call returns [{id, name, signedUrl}] — time-limited presigned download links
```

- **`requestid` is now required on every call** (`Required input 'requestid' is missing`). It names the folder the request's files land in: reuse it *within* one request, never across requests — a repeated `requestid` + name collides.
- `save_content` requires `contents` **and** `names` of equal length; `names` may carry up to 3 folder levels; at most 100 items per call; both actions take an optional `tags` list (≤64 chars each).
- **`save_files` copies files already in aiXplain storage** (e.g. a `signedUrl` from `save_content`) — not arbitrary public web URLs. For outside or runtime-generated content use `save_content`.
- On failure the item comes back with an `error` field **instead of** `id`/`signedUrl` — e.g. `{'name': 'report.pdf', 'error': 'Failed to create file resource'}` (name collision, or a URL it couldn't fetch). Check per item, not just the call.
- `signedUrl` links expire; re-save to get a fresh one.

### Web Search

One call does search + parallel scrape, replacing a search-tool + scraper pair.

| Input | Required | Default | Controls |
|---|---|---|---|
| `query` | yes | — | the search query |
| `result_type` | no | **`raw`** | `raw` = per-page `title` / `url` / `description` + clean text, no LLM step; `answer` = LLM-synthesized `<answer>` + `<references>` |
| `num_results` | no | `5` | top-N results fetched **and scraped in parallel** |
| `word_limit` | no | **`300`** | max words kept per scraped page (token control) |
| `timeout` | no | **`2`** | per-URL scrape timeout (s); slower pages are skipped |
| `max_answer_words` | no | — | caps the synthesized answer length (`answer` mode) |
| `llm` | no | platform default | asset ID of the LLM that writes the answer (`answer` mode) |
| `search_asset_id` | no | platform default | asset ID of the underlying search model |
| `include_domains` / `exclude_domains` | no | — | restrict to / drop these domains; **exclusion wins** |
| `after` | no | — | only results published on/after a year or date (`"2024-01-31"`) |
| `gl` / `hl` / `location` | no | — | search as if from a country (`"us"`), in a UI language (`"en"`), or from a place (`"Toronto, Ontario, Canada"`) |

> The default flipped: `result_type` is now **`raw`**, and `word_limit` rose to 300. If you were relying on an implicit cited answer, pass `result_type="answer"` explicitly.

Pick `answer` for the fewest moving parts; `raw` when the agent should read and cite sources itself — keep `num_results`/`word_limit` modest in `raw` mode so payloads don't bloat the agent's context.

```python
web = aix.Tool.get("aixplain/aixplain-web-search/aixplain")
web.allowed_actions = ["search"]
r = web.run(action="search", data={"query": "EU AI Act implementation timeline",
    "num_results": 3, "word_limit": 120, "timeout": 5,            # defaults: 5 / 300 / 2
    "include_domains": ["europa.eu"], "after": "2024-01-31", "gl": "us", "hl": "en"})
for page in r.data:                                               # raw mode: a list of pages
    print(page["title"], "|", page["url"])
# result_type="answer" (+ max_answer_words) returns one <answer> block plus <references> instead
```

### Marketplace Search

The tool formerly documented as "aiXplain Browse" (`aixplain/aixplain-browse/aixplain`) is the **same asset ID** under a new canonical path, `aixplain/aixplain-marketplace-search/aixplain`. The Browse page is now unlisted; prefer the new path.

```python
mkt = aix.Tool.get("aixplain/aixplain-marketplace-search/aixplain")
mkt.allowed_actions = ["search", "get_asset_details"]        # never run_<type> unless intended
hits = mkt.run(action="search", data={"query": "translation", "asset_type": "model"}).data
print(hits["model"]["stats"]["total"],                        # one {results, stats} entry per type
      [h["path"] for h in hits["model"]["results"][:2]])
d = mkt.run(action="get_asset_details", data={"asset_id": "66311fda6eb563279c574b71"}).data
print(d["path"], d["function"], d["pricing"], d["status"])
```

- `search` returns one entry **per asset type** — `result.data["model"]["results"]` and `result.data["model"]["stats"]["total"]`. ⚠️ The shape changed from the `{items, total}` recorded here earlier; it is now `{results, stats}`. Narrow with `asset_type` = `"agent" | "model" | "tool" | "integration"`.
- `search` **requires** `query`; pass `""` as a wildcard when you only want to filter or count.
- Filters (array, on the search actions): `categories` (LLM, Language, Speech, Search, Video, Image, Image Generation, Developer Tools…), `developers`, `suppliers`, `hosts`, plus `function` (e.g. `"speech-recognition"`) and `page_size` / `page_number` (0-based). Get valid filter values from `list_filters` (takes `data={}`).
- `get_asset_details` takes **`asset_id`** (not `query`) → `path`, `name`, `asset_type`, `function`, `supplier`, `pricing {price, unitType, unitTypeScale}`, `status`. ⚠️ The retired Browse page spelled it `assetId`; if one errors, try the other.
- `list_actions_<type>` / `list_inputs_<type>` introspect one asset by `asset_id`. **`run_<type>` actually runs another asset and spends credits — keep it out of `allowed_actions`** unless the agent is meant to run what it finds.
- The `search_models` / `search_tools` / `search_agents` / `search_integrations` single-type actions were measured capping at 10 results with no paging; the new docs list `page_size` / `page_number` for "the search actions" generally, so re-check before trusting them for counts. `search` + `stats.total` is the reliable count.
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
tool.triggers["NEW_EMAIL"].configure(labelIds=["INBOX"])   # returns the option, so chain it into Trigger(event=…)
```

`.triggers` is a `TriggerTypes` collection — `['NAME']`, `in`, `len()`, iteration — and the option carries the `connection_id` **only when read off a connected tool**; off a bare `Integration` it is discovery-only and can't be activated. `.configure(**values)` sets the event's config payload and returns the option itself.

Pass that option as `event=` to `aix.Trigger`. **See `references/agents.md` for the full Trigger API** (time and event triggers, schedules, save/pause/delete).

## Common asset IDs

| Type | Name | Path · ID |
|------|------|----|
| Tool | Tavily Web Search | `tavily/tavily-web-search/tavily` · `6931bdf462eb386b7158def3` |
| Tool | Web Search | `aixplain/aixplain-web-search/aixplain` · `6a0c9044beac0e7cdc60122a` |
| Tool | Marketplace Search | `aixplain/aixplain-marketplace-search/aixplain` · `6960f934f316da19e5f22494` |
| Tool | File Manager | `aixplain/aixplain-file-manager/aixplain` · `6a0216cffb2a801f1c41e32e` |
| Tool | Scrape Website Tool | `crewai/scrape-website-tool/aixplain` · `69443180f2e6cb73e286ff16` |
| Tool | Code Execution (runtime Python) | `698cda188bbb345db14ac13b` ⚠️ |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` ⚠️ |
| Tool | Firecrawl API (scrape) | `69442021f2e6cb73e286ff0f` ⚠️ |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` ⚠️ |
| Model | GPT-5 Mini (default memory manager) | `6895d6d1d50c89537c1cf237` ⚠️ |
| Model | text-embedding-3-large | `openai/text-embedding-3-large/openai` · `699de0ad8be7bf2a80e80234` |
| Model | text-embedding-3-small | `openai/text-embedding-3-small/openai` · `699de0218be7bf2a80e80233` |
| Model | text-embedding-ada-002 | `openai/text-embedding-ada-002/openai` · `6734c55df127847059324d9e` |
| Integration | aiR Knowledge Base (vector DB) | `aixplain/air-knowledge-base/aixplain` · `6904bcf672a6e36b68bb72fb` |
| Integration | Python Sandbox / Script | `aixplain/python-sandbox/aixplain` · `688779d8bfb8e46c273982ca` |
| Integration | SQLite | `aixplain/sqlite/aixplain` · `689e06ed3ce71f58d73cc999` |
| Integration | PostgreSQL | `aixplain/postgresql/aixplain` · `693ac6e8217c7b13b480970f` |
| Integration | Remote MCP Server | `aixplain/mcp-server` · `686eb9cd26480723d0634d3e` |
| Integration | Shared Memory | `aixplain/shared-memory/aixplain` · `69a59de88e25a303cbf1b8c6` |
| Integration | Composio apps | `composio/<app>/composio` — `slack`, `gmail`, `outlook`, `googledrive`, `googlecalendar`, `salesforce`, `hubspot`, `jira`, `notion`, `github`, `airtable`, `zendesk`, … |

Confirmed this round: PostgreSQL `693ac6e8217c7b13b480970f` now appears in the docs (⚠️ dropped) and Remote MCP gained a published ID.

> ⚠️ **Still unverified** — these IDs appear nowhere in the current docs tree. They are kept because nothing contradicts them, but **resolve them with `aix.Tool.search(query="…")` / `aix.Model.search(...)` before use** rather than hardcoding. (Code Execution is still named in prose as a capability, so the tool exists; only the ID is unconfirmed. The GPT-5 Mini memory-manager ID lost its last docs mention in this restructure — see `references/knowledge-memory.md`.)
>
> The per-app Composio numeric IDs recorded here previously (Slack `686432941223092cb4294d3f`, Gmail `6864328d1223092cb4294d30`, Drive/Sheets/Docs/Calendar `686432…`) have **vanished from the docs** — use the `composio/<app>/composio` paths instead.
>
> IDs change over time. Treat this whole table as a starting point and verify with `aix.*.search(...)` / `.get(...)`. If an ID 404s, search for the asset by name instead. `tavily/tavily-search-api/Tavily` · `6736411cf127849667606689` is now **"Tavily Web Search (Legacy)"** — don't use it for new tools.
