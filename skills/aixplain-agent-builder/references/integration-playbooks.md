# Integration Playbooks

Connection patterns per integration type.
Linked from the main skill — consult when wiring tools.

Canonical v2 entry point:
- Use `from aixplain import Aixplain`.
- Use `aix.Tool`, `aix.Integration` directly from the v2 client surface.

Use `integration.list_actions()` and `integration.list_inputs(action_name)` before connecting in SDK flows. Always scope actions to a non-empty least-privilege set.

---

## 1. aiR Knowledge Base (`6904bcf672a6e36b68bb72fb`)

Connect with uploaded files (`.pdf`, `.docx`, `.txt`, `.md`, `.html`, `.csv`) or start empty and write with `upsert`.

**Typical actions:** `search`, `get`, `count`, `metadata`, optional `upsert`.
**Best practice:** Keep retrieval-first scope (`search`, `get`, `metadata`) unless runtime writing is explicitly required.

```python
index_tool = aix.Tool(
    name="My Knowledge Base",
    description="Semantic search over uploaded documents",
    integration="6904bcf672a6e36b68bb72fb",
).save()

# Populate
records = [
    {"id": "doc1", "text": "Python is a programming language", "metadata": {"category": "tech"}},
    {"id": "doc2", "text": "Machine learning uses algorithms", "metadata": {"category": "ai"}},
]
index_tool.run(action="upsert", data={"records": records})

# Query
index_tool.run(action="search", data={"query": "programming", "filters": []})
index_tool.run(action="count", data={})
```

Semantic search works immediately after `upsert`; `count` returns indexed document total.

---

## 2. PostgreSQL (`693ac6e8217c7b13b480970f`)

Connect with database URL: `postgresql://username:password@host:port/database`.

- Prefer read-only DB users for analysis assistants.
- Scope query actions first; enable write actions only when explicitly required.

---

## 3. SQLite Database (`689e06ed3ce71f58d73cc999`)

Connect using `.db` file URL via `config={"url": "<download_url_to_db_file>"}`.

- Valid actions: `query`, `schema`, `commit`.
- Default safe scope: `["query", "schema"]`.
- SQLite connect rejects non-`.db` file types.

```python
from aixplain.v2.upload_utils import FileUploader

integration = aix.Integration.get("689e06ed3ce71f58d73cc999")
uploader = FileUploader(api_key=TEAM_API_KEY, backend_url=aix.backend_url)
db_url = uploader.upload("/absolute/path/to/data.db", is_temp=True, return_download_link=True)

sqlite_tool = aix.Tool(
    name="SQLite Reader",
    description="Read-only DB access",
    integration=integration,
    config={"url": db_url},
    allowed_actions=["query", "schema"],
).save()
```

---

## 4. Python Sandbox (`688779d8bfb8e46c273982ca`)

Connect with `.py` file or inline source code and set `function_name` for the exposed function.

### Authoring Constraints

Empirically verified against aiXplain SDK v0.2.44 on 2026-04-07. The previously documented 8-rule list has been largely relaxed server-side. Only the following constraints are still active:

1. **`function_name` must match a function defined in `code`.** If you include multiple functions in one code block, only the one whose name equals `function_name` is registered as the tool.
2. **`bool` parameters are broken** — the runtime serializer emits JSON `true`/`false` (lowercase) which then fails inside Python with `NameError: name 'true' is not defined`. Use `int` (0/1) as a workaround until the serializer is fixed.
3. **Tuple / multi-value returns are lossy** — a `return a, b` will round-trip as the string `"(a, b)"`, not structured data. If you need structured output, return a `dict` or `list`.

The following **old** rules are **no longer enforced** (verified by creating and running tools that violate each one):

| Old rule | Status |
|---|---|
| Single-line `def` signature | ❌ No longer enforced — multi-line signatures work |
| Parameter names ≥ 3 characters | ❌ No longer enforced — `a`, `b` work |
| No default parameter values | ❌ No longer enforced — defaults work |
| Type hints required | ❌ No longer enforced — untyped params work |
| Inputs restricted to `str`/`int`/`list`/`dict` | ❌ Relaxed — `float` works (may be int-coerced in serializer). `bool` is the only exception, see rule 2 above |
| At least one input parameter | ❌ No longer enforced — zero-arg functions work |
| All imports inside function body | ❌ No longer enforced — top-level `import` works |
| File must have `.py` extension | N/A for inline `config={"code": ...}` — only relevant when uploading a `.py` file |

### v2 Notes

- Integration action/input specs are discovered after connection (`list_actions`/`list_inputs`).
- Custom utility code (`aix.Utility`) has separate parser rules and requires `def main(...)`; do not confuse with Python Sandbox integration tools.

```python
script_content = """def sum_then_square(first_number: int, second_number: int):
    total = first_number + second_number
    return total * total
"""
tool = aix.Tool(
    name="Sum and Square",
    description="Sums two numbers and squares the result.",
    integration="688779d8bfb8e46c273982ca",
    config={"code": script_content, "function_name": "sum_then_square"},
).save()

result = tool.run(action="sum_then_square", data={"first_number": 2, "second_number": 3})
```

---

## 5. MCP Server (`686eb9cd26480723d0634d3e`)

Connect with authenticated MCP server URL (often includes token).

After connect, inspect full action list and disable destructive actions by default. Keep scoped action set minimal.

### Studio Flow

1. Integrations -> MCP Server -> Connect
2. Enter integration name + MCP URL
3. Connect and inspect `Actions`
4. Enable only required actions
5. Save agent

### SDK Flow

```python
mcp_tool = aix.Tool(
    integration="aixplain/mcp-server",
    name="Remote MCP Tool",
    description="Remote MCP integration tool",
    config={"url": "<mcp_server_url>"},
    allowed_actions=["fetch"],
).save()

# Optional direct test
mcp_tool.run(action="fetch", data={"url": "https://www.aixplain.com"})

# Attach to agent
agent = aix.Agent(
    name="MCP Agent",
    description="Fetches URL content via MCP.",
    instructions="Use the MCP fetch tool to retrieve webpage content.",
    output_format="markdown",
    tools=[mcp_tool.as_tool()],
).save()
```

### Apify-Specific URL Pattern

- Token-based auth: `https://actors-mcp-server.apify.actor/mcp?token=<APIFY_TOKEN>`
- Endpoint must include `/mcp` for aiXplain MCP connect path.
- Available actions include: `fetch-actor-details`, `search-actors`, `call-actor`, `search-apify-docs`, `fetch-apify-docs`, `apify-slash-rag-web-browser`, `get-actor-output`.

### Troubleshooting

- Error `There is nothing at route POST /...` -> wrong MCP endpoint path (missing `/mcp` or incompatible route).
- Tool not invoked -> make instructions explicit about when to use MCP and which action to prefer.
- Too many parameters/actions -> scope `allowed_actions` to a narrow vetted set.

---

## 6. OAuth Integrations (Gmail, Slack, Jira, Google Drive)

**CRITICAL:** The entire SDK Tool/Integration pipeline is broken for OAuth integrations.
`Integration.get()`, `Tool.get()`, and `Tool.search()` all crash with `AttributeError: 'str' object has no attribute 'items'` due to `dataclasses_json` deserialization failures. **Use REST throughout.**

### REST-First Pattern (the only reliable path)

```python
import requests

BACKEND_URL = "https://platform-api.aixplain.com"
MODELS_RUN_URL = "https://models.aixplain.com/api/v2/execute"
H = {"x-api-key": API_KEY, "Content-Type": "application/json"}

# ── Step 1: Create OAuth tool via integration run endpoint ──
INTEGRATION_ID = "6864328d1223092cb4294d30"  # Gmail
resp = requests.post(f"{MODELS_RUN_URL}/{INTEGRATION_ID}", headers=H,
    json={"name": "My Gmail Tool", "description": "Read and draft emails"})
data = resp.json()

if data.get("status") == "FAILED" and "already exists" in data.get("supplierError", ""):
    # Name collision — search via REST or use timestamped name
    search = requests.get(f"{BACKEND_URL}/sdk/models",
        headers=H, params={"query": "My Gmail Tool", "pageSize": 50, "function": "utilities"})
    items = search.json().get("items", [])
    tool_id = next((i["id"] for i in items if i["name"] == "My Gmail Tool"), None)
else:
    tool_id = data["data"]["id"]
    redirect_url = data["data"].get("redirectURL")
    if redirect_url:
        print(f"⚠️ OAuth required — user must visit: {redirect_url}")

# ── Step 2: Fetch tool metadata via REST ──
# IMPORTANT: OAuth tools live under /sdk/models/, NOT /sdk/tools/
model_data = requests.get(f"{BACKEND_URL}/sdk/models/{tool_id}", headers=H).json()

# ── Step 3: Build agent-compatible payload ──
tool_payload = {
    "id": tool_id,
    "assetId": tool_id,
    "name": model_data["name"],
    "description": model_data.get("description", ""),
    "supplier": model_data.get("supplier", {}).get("code", "aixplain"),
    "parameters": model_data.get("params", []),
    "function": model_data.get("function", {}).get("id", "utilities"),
    "type": "tool",       # MUST be "tool" — "model" fails API validation
    "version": model_data.get("version", {}).get("id"),
    "actions": ["GMAIL_FETCH_EMAILS", "GMAIL_CREATE_EMAIL_DRAFT"],  # scoped actions
}
```

### Key Gotchas

1. **`type` must be `"tool"`** — `Model.as_tool()` returns `"model"` which fails validation for OAuth tools.
2. **REST endpoint is `/sdk/models/`** — `/sdk/tools/{id}` returns 404 for OAuth tools.
3. **Name collisions return no ID** — you must search or use timestamped names.
4. **OAuth redirect URL** — returned at creation time only. Capture and present to user.
5. **Agent update via REST** — if SDK `agent.save()` drops tool scopes, use `PUT /sdk/agents/{id}` directly.

### Pre-Connected Tools (from dashboard)

If a tool was already connected via the platform dashboard, skip creation and go straight to Step 2 (fetch metadata by known tool ID) and Step 3 (build payload).
