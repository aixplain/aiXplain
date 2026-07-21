---
name: aixplain-builder
description: Build, run, and deploy anything on the aiXplain platform with the Python SDK and REST/JS/OpenAI-compatible APIs — AI agents and multi-agent teams, direct model inference (LLMs, speech-to-text/Whisper, translation, vision, embeddings), knowledge bases and RAG, tools and integrations (Slack, Gmail, databases, MCP, custom Python functions), runtime governance/inspectors, memory, and serverless deployment. Use this whenever the user mentions aiXplain (aixplain/aiXplain), the `aixplain` SDK, `from aixplain import Aixplain`, `aix.Agent`/`aix.Model`/`aix.Tool`, an aiXplain API key, Studio, the marketplace, or asks to build/run/deploy an agent, transcribe audio, run a model, set up RAG, or wire an integration on aiXplain — even when they don't name every component explicitly.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Builder

Design, run, and deploy everything the aiXplain SDK supports: agents and team agents, direct model inference, knowledge bases / RAG, tools and integrations, runtime governance, memory, and the access APIs. This skill is the single source of truth — every snippet here is verified against **aiXplain SDK v0.2.44** (the unified v2 `Aixplain` client) and live SDK introspection.

## Audience & self-containment

Used on behalf of **both non-developers and developers**. So:

- **Do the technical work yourself.** Write and run the code; don't hand the user a traceback. Diagnose it, fix it, and report in plain language: what happened, what you did, what's next.
- **This skill is authoritative.** Use its snippets as written; don't redirect the user to GitHub or the SDK source. If a snippet here fails against the installed SDK, the skill is wrong, not the user — fix it, then consider the "Report aiXplain issues" habit below.
- **Lead with the result and the Studio link**, not the implementation. Keep full code available for developers who want it.

## Setup

Install/upgrade first, then initialize the client:

```bash
python3 -m pip install --upgrade aixplain
```

```python
import os
from aixplain import Aixplain

aix = Aixplain(api_key=os.environ["AIXPLAIN_API_KEY"])   # or Aixplain() if AIXPLAIN_API_KEY / TEAM_API_KEY is exported
```

If `AIXPLAIN_API_KEY` isn't set, ask the user for it (or to add it to a `.env`) — get one at https://console.aixplain.com/settings/keys. Most operations spend credits (1 credit = $1); say so before running anything billable for a non-developer.

## Pick the right tool for the job

| The user wants to… | Build a… | Reference |
|---|---|---|
| Reason over a goal, call tools, multi-step work | **Agent** | `references/agents.md` |
| Coordinate several specialists / a workflow | **Team agent** | `references/agents.md` |
| Just run a model once (LLM, transcription, translation, vision) | **Direct model call** | `references/models.md` |
| Answer from private documents | **Knowledge base + agent (RAG)** | `references/knowledge-memory.md` |
| Connect Slack/Gmail/DB/MCP, or wrap a Python function | **Tool / integration** | `references/tools-integrations.md` |
| Enforce a policy at runtime (safety, PII, format) | **Inspector** | `references/governance.md` |
| Remember across turns / sessions / agents | **Session or shared memory** | `references/knowledge-memory.md` |
| Call a deployed asset over HTTP/JS/OpenAI client | **REST / access API** | `references/deployment-access.md` |
| Update, or export-as-code, an existing/deployed agent | **agent lifecycle** | `references/agents.md` |
| A ready-made recipe to adapt | — | `references/patterns.md` |

Read the relevant reference file before writing code for that domain — they hold the exact signatures, IDs, and gotchas.

> **Not in the v2 SDK:** pipelines, fine-tuning, benchmarking, and datasets/corpora. These are legacy-v1 only or Studio-only. See `references/deployment-access.md § What the v2 SDK does NOT cover`. For multi-step workflows in v2, use a **team agent**.

## Workflow for building an agent

1. **Plan, then confirm.** State the agent's name, description, instructions, which tools/integrations, and single vs. team. Wait for approval before building anything billable.
2. **Search before hardcoding.** `aix.Tool.search(...)`, `aix.Model.search(...)`, `aix.Integration.search()["results"]`. Never say "not available" without searching. IDs in the reference tables can drift — if one 404s, search by name.
3. **Create tools and scope them.** For every tool, narrow `allowed_actions` to the minimum the task needs — the default (all actions) over-privileges the agent and hurts its reasoning. See `references/tools-integrations.md`.
4. **Build the agent.** Omit `llm` unless the user asks for a specific model (the platform default is good). Set `output_format` and, for JSON, `expected_output`.
5. **Save = deploy.** `agent.save()` (or `team.save(save_subcomponents=True)`) promotes `DRAFT → ONBOARDED` and gives a persistent endpoint. There is no separate `deploy()`.
6. **Run and verify.** `agent.run(query=...)`, read `.data.output`. Inspect `.data.steps` if it misbehaves.
7. **Share Studio links** so the user can edit/monitor visually:
   - Builder/traces: `https://studio.aixplain.com/build/<AGENT_ID>/schema`
   - Analytics: `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

## Conventions that apply everywhere

- **Resilient runs:** sync via `.run(...)`; async via `.run_async(...)` then `.sync_poll(url)` (blocks, returns the same shape) or manual `.poll(url)` until `.completed`.
- **Reading results:** agents → `response.data.output`, `.status`, `.data.steps`, `.data.execution_stats`; models → `response.data`, `.status`, `.usage`, `._raw_data`.
- **Unique names:** if `save()` raises `name_already_exists`, ask the user: update the existing asset or create under a new name. Appending `int(time.time())` to a name keeps demos unique.
- **Don't invent credentials or IDs.** Ask the user for required inputs (DB URLs, API tokens). Use placeholders only when clearly labeled.

## Passing local files to aiXplain

Models/agents/tools take **URLs**, not local paths. Upload first and pass the returned URL:

```python
from aixplain.v2.file import FileUploader
url = FileUploader(api_key=os.environ["AIXPLAIN_API_KEY"]).upload(
    "/path/to/file.mp3", is_temp=True, return_download_link=True)   # download link, not raw s3://
```

Use `return_download_link=True` so the URL is browser-accessible. Size limits: audio 50 MB, image/documents 25 MB, video/database 300 MB. (For `.html`/`.zip` outputs the SDK's MIME detector can mislabel the extension — set the right content type when it matters.)

## Report aiXplain issues (habit)

When you hit a quirk that is clearly **aiXplain-caused** (not the user's code/config) — an advertised action that always fails, a documented parameter the backend ignores, a connector requesting too few scopes — offer to file an issue at https://github.com/aixplain/aiXplain. Reproduce it first to confirm the cause is on aiXplain's side, draft the title/body, and **get the user's approval before posting** (the repo is public). Redact API keys, emails, and asset/account IDs; keep the repro generic. Include SDK version, asset type, a minimal repro, and expected vs. actual behavior.

## External links

- Docs: https://docs.aixplain.com · Studio: https://studio.aixplain.com · Console (keys/billing): https://console.aixplain.com · Pricing: https://aixplain.com/pricing
