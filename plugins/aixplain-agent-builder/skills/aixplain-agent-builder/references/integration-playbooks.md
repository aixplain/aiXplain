# Integration playbooks (SDK v2)

Read only the section needed for the current agent. All examples assume:

```python
from aixplain import Aixplain

aix = Aixplain(api_key=api_key)
```

Never use v1 factories. Before connecting, call `integration.list_actions()` and `integration.list_inputs(action_name)`. Scope every attached tool to a non-empty least-privilege `allowed_actions` list.

## Discover before connecting

```python
matches = aix.Integration.search(query="slack").results
for item in matches:
    print(item.name, item.id, item.path)

integration = aix.Integration.get(matches[0].id)
print(integration.list_actions())
```

Do not choose solely by display name. Prefer `aixplain/...` first-party paths over brokered connectors when both meet the requirement.

## Existing marketplace tool

```python
tool = aix.Tool.get("<TOOL_ID_OR_PATH>")
print(list(tool.actions))
tool.allowed_actions = ["required_action"]
```

`tool.actions` is an `Actions` collection. Use `list(tool.actions)`; `.keys()` and numeric indexing are not reliable.

## OAuth integration

Ask before initiating the external connection. State the minimum actions and why they are needed.

```python
import warnings

integration = aix.Integration.get("6864328d1223092cb4294d30")  # Gmail
print(integration.list_actions())

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    tool = aix.Tool(
        name="Customer Email Sender",
        description="Sends the final approved customer email.",
        integration=integration,
        allowed_actions=["GMAIL_SEND_EMAIL"],
    ).save()

connect_url = next(
    (str(item.message) for item in captured if "http" in str(item.message)),
    None,
)
print(connect_url)
```

The connection is workspace-specific. Create the tool fresh from the integration in each workspace; do not ship a saved connector tool ID in portable build code.

OAuth is a deliberate two-phase checkpoint: print/present the connect URL and stop that execution. Never call `input()` or wait interactively inside generated scripts. After the user confirms authorization, continue agent creation or verification in a new execution using the in-memory tool when available or its recorded workspace-local ID.

## Provider API-key integration

Ask for the provider key only after the user agrees to connect the provider. Keep it in memory/environment and never commit or print it.

```python
integration = aix.Integration.get("<INTEGRATION_ID>")
connected = integration.run(
    name="Provider Tool",
    authScheme="API_KEY",
    data={"generic_api_key": provider_api_key},
)
tool = aix.Tool.get(connected.data.id)
tool.allowed_actions = ["MINIMUM_REQUIRED_ACTION"]
tool.save()
```

The authentication field is `generic_api_key`; `api_key` and `apiKey` can fail with an unhelpful generic error.

## Missing capability: build a deterministic tool with `code=`

Use the Python Sandbox integration when no existing tool/integration meets the need and the implementation should be fixed at build time.

```python
code = """def normalize_account(name: str, domain: str):
    clean_name = " ".join(name.split()).strip()
    clean_domain = domain.lower().removeprefix("https://").rstrip("/")
    return {"name": clean_name, "domain": clean_domain}
"""

tool = aix.Tool(
    name="Normalize Account",
    description="Normalizes an account name and website domain.",
    integration="688779d8bfb8e46c273982ca",
    config={"code": code, "function_name": "normalize_account"},
    allowed_actions=["normalize_account"],
).save()
```

Authoring constraints verified on `0.2.47`:
- `function_name` must exactly match a function defined in `code`.
- Prefer `int` (`0`/`1`) over `bool` parameters because boolean serialization has produced invalid Python literals.
- Return `dict` or `list`, not tuples.
- Define custom code inline in portable build code; custom tool instance IDs are workspace-bound.
- Test the tool standalone before attaching it.

```python
result = tool.run(
    action="normalize_account",
    data={"name": "  Acme   Corp ", "domain": "https://ACME.EXAMPLE/"},
)
assert result.data["domain"] == "acme.example"
```

## Runtime Code Execution

Use Code Execution only when the deployed agent must decide and write code during a run (analysis, calculations, data transforms, plots, dynamic file processing, or API/URL processing).

```python
code_execution = aix.Tool.get("698cda188bbb345db14ac13b")
code_execution.allowed_actions = ["run"]
```

Do not add it merely because the build itself uses Python. For deterministic logic, prefer a Python Sandbox tool.

When generated files must be returned, instruct the runtime code to print metadata:

```json
[{"name":"analysis.csv","file":"analysis.csv"}]
```

Without file metadata, generated files may be lost.

## PostgreSQL

Use read-only credentials whenever possible and reinforce read-only behavior in the agent instructions.

```python
pg = aix.Tool(
    name="Customer Database Reader",
    description="Reads approved customer reporting tables.",
    integration="693ac6e8217c7b13b480970f",
    config={"url": database_url},
    allowed_actions=["schema", "query"],
).save()
```

Never enable write actions unless the user explicitly requires and approves them.

## SQLite

```python
from aixplain.v2.upload_utils import FileUploader

url = FileUploader(api_key=api_key, backend_url=aix.backend_url).upload(
    "/absolute/path/to/data.db",
    is_temp=True,
    return_download_link=True,
)

sqlite = aix.Tool(
    name="SQLite Reader",
    description="Reads the supplied SQLite database.",
    integration="689e06ed3ce71f58d73cc999",
    config={"url": url},
    allowed_actions=["schema", "query"],
).save()
```

SQLite writes apply to an in-memory copy and are not a persistence strategy.

## Knowledge base

```python
index = aix.Tool(
    name="Product Knowledge",
    description="Searches approved product documentation.",
    integration="6904bcf672a6e36b68bb72fb",
).save()

index.run(action="upsert", data={"records": [
    {"id": "doc-1", "text": "Approved product facts.", "metadata": {"type": "product"}},
]})
index.allowed_actions = ["search", "get"]
index.save()
```

Tell the agent explicitly to search the index. Otherwise it may answer from the LLM while the knowledge tool remains unused.

## Files in and out

Local paths are not portable runtime inputs. Upload and use HTTPS URLs:

```python
from aixplain.v2.upload_utils import FileUploader

url = FileUploader(api_key=api_key).upload(
    "/absolute/path/to/input.pdf",
    is_temp=True,
    return_download_link=True,
)
```

Always use `return_download_link=True` for a browser-accessible URL.

### HTML and ZIP MIME safeguard

Stable `0.2.47` omits `.html` and `.zip` from the fallback MIME map; unrecognized files fall back to `text/csv`. Patch before uploading these deliverables:

```python
from aixplain.v2.upload_utils import MimeTypeDetector

MimeTypeDetector.EXTENSION_MAPPING[".html"] = "text/html"
MimeTypeDetector.EXTENSION_MAPPING[".zip"] = "application/zip"
```

When a tool config needs an uploaded resource URL, construction alone does not upload. Call `.save()` and then read `.url`:

```python
resource = aix.Resource(name="Input Database", file_path="/absolute/path/to/data.db")
resource.save()
assert resource.url
```

`aix.Resource.create_from_file(...)` only constructs the object in `0.2.47`; its URL remains empty until `.save()` uploads it.

For deliverables, the File Manager tool is preferred:

```python
import uuid

file_manager = aix.Tool.get("6a0216cffb2a801f1c41e32e")
file_manager.allowed_actions = ["save_content"]
result = file_manager.run(
    action="save_content",
    data={
        "requestid": str(uuid.uuid4()),
        "contents": ["final report"],
        "names": ["report.md"],
    },
)
```

`requestid` is required.

## Remote MCP server

```python
mcp = aix.Tool(
    name="Remote MCP Tool",
    description="Uses the approved remote MCP capability.",
    integration="aixplain/mcp-server",
    config={"url": "https://example.com/mcp"},
).save()
mcp.allowed_actions = ["required_action"]
mcp.save()
```

Keep the exposed action set small; large MCP surfaces degrade tool selection.

## Verification sequence

For every connected or custom tool:
1. Run it directly with realistic input.
2. Attach it to the agent.
3. Run an agent prompt that requires it.
4. Confirm its unit name appears in `result.data.steps`.
5. Confirm governance allowed the run.
6. Record any reproducible platform defect in `BUGS.md`.
