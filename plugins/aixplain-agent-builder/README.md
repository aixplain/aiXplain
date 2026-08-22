# aixplain Agent Builder plugin

Build, connect, deploy, verify, debug, update, and export production aixplain agents from a plain-language goal using the Python SDK v2.

## Install

```text
/plugin marketplace add aixplain/aiXplain
/plugin install aixplain-agent-builder@aixplain
```

## Requirements

- Python 3.10 or newer
- `aixplain==0.2.47`
- `AIXPLAIN_API_KEY` for the target workspace

Set the key in your environment or approved secret manager. Never paste it into source files, generated scripts, bug reports, or commits.

## What it does

- Converts intent into a single agent or a justified team.
- Searches existing marketplace tools and integrations before creating code.
- Applies least-privilege tool action scopes, budgets, and inspectors.
- Handles OAuth and provider credentials as explicit user checkpoints.
- Runs realistic verification and returns working agent links.
- Preserves raw backend tool scopes when updating agents affected by the SDK `0.2.47` hydration bug.
- Records reproducible SDK/runtime quirks in `skills/aixplain-agent-builder/references/BUGS.md`.

## Safety and cost

Saving and running agents can create workspace assets and consume aixplain credits. External integrations can read or write provider data. The skill asks before OAuth, credentials, consequential external actions, or irreversible operations.

## Validation

Validated on 2026-08-22 against public `aixplain==0.2.47`, the current `aixplain-agents` runtime source, authenticated marketplace searches, and live single-agent, team, tool-scope, inspector, execution-strategy, and Slack integration checks.

The runtime applies `llm` and `planner` model-parameter buckets. Although SDK `0.2.47` still accepts and persists `response_generator`, the dedicated responder pass is deprecated and ignored by the current runtime.
