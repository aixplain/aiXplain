# aiXplain Skills

A collection of portable skills you can drop into any skill-compatible AI coding agent (Claude Code, Cursor, etc.) to work with aiXplain.

## Available skills

| Skill | Description |
| --- | --- |
| [`aixplain-agent-builder/`](./aixplain-agent-builder) | Build, run, debug, and deploy aiXplain agents using plain English |

---

## aiXplain Agent Builder Skill

Build, run, debug, and deploy aiXplain agents using plain English — no IDE, no boilerplate, no guesswork.

Drop this skill into any skill-compatible AI coding agent and start describing what you want. The agent handles the architecture, writes the code, deploys to aiXplain, runs a smoke test, and hands you a working agent ID.

> **SDK version:** `aixplain==0.2.44`

### Why aiXplain Agent Builder

1. **Natural language, no code.** Describe it → plan → approve → build → test.
2. **Deploy instantly, free.** No infra bill — pay only for runtime usage.
3. **Agents live on a platform.** Edit, trace, monitor, and version in aiXplain Studio.
4. **One marketplace, one key.** Models, tools, integrations, and MCPs behind a single API key.
5. **Never blocked by missing tools.** Falls back to Python Sandbox and wires it in automatically.
6. **Best practices baked in.** Strong instructions, scoped actions, smart iteration limits, speed/quality tuning.
7. **Safe key handling.** Auto-discovered from env, never hardcoded into generated files.
8. **Portable skill.** Runs in any skill-compatible agent — Claude Code, Cursor, and more.

### Who it's for

Built for **non-technical builders**, **developers**, **power users**, and **AI teams** who want working agents without boilerplate.

### Quick start

1. Grab an [aiXplain API key](https://studio.aixplain.com/settings/keys).
2. Clone [`aixplain-agent-builder/`](./aixplain-agent-builder) into your AI coding agent (Claude Code, Cursor, etc.).
3. Describe the agent — e.g. *"Build an agent that searches the web for competitor pricing and drafts a summary report."*
4. Review the pre-build plan → **approve**.
5. Get back a deployed agent ID and two Studio links: [visual builder & traces](https://studio.aixplain.com/build/) and [analytics dashboard](https://studio.aixplain.com/dashboard/analytics/).

That's it — no pip installs, no config files, no environment setup.

#### How it works under the hood

- **Plan contents.** The pre-build plan shows the proposed architecture, tools to connect, output format, and any OAuth links you'll need to authorize.
- **Reuses existing agents.** Matches by name and updates in place instead of creating silent duplicates.
- **Two Studio links, always.** `studio.aixplain.com/build/<AGENT_ID>/schema` for the visual editor and step traces; `studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>` for runs, latency, tokens, and errors.
- **Key discovery order.** `~/.env` → repo `.env` → environment variables → prompts you.

### What you can build

| Mode | What you say | What the skill does |
| --- | --- | --- |
| **Build — Web research** | *"Build an agent that searches the web and summarizes competitor pricing into a markdown report"* | Drafts a plan with the right tools, output format, and guardrails |
| **Build — Support triage** | *"Create a support agent that searches our KB, checks Jira ticket history, and classifies by severity"* | Finds the integrations, proposes the architecture, waits for approval |
| **Build — Data analyst** | *"Build an agent that runs Python on uploaded CSVs and produces charts"* | Picks models + tools, writes missing logic as a Python Sandbox function |
| **Build — Email assistant** | *"Make an agent that reads my Gmail inbox on demand, groups by topic, and drafts replies"* | Wires OAuth, scopes Gmail actions, runs a smoke test |
| **Build — Real estate** | *"Make a real-estate evaluator that looks up location data and computes cap rate"* | Combines marketplace tools with custom Python for the math |
| **Run** | *"Run agent 69ce064f44eef3c9e3850d95 with: Austin TX, 450k asking price"* | Executes, inspects the step trace, and explains the result |
| **Debug** | *"Why isn't the agent using the knowledge base?"* | Inspects recent runs, diagnoses tool selection, suggests fixes |
| **Export** | *"Export agent 69abc… back to Python"* | Reverse-engineers a deployed agent into runnable SDK code |

### Integrations supported

The skill has access to 600+ integrations including:

- **Productivity:** Gmail, Google Drive, Google Sheets, Notion, Confluence
- **Dev & project:** GitHub, Jira, Linear
- **CRM & sales:** HubSpot, Salesforce
- **Communication:** Slack
- **Data:** PostgreSQL, SQLite, aiR Knowledge Base
- **Compute:** Python Sandbox, Code Execution
- **Web:** Tavily, Firecrawl, Google Search, Google Places
- **Universal:** MCP Server and similar extensible connectors

### File structure

```text
aixplain-agent-builder/
├── SKILL.md                      # Core skill — loaded automatically
├── README.md                     # Quick overview of the skill
└── references/
    ├── asset-ids.md              # Curated model, tool, and integration IDs
    ├── integration-playbooks.md  # Connection patterns per integration
    └── inspector-analytics.md    # Governance policies and inspector patterns
```

Reference files are loaded on demand — only when the task requires them. This keeps context lean and responses fast.
