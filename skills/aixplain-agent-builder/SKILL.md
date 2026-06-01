---
name: aixplain-agent-builder
description: A skill to design, deploy, and run production-grade AI agents on aiXplain.
metadata: {"requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3", "pip"]}}
---

# aiXplain Agent Builder

Design, deploy, run, and manage aiXplain agents — single agents, team agents, tools, and OAuth integrations.

> **Last updated:** 2026-05-31 · **Verified against aiXplain SDK:** v0.2.44 (inspector API verified live)

## Audience & Self-Containment

This skill is used on behalf of **both non-developers and developers**. They will not read the SDK source, API reference, or GitHub. Therefore:

- **This skill is the single source of truth.** Every code block here is verified against the SDK version above — use it as written. Do not tell the user to consult the SDK docs, GitHub, or source code.
- **Do the technical work yourself.** Write and run the code; the user should not have to. Never hand a non-developer a traceback — diagnose it, fix it, and report the outcome in plain language (what happened, what you did, what's next).
- **Explain in plain terms for non-developers**, but keep full code available for developers who want it. Lead with the result and the Studio link, not the implementation.
- **If a snippet here ever fails against the installed SDK, the skill is wrong, not the user.** Fix the skill in place, then follow the "Report aiXplain-Caused Issues" habit (see Debugging) — never redirect the user to external docs to work around it.

## How It Works

This skill accepts the following commands:

- **Build agent** — plan, search tools, create tools, assemble and save the agent
- **Deploy agent** — save and share Studio links for visual editing and analytics
- **Run agent** — execute sync or async and return the output
- **Debug agent** — diagnose tool, action, OAuth, or runtime issues
- **Export agent** — generate a standalone Python script from a deployed agent

## 1. Setup

Always install/upgrade to the latest SDK before doing anything: `pip install --upgrade aixplain`.

This skill is verified against **SDK v0.2.44**. If the installed version differs, tell the user.

```python
import os
from dotenv import load_dotenv
from aixplain import Aixplain

load_dotenv()  # loads AIXPLAIN_API_KEY from .env if present

api_key = os.getenv("AIXPLAIN_API_KEY")
if not api_key:
    raise ValueError("AIXPLAIN_API_KEY not set. Add it to your .env file or environment.")

aix = Aixplain(api_key=api_key)
```

> **Passing local files to agents or aiXplain assets:** Use `FileUploader` to upload a file to aiXplain S3 and get a presigned URL. Pass that URL anywhere a URL input is accepted (tools, models, integrations). `Resource.save()` is internal and not usable standalone.
> ```python
> from aixplain.v2.upload_utils import FileUploader
> uploader = FileUploader(api_key=api_key)
> file_url = uploader.upload("/path/to/file.mp3", is_temp=True, return_download_link=True)
> ```
>
> **Downloadable links:** If the agent needs to return files the user can click and download, always set `return_download_link=True`. Without it, `upload()` returns a raw `s3://` path that is not browser-accessible.
>
> **MIME type patch for `.html` and `.zip`:** The SDK's `MimeTypeDetector` does not include these extensions — both fall back to `text/csv`, causing browsers to save files with the wrong extension. Always patch before uploading when generating these file types:
> ```python
> from aixplain.v2.upload_utils import MimeTypeDetector
> MimeTypeDetector.EXTENSION_MAPPING['.html'] = 'text/html'
> MimeTypeDetector.EXTENSION_MAPPING['.zip']  = 'application/zip'
> ```

## 2. Plan

Before building, present a plan to the user covering: agent name, description, instructions, which tools/integrations to use, and whether it's a single or team agent. Wait for approval before proceeding.

**Always search before creating or hardcoding a tool or integration.** `Tool`, `Model`, and `Integration` all support `.search(query=...).results`. Never say "not available" without searching first.

```python
results = aix.Tool.search(query="web search").results
# Names may be concatenated (e.g. "Googledrive"). Normalize before comparing.
```

If a needed capability has no marketplace tool or integration, announce you'll build it as a **Python Sandbox** function (see `references/integration-playbooks.md § 4`).

## 3. Create Tools

**MANDATORY: Scope `allowed_actions` on every tool.** Never attach a tool to an agent without first narrowing its actions to the minimum needed for the task. Tools loaded via `Tool.get()` come with all actions enabled by default — this is over-privileged and degrades agent reasoning. Inspect `tool.actions` to see the full set, then assign `tool.allowed_actions = [...]` (or pass `allowed_actions=[...]` in the constructor) before adding to the agent. If you genuinely need all actions, state that explicitly to the user and confirm.

```python
tool = aix.Tool.get("<ID>")
print(tool.actions)              # discover available actions
tool.allowed_actions = ["search_models", "list_filters"]  # scope to task
```

Three paths, in order of preference:

```python
# Path A: Marketplace tool by ID — REMEMBER to scope allowed_actions after .get()
tool = aix.Tool.get("698cda188bbb345db14ac13b")  # Code Execution
tool.allowed_actions = [...]  # required

# Path B: Non-OAuth integration (KB, SQLite)
# READ references/integration-playbooks.md for config payloads.
# Ask the user for any missing inputs — never invent placeholders.
# Always create fresh; do not reuse by name unless explicitly asked.
tool = aix.Tool(name="KB Search", description="Search product docs",
    integration="6904bcf672a6e36b68bb72fb", allowed_actions=["search", "get"]).save()

# Path C: OAuth integration (Gmail, Slack, Jira, Google Drive)
# READ references/integration-playbooks.md § 5 for full workflow.
# (1) integration = aix.Integration.get("<ID>")
# (2) integration.list_actions() → discover action names
# (3) Create tool with allowed_actions in constructor
# (4) User completes OAuth via redirect URL emitted at .save()
# (5) Attach in-memory tool object to agent and save

# Path D: Python Sandbox (last resort)
# READ references/integration-playbooks.md § 4 for config shape.
```

## 4. Build Agent

Agents use the platform default LLM — do not specify `llm` unless the user requests a specific model.

```python
agent = aix.Agent(
    name="My Agent", description="...", instructions="...",
    tools=[tool], output_format="markdown",
    max_tokens=6000,  # set at creation, not per-run
).save()
```

If `save()` raises `name_already_exists`, ask the user: update existing or create with a new name.

## 5. Deploy & Run

After deploy, share these links with the user:
- **Visual builder:** `https://studio.aixplain.com/build/<AGENT_ID>/schema`
- **Analytics:** `https://studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`

Default: leave `runResponseGeneration` unset. Only pass `runResponseGeneration=True` when you specifically need structured/JSON output.

```python
# Sync — default text output
result = agent.run(query="...")
print(result.data.output)

# Sync — structured/JSON output
result = agent.run(query="...", runResponseGeneration=True)

# Async — SDK handles polling; no manual HTTP needed
ar = agent.run_async(query="...")
result = agent.sync_poll(ar.url)   # blocks until SUCCESS/FAILED, returns the same result shape as run()
print(result.data.output)
```

## 6. Debugging

### Inspect Intermediate Steps

```python
result = agent.run(query="...")

# Step-by-step trace: thought, action, tool used, input/output, tokens
for step in result.data.steps:
    print(step['thought'], step['action'], step['unit']['name'])

# Aggregate costs and timing
stats = result.data.execution_stats
print(stats['credits'], stats['runtime'], stats['api_calls'])
```

Or view traces visually in Studio: `https://studio.aixplain.com/build/<AGENT_ID>/schema`

### Report aiXplain-Caused Issues

When you hit a quirk or error that is **aiXplain-caused** — not a mistake in the user's code, query, or config — make it a habit to propose filing a GitHub issue at https://github.com/aixplain/aiXplain. Examples: an action advertised by an integration that always fails, an SDK method that misbehaves, a documented parameter the backend ignores, a connector requesting insufficient OAuth scopes.

Workflow:
1. Confirm the cause is on aiXplain's side (reproduce it; rule out user input, missing scopes the user controls, rate limits, etc.).
2. Propose the issue to the user with a draft title and body. Do not post without confirmation — the repo is public.
3. **Redact personal data** from the public issue: no API keys, real email addresses, tool/agent IDs, message counts, or any account-specific data. Keep repro steps generic.
4. On approval, post with `gh issue create --repo aixplain/aiXplain` and share the issue link.

Issue body should include: SDK version, integration/asset type, a minimal repro, the exact error, and expected vs. actual behavior.

## Quick Asset IDs

| Type | Name | ID |
|------|------|----|
| Tool | Tavily Web Search | `6931bdf462eb386b7158def3` |
| Tool | Code Execution | `698cda188bbb345db14ac13b` |
| Tool | Google Search API | `692f18557b2cc45d29150cb0` |
| Tool | Firecrawl API | `69442021f2e6cb73e286ff0f` |
| Tool | Docling Document Parser | `6944350ff2e6cb73e286ff20` |
| Integration | Gmail | `6864328d1223092cb4294d30` |
| Integration | Slack | `686432941223092cb4294d3f` |
| Integration | Google Drive | `6864329b1223092cb4294d4e` |
| Integration | Google Sheets | `686432931223092cb4294d3c` |
| Integration | Google Docs | `6864329c1223092cb4294d51` |
| Integration | Google Calendar | `686432901223092cb4294d36` |
| Integration | aiR Knowledge Base | `6904bcf672a6e36b68bb72fb` |
| Integration | PostgreSQL | `693ac6e8217c7b13b480970f` |
| Integration | SQLite | `689e06ed3ce71f58d73cc999` |
| Integration | Python Sandbox | `688779d8bfb8e46c273982ca` |

## Reference Files

- `references/integration-playbooks.md` — config payloads, file upload, authoring constraints, and OAuth workflow for all integration types
- `references/agent-patterns.md` — team agents, updating deployed agents, inspectors, export to Python, Code Execution vs Python Sandbox
- `references/inspectors.md` — inspector policies, action values, and post-change validation

## External Links

- **Docs:** https://docs.aixplain.com
- **Pricing:** https://aixplain.com/pricing
- **Studio:** https://studio.aixplain.com
