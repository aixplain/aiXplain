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
index.list_actions()    # exactly six: search, count, upsert, get, delete, metadata
```

### 2. Ingest documents (`upsert`)

Records are dicts with `id` and `text` (required) and optional `metadata` (enables filtering). Text is capped at 100,000 characters per document.

```python
documents = [
    {"id": "doc1", "text": "Wireless headphones, $79, electronics", "metadata": {"category": "electronics", "price": 79}},
    {"id": "doc2", "text": "Cotton t-shirt, $19, apparel",          "metadata": {"category": "apparel", "price": 19}},
]
index.run(action="upsert", data={"records": documents})

# Override the default chunking (defaults are sentence / 10 / 3 — see the table):
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "sentence", "split_length": 3, "split_overlap": 1},
})

# Store each document as one record — no chunking at all:
index.run(action="upsert", data={"records": documents, "chunking": {"enabled": False}})

# Delimiter / regex splitting:
index.run(action="upsert", data={
    "records": documents,
    "chunking": {"split_by": "regex", "split_delimiter": r"\n#{1,3}\s",
                 "split_length": 1, "split_overlap": 0},
})
```

Omitting `chunking` entirely applies the defaults below — **not** the `3`/`1` shown above.

| `chunking.*` | Type | Default | Notes |
|---|---|---|---|
| `enabled` | `bool` | `true` | `false` = one record per document, no splitting |
| `split_by` | `str` | `"sentence"` | `word` \| `sentence` \| `passage` \| `page` \| `line` \| `string` \| `regex` — there is **no** `"character"` |
| `split_length` | `int` | `10` | units per chunk, `>= 1` |
| `split_overlap` | `int` | `3` | `>= 0` **and** `< split_length` |
| `split_delimiter` | `str` | — | required when `split_by` is `"string"` or `"regex"` |

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

> **Result-count key — `top_k` vs `num_results`.** The current docs' filter example passes `num_results`, but the SDK's own first-party caller (`aixplain/v2/rlm.py`) builds index queries with `top_k`. Both are pass-through `data` keys to the aiR service. Keep using `top_k`; if a query ignores it, try `num_results` before assuming the limit is unsupported.

Filter operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`.

Other actions — `get`, `delete`, `count`, `metadata` (inspect index config). `get` accepts a bare id string, and `count`/`metadata` need no `data` at all:

```python
index.run(action="get", data={"id": "doc1"})
index.run(action="get", data="doc1")     # bare string, equivalent to the above
index.run(action="count")                 # no `data`
index.run(action="metadata")              # no `data` -> distinct values per metadata field, e.g.
                                          # {'type': ['simple','aggregate'], 'color': ['green','yellow','red']}
```

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
| Short-term / session | `aix.Session` — see **`references/agents.md`** | one conversation |
| Long-term, cross-session | Shared Memory tool | durable across runs/sessions |
| Shared across agents | Shared Memory tool attached to multiple agents | any agent holding the tool |

### Session memory (short-term) — moved

Multi-turn conversation state is no longer a memory-side concern. `Agent.generate_session_id()` has been **removed**, and `session_id=` is no longer an `agent.run()` parameter — it is silently dropped if passed, so a run that looks session-scoped is actually stateless. The replacement is `aix.Session`, passed as `agent.run(session=...)`.

**See `references/agents.md`** for the Session API. (Over REST the wire field is still `sessionId` — see `references/deployment-access.md`.)

### Shared memory (long-term / cross-agent)

aiXplain-managed, persists across runs and sessions, no third-party key (connecting it just creates a private aiXplain-managed tool asset in your workspace). Integration path `aixplain/shared-memory/aixplain`; marketplace asset `69a59de88e25a303cbf1b8c6` (`https://app.aixplain.com/marketplace/integrations/69a59de88e25a303cbf1b8c6`).

```python
shared = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Persistent memory for account context.",
    config={
        "max_memory_size": 256,                         # words; default 1028, max 4096
        "memory_manager_model": "6895d6d1d50c89537c1cf237",  # GPT-5 Mini (default)
        # default is "forget" (drops oldest lines); "summarize" compresses via the manager model
        "size_management_policy": "summarize",
    },
    allowed_actions=["insert", "get", "optimize"],
)
shared.save()

shared.run(action="insert", data={"content": "ACME Corp prefers weekly updates."})
shared.run(action="get", data={})           # -> stored text in .data
shared.run(action="optimize", data={})       # compress/summarize stored memory
```

Inspect what each action takes with `Tool.list_inputs(*actions)`:

```python
for action in shared.list_inputs("insert", "get", "optimize"):
    print(action.name, [(p.code or p.name, p.required) for p in action.inputs or []])
# get      -> identifier (optional)
# insert   -> content (required), identifier (optional)
# optimize -> identifier (optional)
```

Per-user isolation: pass an `identifier` to `insert`, `get` **and** `optimize` (e.g. `data={"identifier": "customer-123", "content": "..."}`). It is a runtime-only field — it is not a `config` key and does not appear in the Studio connect dialog. Attach the tool to one or more agents (often `allowed_actions=["insert"]`) and the stored context is injected into the agent's prompt:

```python
agent = aix.Agent(name="Support Agent", description="...", instructions="...", tools=[shared])
agent.save()
agent.run(query="What pattern should we use for ACME Corp?")
```
