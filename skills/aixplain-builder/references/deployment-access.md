# Deployment & access (REST, JS, OpenAI-compatible, API keys)

## Deploying agents

`agent.save()` **is** the deployment step — there is no separate `agent.deploy()`. Saving promotes the agent from `DRAFT` to `ONBOARDED`, giving it a persistent, autoscaling serverless endpoint on aiXplain's managed cloud, reachable by ID via the REST API below. For teams use `team.save(save_subcomponents=True)`.

After deploy, point the user to the app (everything moved from `console.`/`studio.` to **`app.aixplain.com`**):
- Dashboard — usage, latency, cost, run traces: `https://app.aixplain.com/dashboard`
- Marketplace: `https://app.aixplain.com/marketplace`
- Visual builder: `https://app.aixplain.com/studio` · Analytics: `https://app.aixplain.com/dashboard`
  (aiXplain consolidated onto `app.aixplain.com`: as of docs `f5c016a` there are **zero** `studio.aixplain.com` / `console.aixplain.com` references left, and no per-agent deep link such as `/build/<ID>/schema` is documented. Hand the user the agent **ID** with the link.)

### Three deployment modes

The agent definition and its governance are identical in all three; choose on data and infrastructure needs.

| Mode | Where it runs | Choose it for |
|---|---|---|
| **Web (serverless)** | aiXplain-managed cloud — the default | Fastest path to production, autoscaling handled for you |
| **On-prem** | Your own infrastructure, including air-gapped | Data sovereignty, regulatory compliance, zero outbound connectivity |
| **Desktop** | The user's own machine, via aiXplain Desktop | Local or cloud models/tools with work kept on-device |

"Edge" is no longer a documented mode — **Desktop** replaced it.

**Desktop** has **no SDK surface at all**: no flag, no class, nothing in `dir(Aixplain)`. Point users to the guide at `https://app.aixplain.com/guide/desktop`; do not invent an SDK API for it.

**On-prem** runs the whole platform inside the customer network — install, updates, license validation and runtime are self-contained, and aiXplain staff have no access to the environment. It is arranged via aiXplain, **not toggled by an SDK flag**, and there is no documented per-deployment SDK config (e.g. custom backend URL).

- Containerized services on **Linux (Docker / Docker Compose)**, scaled out behind a load balancer; GPU nodes for model serving are customer-provisioned.
- Air-gapped install ships as **signed offline bundles**; updates are signed patch bundles verified by **SHA-256** checksums; **perpetual licenses validate locally with no call-home**.
- Data, models, logs and telemetry stay in-network. Inference runs **in memory with nothing written to disk by default**, and prompts/responses are never used for training. The only opt-in exceptions that persist are **RAG embeddings** and **configured agent/session memory**, governed by RBAC and model-scoped keys.
- Supports data-residency / access-governance regimes (e.g. SDAIA, NCA, GCC data protection).
- **Not all services are available on-prem** — scope the deployment with aiXplain (`https://aixplain.com/enterprise-ai/`).

### Before going live (serverless)

- Validate on representative **and adversarial** inputs, using the run traces.
- Add Inspectors for safety/quality/compliance checks.
- Set access and quotas via API keys and rate limits (below).
- Keep retries and a **primary/secondary fallback chain** for model and tool failures, and set clear **termination criteria** so the loop can't run away.
- **Capture `requestId` on every call** so platform runs correlate with your own logs.

## REST API — run a deployed agent

**Two auth header schemes — this is the usual trip-up.** Same key, different header:

| Endpoints | Header |
|---|---|
| Model/agent execution, polling, discovery (everything below except uploads) | `x-api-key: YOUR_API_KEY` |
| File upload only (`/sdk/file/upload/temp-url`, `/sdk/file/upload-url`) | `Authorization: token YOUR_API_KEY` |
| MCP endpoints (`models-mcp.aixplain.com`) | `Authorization: Bearer YOUR_API_KEY` |

Requests with a body also need `Content-Type: application/json`. The key is the **workspace (team)** key — keep it server-side.

Agent runs are always asynchronous: `POST` returns a polling URL, `GET` it until done. Auth header is `x-api-key`.

```bash
# 1. Submit
curl -X POST 'https://platform-api.aixplain.com/v2/agents/<AGENT_ID>/run' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"query": "What is 5 + 5?", "sessionId": "user_123_session"}'
# -> {"requestId": "...", "data": "https://platform-api.aixplain.com/sdk/agents/<REQUEST_ID>/result"}

# 2. Poll the URL returned in "data"
curl -X GET 'https://platform-api.aixplain.com/sdk/agents/<REQUEST_ID>/result' \
  -H 'x-api-key: YOUR_API_KEY'
# -> {"completed": true, "status": "SUCCESS", "data": {"output": "10", "session_id": "...", ...}}
```

- `query` must be **top-level** (`{"data":{"query":...}}` fails with `query should not be empty`).
- Optional top-level run params: `maxTokens`, `maxIterations`, `outputFormat` (`text`|`markdown`|`json`).
- Multi-turn: either omit `sessionId` on the first call and echo back `data.session_id` on later calls, **or** send a `history` array of `{"role","content"}` turns.
- Answer is in `data.output`. Poll while `status == "IN_PROGRESS"`; stop on `SUCCESS`/`FAILED`.

Python (requests) polling loop:

```python
import requests, time
H = {"x-api-key": API_KEY, "Content-Type": "application/json"}
start = requests.post(f"https://platform-api.aixplain.com/v2/agents/{AGENT_ID}/run",
                      headers=H, json={"query": "Summarize this ticket."}, timeout=30).json()
poll_url = start["data"]
while True:
    res = requests.get(poll_url, headers=H, timeout=30).json()
    if res.get("completed"):
        print(res["data"]["output"]); break
    time.sleep(2)
```

Equivalently, build the poll URL from `requestId` — `f"https://platform-api.aixplain.com/sdk/agents/{start['requestId']}/result"` resolves to the same path, and you want `requestId` in your logs anyway. For **models**, keep polling the exact URL returned in `data`: the polling host and version (`/api/v1/data/` vs `/api/v2/data/`) vary by service, and an in-flight model poll returns a bare `{"completed": false}` with no progress metadata.

## REST API — run a model directly

One execute endpoint for all modalities. Base `https://models.aixplain.com`.

```bash
curl -X POST 'https://models.aixplain.com/api/v2/execute/<MODEL_ID>' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"text": "What is 2 + 2?"}'
```

If the response has `"completed": true`, the result is in `data`. If `data` is a URL, poll that exact URL (host/version can vary per service) until completed. Other inputs: LLM gen params (`max_tokens`, `temperature`); chat `text` as a `[{role,content}]` array; vision via a `content` array with `image_url.url` parts (public URL or `data:` base64); TTS `text`; ASR `language` + `source_audio` URL; SSE streaming with `"stream": true` (ends with `data: [DONE]`); provider-raw via `"options": {"includeRawData": true}`.

Discover a model's parameters: `GET https://platform-api.aixplain.com/sdk/models/<MODEL_ID>` (returns a `params` array with name/required/dataType/availableOptions/defaultValues). This is the source of truth for what a model accepts — check it before assuming a field exists.

### SSE streaming (LLMs)

Add `"stream": true` to the execute body to get tokens as Server-Sent Events instead of one final response. Each event is a `data:` line carrying an OpenAI-style `chat.completion.chunk`; read incrementally from `choices[0].delta.content`. The last non-`[DONE]` event carries `usage` totals, and the stream terminates with `data: [DONE]`.

```
data: {"choices":[{"index":0,"delta":{"content":"1"},"finish_reason":null}]}
data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":8,"total_tokens":20}}
data: [DONE]
```

## JavaScript / TypeScript

```javascript
const res = await fetch(`https://platform-api.aixplain.com/v2/agents/${AGENT_ID}/run`, {
  method: "POST",
  headers: { "x-api-key": API_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ query: "What is the weather today?", sessionId: "user_123" }),
});
const { data: pollUrl } = await res.json();              // data = polling URL
// then GET pollUrl with the same x-api-key header until { completed: true }
```

## OpenAI-compatible API

Use an aiXplain agent or model as a drop-in OpenAI client.

```python
from openai import OpenAI
client = OpenAI(api_key="YOUR_AIXPLAIN_API_KEY", base_url="https://api.aixplain.com/v1")
r = client.chat.completions.create(
    model="<AGENT_OR_MODEL_ASSET_ID>",
    messages=[{"role": "user", "content": "How do I create an agent?"}],
)
print(r.choices[0].message.content)
```

> The docs show base URL `https://api.aixplain.com/v1` with a bare asset ID as `model`. Other materials reference `https://models.aixplain.com/api/v1/` and an `agent-<id>` model form. If one form 404s, try the other and confirm against the asset card in `https://app.aixplain.com`.

## Upload a local file (REST)

The execute endpoints take URLs, not file bytes. Upload first (note: file-upload endpoints use `Authorization: token YOUR_API_KEY`, **not** `x-api-key`):

1. `POST https://platform-api.aixplain.com/sdk/file/upload/temp-url` with `{contentType, originalName}` → `{key, uploadUrl, downloadUrl}`
2. `PUT` the file bytes to `uploadUrl`
3. Pass `downloadUrl` to the model/agent.

From Python the SDK wraps this: `FileUploader(api_key=...).upload(file_path, is_temp=True, return_download_link=True)` (use `return_download_link=True` to get a browser-clickable URL, not a raw `s3://` path). Size limits: audio 50 MB, image/documents 25 MB, video/database 300 MB.

## MCP server access

Any marketplace **model or tool** is reachable as a hosted MCP server — one PAYG key covers every asset the key can reach. **Agents do not expose an MCP server**; models and tools do.

**Endpoint:** `https://models-mcp.aixplain.com/mcp/<ASSET_ID_OR_ENCODED_PATH>`

| Form | Example |
|---|---|
| Asset ID | `.../mcp/6646261c6eb563165658bbb1` |
| URL-encoded path (canonical) | `.../mcp/openai%2Fgpt-4o-mini%2Fopenai` |
| Raw slash path (also works) | `.../mcp/openai/gpt-4o-mini/openai` |

Underscore-substituted paths (`openai_gpt-4o-mini_openai`) do **not** work. Auth on every request: `Authorization: Bearer <KEY>` plus `Accept: application/json, text/event-stream`.

**Direct HTTP (Streamable HTTP)** — Claude Code, VS Code, newer Cursor. One entry per asset:

```json
{"mcpServers": {"gpt4o_mini": {
  "url": "https://models-mcp.aixplain.com/mcp/openai%2Fgpt-4o-mini%2Fopenai",
  "headers": {"Authorization": "Bearer <AIXPLAIN_APIKEY>",
              "Accept": "application/json, text/event-stream"}}}}
```

Claude Code one-liner: `claude mcp add --transport http <name> <url> --header "Authorization: Bearer <key>"`.

**Stdio bridge (`mcp-remote`)** — Claude Desktop and older Cursor read `claude_desktop_config.json`, which only accepts `command` servers, so they need a local proxy. Requires Node 18+:

```json
{"mcpServers": {"gpt4o_mini": {
  "command": "npx",
  "args": ["-y", "mcp-remote",
           "https://models-mcp.aixplain.com/mcp/openai%2Fgpt-4o-mini%2Fopenai",
           "--header", "Authorization:${AUTH_HEADER}"],
  "env": {"AUTH_HEADER": "Bearer <AIXPLAIN_APIKEY>",
          "PATH": "/opt/homebrew/bin:/usr/bin:/bin"}}}}
```

> A literal space inside an `args` entry (`"Authorization: Bearer ..."`) breaks `mcp-remote` — that's why the value lives in `env.AUTH_HEADER`. Keep `npx`'s directory on `PATH` (usually `/opt/homebrew/bin` on Apple Silicon).

Rule of thumb: if the client's config takes a `url`, use direct HTTP; if it takes `command`/`args`, use the bridge.

Building your own client: the endpoint returns **SSE-formatted** JSON-RPC responses, so parse the `data:` line. Always call `tools/list` first — the tool name is dynamic (e.g. `GPT-4o Mini (669a63646eb56306647e1091)` for a model, `search` for Tavily) and input schemas vary per asset. An empty `tools/list` means the asset has no MCP-exposed actions; `404` means the path/ID isn't MCP-enabled (try the asset ID); `401` means the `Authorization: Bearer` header is missing or the key is wrong.

aiXplain's own **Marketplace Search** tool (`6960f934f316da19e5f22494`) is itself MCP-exposed, so a client can discover assets conversationally and then wire up whatever it finds.

## API keys & least-privilege

Keys come from Team settings → API keys (`https://app.aixplain.com/team/settings?tab=api-keys`); the full key is shown once. Max 10 per workspace; keys are workspace-specific and cannot be moved between workspaces.

> **The snippet below silently needs an *admin* key.** Only Owners/Admins can create admin keys, and only an admin key can set limits on or inspect other keys — a member key calling `APIKey.search()` raises `Forbidden`. The trade-off: **admin keys cannot run inference**, so you need two clients (`aix` = member key for runs, `aix_admin` = admin key for governance). Members can still call `get_usage_limits()` on their own key.

```python
from datetime import datetime
from aixplain.v2 import APIKey, APIKeyLimits, TokenType   # also: from aixplain.v2.api_key import ...

# Admin key: create a member key with per-asset + global limits, a budget and an expiry
new_key = aix_admin.APIKey(
    name="member-key-prod",
    asset_limits=[APIKeyLimits(
        model="6646261c6eb563165658bbb1",          # asset ID or path
        token_per_minute=300_000, token_per_day=144_000_000,
        request_per_minute=60, request_per_day=28_800,
        token_type=TokenType.OUTPUT,               # INPUT | OUTPUT | TOTAL; omit = input+output
    )],
    global_limits=APIKeyLimits(token_per_minute=100, token_per_day=1000,
                               request_per_minute=100, request_per_day=1000),
    budget=1000,                                   # total credits; raise the value to top up
    expires_at=datetime(2030, 1, 1),               # omit for a non-expiring key
).save()

# Edit an existing key — by ID, or by the key string itself
key = APIKey.get("your-api-key-id")
key = aix_admin.APIKey.get_by_access_key("TARGET_MEMBER_API_KEY")   # when you hold the secret, not the ID
print(key.id, key.name, key.is_admin, key.global_limits, key.asset_limits)
key.asset_limits = [APIKeyLimits(model="669a63646eb56306647e1091", request_per_minute=2)]
key.save()

aix_admin.APIKey.search()          # list every key in the workspace — admin only
```

Global and per-asset limits are **both** enforced — whichever is stricter bites first; global does not override per-model. Enforcement lives in the **Access layer inside AgenticOS** and covers every invocation path (REST, SDK, an agent's backbone LLM including team agents, and multi-agent pipelines), so capping a model caps it workspace-wide. Over-limit requests are **rejected immediately, not queued**, and limit changes take effect at the **start of the next timeframe** (next minute / next day).

Monitor usage: `aix.APIKey.get_usage_limits()` or `get_usage_limits(model=MODEL_ID)` (use IDs, not paths) → `APIKeyUsageLimit` rows with `daily_request_count/limit`, `daily_token_count/limit`, `model`. The row with `model=None` is the **global scope**; all-`None` counts just mean no global cap is configured — ignore it unless you set one.

Rate-limit errors surface as HTTP **497** (aiXplain per-minute) or **429**. Other REST errors: 401 bad key, 492 unfetchable input URL, 400 malformed/empty `query`. Error-string triage: `Invalid API key` = deleted/expired/mistyped or wrong workspace; `Rate limit exceeded` = admin-key limits or too much concurrency (back off); `Insufficient credits` = top up the workspace.

## Credits & billing

1 credit = $1 USD. Models/tools/integrations bill at vendor rates (0% margin). Deployed **agents** add a 20% markup over the sum of model + tool calls (covers orchestration, the planner/orchestrator/inspector micro-agents, memory, validation). Track spend via `response.used_credits` or the transaction history at `https://app.aixplain.com/team/settings?tab=usage`.

## What the v2 SDK does NOT cover (legacy v1 only)

The unified `aix.*` client (`from aixplain import Aixplain`) is agent/model/tool-centric. **Pipelines, fine-tuning, benchmarking, and datasets/corpora have no v2 API.** They exist only in the legacy v1 factories — which now carry a **hard removal date of 2027-02-01** (`aixplain._compat.V1_REMOVAL_DATE`, verified in the installed package). Importing v1 code emits an `AixplainV1DeprecationWarning` once per process; silence it with `AIXPLAIN_SUPPRESS_V1_DEPRECATION=1`. The porting map is **MIGRATION.md** (`https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md`) — it is not shipped inside the wheel, so an installed copy has no local file. The removal date is contingent on closing the eight factory gaps MIGRATION.md lists, but plan for it rather than against it.

```python
# Legacy v1 — only if the user explicitly needs these capabilities
from aixplain.factories import PipelineFactory, FinetuneFactory, BenchmarkFactory, DatasetFactory, CorpusFactory
pipeline = PipelineFactory.get("<pipeline_id>")
result = pipeline.run("input")
```

For **pipelines**, prefer building visually in aiXplain Studio and then running by ID (Studio, REST `https://platform-api.aixplain.com` pipeline endpoints, or the v1 `PipelineFactory`). The current Python v2 SDK has no pipeline builder. If a user asks to "build a pipeline" in Python, tell them this and offer either Studio or the equivalent as a **team agent** (which is the v2-native way to compose multi-step workflows).

## v1 → v2 migration

Use `from aixplain import Aixplain; aix = Aixplain(api_key=...)` then `aix.Agent` / `aix.Model` / `aix.Tool`. Avoid the deprecated v1 `aixplain.factories.*` (`AgentFactory`, `ModelFactory`, …) for anything the v2 client covers. If you see old factory code, port it to the `aix.*` equivalents.
