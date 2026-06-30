# Deployment & access (REST, JS, OpenAI-compatible, API keys)

## Deploying agents

`agent.save()` **is** the deployment step — there is no separate `agent.deploy()`. Saving promotes the agent from `DRAFT` to `ONBOARDED`, giving it a persistent, autoscaling serverless endpoint on aiXplain's managed cloud, reachable by ID via the REST API below. For teams use `team.save(save_subcomponents=True)`.

After deploy, point the user to Studio:
- Visual builder / traces: `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- Analytics: `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

**Private / on-prem / edge:** the same agent definition runs unchanged across managed cloud, on-prem (including air-gapped, zero outbound), and edge — governance and memory travel with it. On-prem deploys as containerized services (Docker Compose / Kubernetes) and is arranged via aiXplain, not toggled by an SDK flag. There is no documented per-deployment SDK config (e.g. custom backend URL) — point enterprise users to aiXplain for on-prem setup.

## REST API — run a deployed agent

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

## REST API — run a model directly

One execute endpoint for all modalities. Base `https://models.aixplain.com`.

```bash
curl -X POST 'https://models.aixplain.com/api/v2/execute/<MODEL_ID>' \
  -H 'x-api-key: YOUR_API_KEY' -H 'Content-Type: application/json' \
  -d '{"text": "What is 2 + 2?"}'
```

If the response has `"completed": true`, the result is in `data`. If `data` is a URL, poll that exact URL (host/version can vary per service) until completed. Other inputs: LLM gen params (`max_tokens`, `temperature`); chat `text` as a `[{role,content}]` array; vision via a `content` array with `image_url.url` parts (public URL or `data:` base64); TTS `text`; ASR `language` + `source_audio` URL; SSE streaming with `"stream": true` (ends with `data: [DONE]`); provider-raw via `"options": {"includeRawData": true}`.

Discover a model's parameters: `GET https://platform-api.aixplain.com/sdk/models/<MODEL_ID>` (returns a `params` array with name/required/dataType/defaultValues).

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

> The docs show base URL `https://api.aixplain.com/v1` with a bare asset ID as `model`. Other materials reference `https://models.aixplain.com/api/v1/` and an `agent-<id>` model form. If one form 404s, try the other and confirm against the user's Studio console.

## Upload a local file (REST)

The execute endpoints take URLs, not file bytes. Upload first (note: file-upload endpoints use `Authorization: token YOUR_API_KEY`, **not** `x-api-key`):

1. `POST https://platform-api.aixplain.com/sdk/file/upload/temp-url` with `{contentType, originalName}` → `{key, uploadUrl, downloadUrl}`
2. `PUT` the file bytes to `uploadUrl`
3. Pass `downloadUrl` to the model/agent.

From Python the SDK wraps this: `FileUploader(api_key=...).upload(file_path, is_temp=True, return_download_link=True)` (use `return_download_link=True` to get a browser-clickable URL, not a raw `s3://` path). Size limits: audio 50 MB, image/documents 25 MB, video/database 300 MB.

## MCP server access

Every marketplace model/tool is reachable over MCP at `https://models-mcp.aixplain.com/mcp/<ASSET_ID_OR_ENCODED_PATH>` (URL-encode `/` as `%2F`). Auth differs again: `Authorization: Bearer <KEY>` plus `Accept: application/json, text/event-stream`. Add to Claude Code: `claude mcp add --transport http <name> <url> --header "Authorization: Bearer <key>"`.

## API keys & least-privilege

Keys come from Console → Settings → API Keys (`https://console.aixplain.com/settings/keys`); the full key is shown once. Max 10 per workspace; keys are workspace-specific. Scope a key to specific assets and rate limits:

```python
from aixplain.v2 import APIKey, APIKeyLimits, TokenType

key = APIKey.get("your-api-key-id")
key.asset_limits = [APIKeyLimits(
    model="6646261c6eb563165658bbb1",          # asset ID (not path)
    token_per_minute=300_000, token_per_day=144_000_000,
    request_per_minute=60, request_per_day=28_800,
    token_type=TokenType.OUTPUT,
)]
key.save()
```

Monitor usage: `aix.APIKey.get_usage_limits()` or `get_usage_limits(model=MODEL_ID)` (use IDs, not paths). Rate-limit errors surface as HTTP **497** (aiXplain per-minute) or **429**. Other REST errors: 401 bad key, 492 unfetchable input URL, 400 malformed/empty `query`.

## Credits & billing

1 credit = $1 USD. Models/tools/integrations bill at vendor rates (0% margin). Deployed **agents** add a 20% markup over the sum of model + tool calls (covers orchestration, the planner/orchestrator/inspector micro-agents, memory, validation). Track spend via `response.used_credits`, Console → Transactions, or the Studio Validation tab.

## What the v2 SDK does NOT cover (legacy v1 only)

The unified `aix.*` client (`from aixplain import Aixplain`) is agent/model/tool-centric. **Pipelines, fine-tuning, benchmarking, and datasets/corpora have no v2 API.** They exist only in the legacy v1 factories:

```python
# Legacy v1 — only if the user explicitly needs these capabilities
from aixplain.factories import PipelineFactory, FinetuneFactory, BenchmarkFactory, DatasetFactory, CorpusFactory
pipeline = PipelineFactory.get("<pipeline_id>")
result = pipeline.run("input")
```

For **pipelines**, prefer building visually in aiXplain Studio and then running by ID (Studio, REST `https://platform-api.aixplain.com` pipeline endpoints, or the v1 `PipelineFactory`). The current Python v2 SDK has no pipeline builder. If a user asks to "build a pipeline" in Python, tell them this and offer either Studio or the equivalent as a **team agent** (which is the v2-native way to compose multi-step workflows).

## v1 → v2 migration

Use `from aixplain import Aixplain; aix = Aixplain(api_key=...)` then `aix.Agent` / `aix.Model` / `aix.Tool`. Avoid the deprecated v1 `aixplain.factories.*` (`AgentFactory`, `ModelFactory`, …) for anything the v2 client covers. If you see old factory code, port it to the `aix.*` equivalents.
