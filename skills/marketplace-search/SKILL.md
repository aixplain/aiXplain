---
name: marketplace-search
description: Search the aixplain marketplace for agents, models, tools, and integrations — check whether an asset exists, what it costs, who hosts it, how many of a kind there are — and turn any hit into working code (SDK, REST, MCP config, or an agent that attaches it). Use whenever the user asks what is on aixplain, asks for a model/tool by name or capability, asks the price or host of an aixplain asset, or asks how to call or attach one.
---

# aixplain Marketplace Search

Searches the aixplain catalog through the `aixplain-marketplace-search` MCP server, then hands back
something runnable. One `search` covers all four asset types at once — you never need to know whether
the thing you want is a model, a tool, an agent, or an integration.

Every fact you report must come from a tool result. Never invent an asset, price, host, or count.
If every type returns `total: 0`, say the asset is not on the marketplace.

## Setup check

The tools are named `mcp__aixplain-marketplace-search__*`. If they are not available, the plugin's MCP
server has not connected — almost always a missing key. Tell the user:

```bash
export AIXPLAIN_API_KEY=your_aixplain_api_key
```

Keys come from https://studio.aixplain.com under account settings. The server is PROD.

## Which tool to call

| Question | Call |
|---|---|
| Does X exist? What is it? | `search` with `query` |
| Price, host, supplier, status | `get_asset_details` with `asset_id` |
| How many X are there? | `search` with `query: ""` plus filters, read `stats.total` |
| What inputs does it take? | `list_inputs_models` / `list_inputs_tools` / `list_inputs_agents` / `list_inputs_integrations` |
| What actions does it have? | `list_actions_models` / `list_actions_tools` / … |
| What filter values are valid? | `list_filters` (no arguments) |

`search` parameters are all flat strings or numbers — **not** arrays: `query`, `asset_type`,
`categories`, `developers`, `suppliers`, `hosts`, `function`, `num_results`, `page_number`, `page_size`.
`get_asset_details` takes `asset_id` (snake_case) and optionally `asset_type`.

`search` returns one block per asset type, each `{results: [...], stats: {total, pages_count, current_page}}`.

### The surface is only universal at discovery

Of the 19 actions, three are universal — `search`, `get_asset_details`, `list_filters` — and sixteen are
per-type variants of `search_*`, `list_actions_*`, `list_inputs_*`, `run_*`. **There is no universal
`run`.** Do not look for one. Resolve the asset's type from the `search` block it came back in (or from
`get_asset_details.asset_type`), then use the matching per-type action.

`get_asset_details` is the exception worth knowing: it takes `asset_id` alone, with `asset_type`
optional, so you can read any asset's details without knowing its type first.

### Counting

Pass an empty `query` as a wildcard and read `stats.total`. Add `page_size: 1` so you are not paying for
rows you will not read:

```
search(query: "", asset_type: "model", categories: "LLM", page_size: 1)   → stats.total = 177
```

Filter by `hosts` or `developers` the same way to narrow a count ("how many hosted by OpenAI").

There is **no sort parameter** — `search` orders by relevance only. To answer "cheapest", "newest", or
"most expensive" you must page through the filtered set and sort locally, which for a big category
(LLM alone is 177) means several calls. Say that is what you are doing rather than presenting a
single page's minimum as the catalog's minimum.
Do not count with `search_models` / `search_tools` / `search_agents` / `search_integrations` — those cap
results and carry no reliable total. Use them only to list examples.

Valid `categories` (from `list_filters`): LLM, Productivity, Marketing, Finance & Accounting, Utility,
Sales, Customer Support, Communication, Cybersecurity, Developer Tools, Search, Speech,
E-commerce & Payments, Analytics, Data & Storage, Language, Miscellaneous, Media & Creative,
Development, Image, Classification, Video, OCR, Guardrails. Call `list_filters` for the current
developer/host/supplier lists rather than guessing a name.

### Matching behavior

Keyword matching is literal. If a multi-word phrase returns nothing, retry with one distinctive token
before concluding the asset is absent — "speaker diarization whisper" may miss where "whisper" hits.

### Pricing has two shapes

Report whichever the tool returned; do not normalize one into the other.

- Per-unit assets: `{price, unit_type, unit_type_scale}` → "0.0018 per MINUTE"
- Token-priced LLMs: `{input_price, output_price}` → "0.000003 in / 0.000015 out per token"
- `null` or absent → say pricing is not listed.

For hosting, report the returned `hosted_by` value only. If it is absent or empty, say **“Hosting provider is not listed.”** Never infer a host from a model name, supplier, or price.

## Always finish the lookup

When the user asks about cost, host, supplier, function, or status, call `get_asset_details` on the
best match in the same response as the `search`. Do not stop at `search` and do not ask permission to
look up details. If several assets match strongly, detail the most relevant and name the others.

## Turning a hit into code

Resolve the asset's `id`, `path`, and `asset_type` first. For web search, prefer the first-party aixplain Web Search tool when it meets the request. Then **call the matching `list_actions_*` and `list_inputs_*` tools** and build the snippet from the real returned action and input names — `source_audio`, `text`,
`sourcelanguage`, whatever the asset actually declares. Only fall back to a `"<your input>"`
placeholder if `list_inputs_*` returns nothing usable. Never invent a parameter name.

Note which inputs are `required`, and which are `isFixed: true` with a single allowed value — a fixed
input should be emitted as that literal value, not as a choice for the user to fill in. Inputs with an
`availableOptions` list are enums: pick from it (language codes, for example) rather than free-texting.

## Testing an asset before you wire it in

**Do not use the `run_models` / `run_tools` / `run_agents` / `run_integrations` MCP actions.** They take
a single `input` string, which cannot express the multi-field input real assets declare, and they fail in
practice — verified 2026-08-18: an LLM returned `err.supplier_error` ("Input required: specify prompt or
messages") and a translation model returned HTTP 491, while the same asset ran fine through the SDK.

To actually test an asset, write the SDK call from `list_inputs_*` and run it in the shell:

```bash
python3 -c '
from aixplain import Aixplain
aix = Aixplain(api_key="'"$AIXPLAIN_API_KEY"'")
r = aix.Model.get("<id>").run(<kwargs from list_inputs>)
print(r.status, r.data)
'
```

Report the real `status` and `data`. That closes the loop — found, verified running, then integrated —
and it is the only execution path that works today.

### Python SDK

`run()` takes the input names as **keyword arguments** — not a positional dict. Use the exact `name`
values from `list_inputs_*`:

```python
from aixplain import Aixplain
aix = Aixplain(api_key="YOUR_API_KEY")

# model — one kwarg per declared input (verified against Cloud Translation)
r = aix.Model.get("66aa869f6eb56342c26057e1").run(
    text="Good morning", sourcelanguage="en", targetlanguage="ar")
print(r.status, r.data)          # SUCCESS  صباح الخير

aix.Tool.get("<id>").run(action="<action>", data={...})   # tool
aix.Agent.get("<id>").run(query="...")                   # agent
```

`Model.get("<id>").run({...})` with a positional dict raises `TypeError` — always kwargs.
Read the result off `r.status` and `r.data`.

`Model.get` / `Tool.get` also accept the supplier path (`"openai/whisper-large/groq"`), not just the id.
Integrations need a one-time connect (OAuth or API key) before they can run — point the user at the
integration's page rather than emitting a one-line call.

### Attach it to an agent

This is usually what the user actually wants after finding a tool:

```python
from aixplain import Aixplain
aix = Aixplain(api_key="YOUR_API_KEY")

agent = aix.Agent(
    name="...",
    description="...",
    instructions="...",
    tools=[aix.Tool.get("<id>")],
).save()

agent.run(query="...")
```

### REST

Headers `x-api-key: YOUR_API_KEY` and `Content-Type: application/json`.

- model: `POST https://models.aixplain.com/api/v2/execute/<id>` — body from `list_inputs_models`
- tool: `POST https://models.aixplain.com/api/v2/execute/<id>` — body `{"action": "<action>", "data": {...}}`
- agent: `POST https://platform-api.aixplain.com/v2/agents/<id>/run` — body `{"query": "..."}`

A response may return a `requestId` to poll: models and tools at
`GET https://models.aixplain.com/api/v2/data/<request_id>`, agents at
`GET https://platform-api.aixplain.com/sdk/agents/<request_id>/result`.

### MCP config for another asset

Models and tools are each individually available over hosted MCP — agents and integrations are not.
Endpoint: `https://models-mcp.aixplain.com/mcp/<id-or-URL-encoded-path>` (encode `/` as `%2F`).

Native streamable HTTP — Claude Code, VS Code, newer Cursor:

```json
{"mcpServers": {"<key>": {
  "type": "http",
  "url": "https://models-mcp.aixplain.com/mcp/<id>",
  "headers": {"Authorization": "Bearer YOUR_API_KEY", "Accept": "application/json, text/event-stream"}
}}}
```

stdio bridge — Claude Desktop and older clients without native remote MCP:

```json
{"mcpServers": {"<key>": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "https://models-mcp.aixplain.com/mcp/<id>", "--header", "Authorization:${AUTH_HEADER}"],
  "env": {"AUTH_HEADER": "Bearer YOUR_API_KEY", "PATH": "/opt/homebrew/bin:/usr/bin:/bin"}
}}}
```

Pass the key via `env.AUTH_HEADER` and reference it as `Authorization:${AUTH_HEADER}` — a literal space
inside a single `mcp-remote` arg breaks it. On Apple Silicon `npx` is usually `/opt/homebrew/bin/npx`;
keep its directory on `PATH`.

## Answering

Lead with the direct answer — yes/no, or the number — then a short bulleted detail block: path,
function, price, host, supplier, status. When listing matches, give name plus path so the user can
identify the exact asset. Never paste raw tool JSON.
