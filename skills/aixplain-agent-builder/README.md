# aiXplain Agent Builder Skill

A Claude skill for building, deploying, running, debugging, and managing aiXplain v2 agents via the Python SDK and REST API. Verified against **aiXplain SDK v0.2.44**.

## What it covers

- Single and team agents with tools, integrations, and inspectors
- Sync and async agent runs (SDK + language-agnostic REST/cURL)
- In-place updates to deployed agents (instructions, tools, LLM, output format)
- Non-OAuth integrations: Knowledge Base, PostgreSQL, SQLite, Python Sandbox, MCP Server
- OAuth integrations: Gmail, Slack, Jira, Google Drive (REST-first workaround for broken SDK path)
- Inspector policies (ABORT / ADAPTIVE / RERUN) and analytics
- Exporting an existing agent to a reproducible Python script

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main entry point — load this first |
| `references/integration-playbooks.md` | **Required read** before wiring any non-OAuth integration. Exact `config={...}` shapes, file uploads, authoring constraints |
| `references/asset-ids.md` | Full model / integration / tool ID tables |
| `references/inspector-analytics.md` | Inspector policy matrix and analytics schema |

## Prerequisites

- `pip install --upgrade aixplain`
- `AIXPLAIN_API_KEY` (or `TEAM_API_KEY`) set in env

## Core principles

1. **Search before creating.** `Agent`, `Tool`, `Model`, and `Integration` all share `.search(query=...).results`. Run it before falling back to hardcoded IDs or declaring an asset missing.
2. **Mutate, don't recreate.** Deployed agents are mutable — load, edit, `save()`. Never recreate to change behavior.
3. **Ask for missing inputs.** For non-OAuth integrations (KB, DB, Python, MCP), always create fresh connected tools and ask the user for missing files / credentials rather than inventing placeholders.
4. **Consult the playbook.** `references/integration-playbooks.md` is the source of truth for `config` payloads and per-integration gotchas. `SKILL.md` only shows the KB shape.

## Known gotchas

- `Agent.search()` is eventually-consistent — fall back to `GET /sdk/agents` on `name_already_exists`.
- MCP Server and SQLite validate at **save-time**, not run-time.
- OAuth tools are at `/sdk/models/`, not `/sdk/tools/`, and the SDK Tool pipeline is broken for them — use REST.
- Python Sandbox: `bool` params are broken (JSON lowercase `true` → `NameError`); tuple returns round-trip as string reprs. Use `int` (0/1) and `dict`/`list` respectively.
