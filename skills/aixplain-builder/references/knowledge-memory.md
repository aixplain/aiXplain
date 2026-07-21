# Knowledge bases (RAG) & memory

## Knowledge base = an index tool on aiR

A knowledge base is a vector index created as a `Tool` bound to the aiR vector database integration `6904bcf672a6e36b68bb72fb`. There is no separate `Index` class — it's `aix.Tool(...)`. Workflow: **create → upsert documents → scope to read-only → attach to agent.**

### 1. Create

```python
import time
index = aix.Tool(
    name=f"Product Index {int(time.time())}",
    description="Vector database for product information.",
    integration="6904bcf672a6e36b68bb72fb",     # aiR vector database — always this ID
    # optional: pick the embedding model used at upsert time
    # config={"model": "67efd4f92a0a850afa045af7"},
)
index.save()
index.list_actions()    # search, count, upsert, get, delete, metadata (also: split)
```

### 2. Ingest documents (`upsert`)

Records are dicts with `id` and `text` (required) and optional `metadata` (enables filtering). Text is capped at 100,000 characters per document.

```python
documents = [
    {"id": "doc1", "text": "Wireless headphones, $79, electronics", "metadata": {"category": "electronics", "price": 79}},
    {"id": "doc2", "text": "Cotton t-shirt, $19, apparel",          "metadata": {"category": "apparel", "price": 19}},
]
index.run(action="upsert", data={"records": documents})

# Chunk long texts on the way in:
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "sentence",   # "word" | "sentence" | "character"
                 "split_length": 3, "split_overlap": 1},
})
```

Loading from CSV (metadata columns come back as strings — re-parse):

```python
import ast, pandas as pd
df = pd.read_csv("documents.csv")
df["metadata"] = df["metadata"].apply(ast.literal_eval)
documents = df.to_dict(orient="records")
```

> Source documents (PDFs, web pages, etc.) are preprocessed by you into the `text` field — the index ingests records, not raw files/URLs directly.

### 3. Search directly

```python
r = index.run(action="search", data={"query": "yellow fruit"})
for rec in r.data:
    print(rec["id"], rec["text"], rec.get("score"))

# With top_k + metadata filters
r = index.run(action="search", data={
    "query": "headphones", "top_k": 5,
    "filters": [{"field": "category", "operator": "==", "value": "electronics"}],
})
```

Filter operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`. Other actions: `get` (`data={"id": "doc1"}`), `delete`, `count`, `metadata` (inspect index config).

### 4. Attach to an agent (agentic RAG)

Scope to read-only first, and **tell the agent in its instructions to search the index** — otherwise it may not call the tool.

```python
index.allowed_actions = ["search", "get"]
agent = aix.Agent(
    name="Product Assistant",
    description="Helps users find products.",
    instructions="Search the product index to answer questions. Include price and category.",
    tools=[index],
)
agent.save()
print(agent.run("Find affordable electronics under $200.").data.output)
```

> Only **vector** semantic search is documented for the index tool. The platform also describes graph and SQL retrieval (GraphRAG) at a higher level, but those aren't exposed as distinct index-tool modes in the SDK docs — use the SQL integrations (`references/tools-integrations.md`) for relational data.

## Memory

| Type | Mechanism | Scope |
|---|---|---|
| Short-term / session | `agent.run(session_id=...)` + `generate_session_id()` | one conversation |
| Long-term, cross-session | Shared Memory tool | durable across runs/sessions |
| Shared across agents | Shared Memory tool attached to multiple agents | any agent holding the tool |

### Session memory (short-term)

```python
session_id = agent.generate_session_id()          # or generate_session_id(history=[{"role","content"}, ...])
agent.run(query="My name is Sam.", session_id=session_id)
agent.run(query="What's my name?", session_id=session_id)   # remembers within the session
```

### Shared memory (long-term / cross-agent)

aiXplain-managed, persists across runs and sessions, no third-party key. Integration path `aixplain/shared-memory/aixplain`.

```python
shared = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Persistent memory for account context.",
    config={
        "max_memory_size": 256,                         # words; default 1028, max 4096
        "memory_manager_model": "6895d6d1d50c89537c1cf237",  # GPT-5 Mini (default)
        "size_management_policy": "summarize",          # "summarize" | "forget" (default)
    },
    allowed_actions=["insert", "get", "optimize"],
)
shared.save()

shared.run(action="insert", data={"content": "ACME Corp prefers weekly updates."})
shared.run(action="get", data={})           # -> stored text in .data
shared.run(action="optimize", data={})       # compress/summarize stored memory
```

Per-user isolation: pass an `identifier` to `insert`/`get` (e.g. `data={"identifier": "customer-123", "content": "..."}`). Attach the tool to one or more agents (often `allowed_actions=["insert"]`) and the stored context is injected into the agent's prompt:

```python
agent = aix.Agent(name="Support Agent", description="...", instructions="...", tools=[shared])
agent.save()
agent.run(query="What pattern should we use for ACME Corp?")
```
