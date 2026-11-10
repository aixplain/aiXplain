# Knowledge bases (RAG) & memory

## Knowledge base = an index tool on aiR

A knowledge base is a vector index created as a `Tool` bound to the aiR knowledge-base integration. There is no separate `Index` class — it's `aix.Tool(...)`. Workflow: **create → upsert documents → scope to read-only → attach to agent.**

### 1. Create

```python
import time
index = aix.Tool(
    name=f"Product Index {int(time.time())}",
    description="Vector database for product information.",
    integration="aixplain/air-knowledge-base/aixplain",   # or the asset id below
    # optional: pick the embedding model used at upsert time
    # config={"model": "67efd4f92a0a850afa045af7"},       # BGE-M3
)
index.save()
index.list_actions()    # exactly six: search, count, upsert, get, delete, metadata
```

> **Asset path vs hex id.** The docs now lead with the asset **path** `aixplain/air-knowledge-base/aixplain`. The hex id `6904bcf672a6e36b68bb72fb` is **unchanged and still current** (it is the integration's marketplace card, `https://app.aixplain.com/marketplace/integrations/6904bcf672a6e36b68bb72fb`). Both forms work: `Tool.integration` is typed `Union[Integration, str]` and the string is resolved with `Integration.get(...)`, which accepts either an id or a path. The embedding model `67efd4f92a0a850afa045af7` is unchanged too — the docs now name it **BGE-M3**.

Actions, and what each returns:

| Action | Returns |
|---|---|
| `upsert` | `{'status': 'success'}` — adds or replaces documents |
| `search` | list of records: `id`, `text`, `score`, `metadata` |
| `get` | the **list of chunks** for one document id |
| `delete` | removes a document id — i.e. **all** of its chunks |
| `count` | number of stored **chunks**, not documents |
| `metadata` | every metadata field and its stored distinct values |

### 2. Ingest documents (`upsert`)

Records are dicts: `text` is the only required key. Add an `id` so you can update or delete the document later, and `metadata` to filter on it. (The retired page capped document text at 100,000 characters; the rewritten page drops that number and states the binding limit differently — see the chunk-size note below.)

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

Two rules the rewritten page adds: when you pass `chunking` at all, pass **`split_by`, `split_length` and `split_overlap` together** rather than overriding one of them; and **each chunk must fit the embedding model's input limit** — 8,192 tokens for the default model. Overshooting it fails the upsert with `maximum context length is 8192 tokens`; lower `split_length`, or split by `"word"` for text with no sentence breaks.

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
# prod3#chunk1 Stainless steel water bottle … 0.811
# ids carry a #chunk suffix — documents are split into chunks on upsert

# Limit the result count + metadata filters — use num_results, NOT top_k
r = index.run(action="search", data={
    "query": "headphones", "num_results": 5,
    "filters": [{"field": "category", "operator": "==", "value": "electronics"}],
})
```

> **Result-count key — use `num_results`. ⚠️ Field-verified.** `num_results` is the key the aiR service actually honours. `top_k` is **silently ignored**: the request succeeds and comes back `200`, the limit simply isn't applied, so you get the service default rather than an error telling you the key was wrong. This was established by probing a live index.
>
> The docs have now **come round to this**: the rewritten knowledge-base page uses `num_results` in every search example and its troubleshooting table blames a short result list on "no `num_results` set" — the earlier page's `top_k` example is gone. The SDK has **not**: `aixplain/v2/rlm.py` still builds its RAG queries as `{"query": …, "top_k": top_k}` (0.2.48, line ~1706), so first-party RLM retrieval is still passing the ignored key. That remaining SDK-vs-reality conflict isn't provable from the source either way — both keys are untyped pass-throughs in the `data` payload, so nothing in the SDK validates either one. Write `num_results`, and if you inherit code using `top_k`, check the returned record count before assuming the limit took effect.

Filter conditions are combined with **AND**. Operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in` — pass a list as the `value` for `in`/`not in`, and a number or an ISO 8601 date for the comparisons. **Field names are case-sensitive**; the `metadata` action lists the valid ones.

Other actions — `get`, `delete`, `count`, `metadata`. `get` accepts a bare id string, and `count`/`metadata` need no `data` at all:

```python
index.run(action="get", data={"id": "doc1"})   # -> list of that document's chunks
index.run(action="get", data="doc1")     # bare string, equivalent to the above
index.run(action="delete", data={"id": "doc1"})   # removes every chunk of doc1
index.run(action="count")                 # no `data` -> {'status': 'success', 'data': 5} = chunk count
index.run(action="metadata")              # no `data` -> distinct values per metadata field, e.g.
                                          # {'type': ['simple','aggregate'], 'color': ['green','yellow','red']}
```

### 4. Attach to an agent (agentic RAG)

Scope to read-only first, and **tell the agent in its instructions to search the index** — otherwise it may not call the tool.

```python
index.allowed_actions = ["search"]      # keeps the agent from writing to or deleting from the index
agent = aix.Agent(
    name="Product Assistant",
    description="Helps users find products.",
    instructions="Search the product index to answer questions. Include price and category.",
    tools=[index],
)
agent.save()
print(agent.run("Find affordable electronics under $200.").data.output)
```

> **`allowed_actions` also gags you, not just the agent.** The check is **client-side** — `Tool._validate_params` rejects the call before any request goes out (`Action 'get' is not allowed for this tool. Allowed actions: [...]`, `aixplain/v2/tool.py:510`). So once you scope an index down for an agent, your own `index.run(action="get", …)` starts failing. Reset with `index.allowed_actions = []` before running other actions yourself. (Related, same file: when `allowed_actions` holds exactly **one** entry, `run()` fills `action` in for you.)

> Only **vector** semantic search is documented for the index tool. The platform also describes graph and SQL retrieval (GraphRAG) at a higher level, but those aren't exposed as distinct index-tool modes in the SDK docs — use the SQL integrations (`references/tools-integrations.md`) for relational data.

## Memory

| Type | Mechanism | Scope |
|---|---|---|
| Short-term / session | `aix.Session` — see **`references/agents.md`** | one conversation |
| Long-term, cross-session | Shared Memory tool | durable across runs/sessions |
| Shared across agents | Shared Memory tool attached to multiple agents | any agent holding the tool |

### Session memory (short-term) — not covered here

Multi-turn conversation state is no longer a memory-side concern: it is `aix.Session`, passed as `agent.run(session=...)`. **See `references/agents.md`** for the whole session lifecycle and API (and `references/deployment-access.md` for the REST wire field).

### Shared memory (long-term / cross-agent)

> **Where this lives upstream.** Shared Memory no longer has its own docs page — it was folded into the **Sessions** page (`docs/assets/agents/sessions.md`, under "Share memory across sessions"). Treat that page as the source for both; the session lifecycle itself is covered in **`references/agents.md`**, not here.

aiXplain-managed, persists across runs and sessions, no third-party key (connecting it just creates a private aiXplain-managed tool asset in your workspace). Integration path `aixplain/shared-memory/aixplain`; marketplace asset `69a59de88e25a303cbf1b8c6` (`https://app.aixplain.com/marketplace/integrations/69a59de88e25a303cbf1b8c6`) — **unchanged**.

Model: it is a single **text buffer** of facts. The agent appends to it when the user says something durable and reads the whole thing at the start of each run, which is why an agent answers from it with **no session and no history** in play.

```python
shared = aix.Tool(
    integration="aixplain/shared-memory/aixplain",
    name="Account Memory",
    description="Persistent memory for account context.",
    config={
        "max_memory_size": 256,                         # words; default 1028
        # default is "forget" (drops oldest lines); "summarize" compresses via the manager model
        "size_management_policy": "summarize",
        "memory_manager_model": "6895d6d1d50c89537c1cf237",  # optional; see note below
    },
    allowed_actions=["insert", "get", "update", "optimize"],
)
shared.save()

shared.run(action="insert", data={"content": "ACME Corp prefers weekly updates."})
shared.run(action="get", data={})            # -> whole buffer as text in .data
shared.run(action="update", data={"content": "…"})   # REPLACES the whole buffer
shared.run(action="optimize", data={})       # compress/clean up via the manager model
```

| Action | What it does |
|---|---|
| `insert` | Appends `content` to the buffer |
| `get` | Returns the whole buffer as text |
| `update` | **Replaces** the whole buffer with `content` |
| `optimize` | Compresses and cleans up the buffer with the memory manager model |

`update` is newly documented — the retired page listed only `insert` / `get` / `optimize`. It is destructive by design; don't hand it to an agent unless overwriting is the point.

Config fields (all optional, all set at creation):

| Field | Default | Notes |
|---|---|---|
| `max_memory_size` | `1028` | Maximum buffer size in **words**. The retired page added: max accepted `4096`, and it falls back to `1028` if missing, invalid, or `< 1`. The new page states only the default — treat the `4096` ceiling as unconfirmed. |
| `size_management_policy` | `"forget"` | Past the limit, `"forget"` drops the oldest lines; `"summarize"` compresses older content with the manager model. |
| `memory_manager_model` | platform default | Asset id or name of the LLM used by `"summarize"` **and** by `optimize`. The retired page pinned this default to GPT-5 Mini (`6895d6d1d50c89537c1cf237`); the new page says only "platform default", so **don't assume that id is still what you get** — pass it explicitly if you need that model. |

Inspect what each action takes with `Tool.list_inputs(*actions)`:

```python
for action in shared.list_inputs("insert", "get", "optimize"):
    print(action.name, [(p.code or p.name, p.required) for p in action.inputs or []])
# get      -> identifier (optional)
# insert   -> content (required), identifier (optional)
# optimize -> identifier (optional)
```

Per-user isolation: pass an `identifier` to read and write a **separate buffer per end user** — on `insert`, `get` and `optimize` alike (e.g. `data={"identifier": "customer-123", "content": "..."}`). It is a runtime-only field: not a `config` key, and it does not appear in the Studio connect dialog. A buffer is **empty (`''`) until something is written under its identifier** — an unknown identifier reads back blank rather than erroring, so a typo looks like amnesia, not a failure.

Attach the tool to one or more agents (often `allowed_actions=["insert"]`) and the stored context is injected into the agent's prompt:

```python
agent = aix.Agent(name="Support Agent", description="...", instructions="...", tools=[shared])
agent.save()
agent.run(query="What pattern should we use for ACME Corp?")
```
