# Integration build and data tools (SDK v2)

Read this when creating deterministic tools, enabling runtime code, working with databases or knowledge, or handling files.

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

### Python Sandbox authoring contract

Use Python Sandbox for a small, deterministic function authored at build time—not for an agent to generate code during a run, and not as an implicit replacement for an approved external integration.

- Define one clear entry function with JSON-compatible inputs and a `dict` or `list` result.
- Prefer the Python standard library. Do not assume third-party packages, network access, filesystem persistence, environment variables, or credentials are available unless the live integration schema and a standalone run prove the requirement works.
- Never embed API keys, tokens, customer data, or workspace-bound IDs in `code`.
- Keep side effects explicit and minimal. Use a supported integration with explicit user consent when the job needs an external system.
- Inspect the current integration actions and input schema before generating code that depends on a Sandbox capability.
- Run one representative success case and one expected failure case directly through the tool before attaching it to an agent; then verify the agent trace includes the tool when the capability is required.

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
