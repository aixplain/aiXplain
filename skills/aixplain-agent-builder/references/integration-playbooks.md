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
uploader = FileUploader(api_key=api_key, backend_url=aix.backend_url)
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

Verified against aiXplain SDK v0.2.44. Follow these authoring constraints:

1. **`function_name` must match a function defined in `code`.** If you include multiple functions in one code block, only the one whose name equals `function_name` is registered as the tool.
2. **Use `int` (0/1) instead of `bool` parameters.** The runtime serializer passes JSON `true`/`false` (lowercase), which Python interprets as undefined names. Using `int` avoids this.
3. **Return `dict` or `list`, not tuples.** A `return a, b` round-trips as the string `"(a, b)"`. For structured output, always return a `dict` or `list`.

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

## 5. OAuth Integrations (Gmail, Slack, Jira, Google Drive)

The workflow is described in SKILL.md § 3 (Create Tools, Path C). This section provides the code.

```python
import warnings

integration = aix.Integration.get("6864328d1223092cb4294d30")  # Gmail
actions = integration.list_actions()

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    gmail_tool = aix.Tool(
        name="My Gmail Tool",
        description="Send emails",
        integration=integration,
        allowed_actions=["GMAIL_SEND_EMAIL"],
    ).save()
    oauth_url = next((str(x.message) for x in w if "http" in str(x.message)), None)

print(f"Connect Gmail: {oauth_url}")
# User completes OAuth, then attach to agent:
agent = aix.Agent(
    name="Gmail Agent", instructions="Use Gmail to send emails.",
    tools=[gmail_tool], output_format="markdown",
).save()
```
