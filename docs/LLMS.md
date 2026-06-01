# LLM-Friendly Documentation (`llms.txt` / `llms-full.txt`)

This folder ships two machine-readable bundles of the aiXplain SDK v2 reference, following the [llmstxt.org](https://llmstxt.org) standard:

| File | What it is | When to use |
| --- | --- | --- |
| [`llms.txt`](./llms.txt) | Curated index — title + one-line summary for every SDK v2 module, plus pointers to the full bundle | LLMs and humans browsing for the right module |
| [`llms-full.txt`](./llms-full.txt) | Single concatenated dump of every SDK v2 reference page | Drop the whole SDK reference into one context window |

## Why these files matter

- **One-shot context for AI coding agents.** Claude Code, Cursor, Codex, Copilot Chat, and any MCP-compatible agent can `fetch` `llms-full.txt` once and answer SDK questions without crawling the docs site.
- **Deterministic code suggestions.** Agents stop hallucinating method signatures because the entire v2 surface area is in their context.
- **Faster onboarding for new engineers.** Paste `llms-full.txt` into any chat assistant and get accurate "how do I…" answers grounded in the latest SDK.
- **Standards-compliant.** Follows the [llmstxt.org](https://llmstxt.org) convention so external tools (Mintlify, Cursor, Continue, etc.) discover them automatically.
- **Cheap to keep fresh.** Generated from the source markdown — no manual maintenance.

## Regenerating

Run from the repo root:

```bash
python generate_llms_full.py
```

This rewrites both `docs/llms.txt` and `docs/llms-full.txt` from the SDK v2 sidebar (`docs/api-reference/python/api_sidebar.js`).

## Keeping them in sync (engineers)

Regenerate **every time you push SDK changes that touch `aixplain/v2/`** (new module, new method, signature change, docstring update). Two recommended ways:

### Option A — GitHub Actions (recommended)

Add this workflow at `.github/workflows/llms-docs.yml`:

```yaml
name: Refresh LLM docs

on:
  push:
    branches: [main]
    paths:
      - 'aixplain/v2/**'
      - 'docs/api-reference/python/**'
      - 'generate_llms_full.py'

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python generate_llms_full.py
      - name: Commit refreshed bundles
        run: |
          if [ -n "$(git status --porcelain docs/llms.txt docs/llms-full.txt)" ]; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add docs/llms.txt docs/llms-full.txt
            git commit -m "docs: refresh llms.txt and llms-full.txt"
            git push
          fi
```

### Option B — Pre-push git hook

Add to `.git/hooks/pre-push`:

```bash
#!/usr/bin/env bash
python generate_llms_full.py
git add docs/llms.txt docs/llms-full.txt
git diff --cached --quiet || git commit -m "docs: refresh llms.txt and llms-full.txt"
```

```bash
chmod +x .git/hooks/pre-push
```

## How LLMs discover them

Most agentic coding tools look for `/llms.txt` at the repo or domain root. Once these files land at `https://docs.aixplain.com/llms.txt` and `https://docs.aixplain.com/llms-full.txt`, no further configuration is needed — agents will auto-discover them.
