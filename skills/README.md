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

### Who it's for

| Persona | What they get |
| --- | --- |
| **Non-technical builders** | Zero-code agent creation — just describe what you want |
| **Developers** | Production-ready Python, SDK patterns, OAuth wiring, error handling |
| **Power users** | Export any deployed agent back to Python, reverse-engineer team architectures, add inspectors and governance |
| **AI teams** | Safe API key handling, pre-build approval gates, no silent duplicates |

### Quick start

1. [Get an aiXplain API key](https://studio.aixplain.com/settings/keys) — one pay-as-you-go, pre-paid key unlocks every model, tool, and integration on the aiXplain marketplace. No per-provider billing, no separate vendor accounts.
2. Download or clone the [`aixplain-agent-builder/`](./aixplain-agent-builder) folder and add it to your AI coding agent (Claude Code, Cursor, etc.) as a skill.
3. Ask it to build something — for example: *"Build an agent that monitors competitor pricing and emails me a weekly summary."*
4. The skill searches the aiXplain marketplace for the right models, tools, and integrations, then hands you a **pre-build plan**: proposed architecture, tools to connect, output format, and any OAuth links you'll need to authorize.
5. **Approve the plan** (or tweak it) — the skill then creates the agent, wires up the tools, runs a smoke test, and gives you back a deployed agent ID.
6. The skill returns two aiXplain Studio links for the deployed agent:
   - **Visual builder & traces** (`studio.aixplain.com/build/<AGENT_ID>/schema`) — edit the agent graph, tools, and instructions, and inspect step-by-step run traces.
   - **Analytics dashboard** (`studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>`) — monitor runs, latency, token usage, and errors over time.

> **Note:** If a required tool or integration isn't in the marketplace, the skill falls back to **Python Sandbox** — it writes a Python function for the missing capability, deploys it as a sandboxed tool, and attaches it to the agent automatically. No manual glue code required.

No pip installs, no config files, no environment setup — the skill auto-discovers your API key and walks you through anything it can't find.

### What you can build

**Build**

Describe the agent in plain English. The skill drafts the plan, tools, output format, and guardrails before it builds.

```text
"Build an agent that searches the web, finds competitor pricing, and emails me a summary"
"Create a support triage agent connected to our knowledge base and Jira"
"Make a real estate evaluator that looks up location data and computes cap rate"
```

**Run / Debug**

Give it an agent ID or name. The skill runs it, inspects the steps, and diagnoses failures.

```text
"Run agent 69ce064f44eef3c9e3850d95 with this query: Austin TX, 450k asking price"
"Debug why the agent isn't using the knowledge base"
"Inspect the execution steps from the last run"
```

**Deploy**

Once approved, the skill creates or updates the agent, connects the right tools, runs a smoke test, and leaves you with a working asset.

```text
"Deploy this customer support agent to aiXplain and test it with a ticket triage prompt"
"Build this real-estate evaluator and deploy it to my workspace"
"Create the team agent, connect the tools, and validate the first run"
```

### What the skill does for you

- Shows a pre-build plan before creating anything
- Finds API keys from `~/.env`, repo `.env`, or environment variables
- Reuses existing agents instead of creating duplicates
- Surfaces OAuth connection links when integrations need them
- Runs a smoke test and checks for grounded output

```text
~/.env → repo .env → environment variables → asks you
```

Keys are set as environment variables, never hardcoded into generated files.

### Best practices baked in

- Uses a strong instruction format: `ROLE`, `CONSTRAINTS`, and `OUTPUT RULES`
- Keeps tool descriptions short and action-oriented for better selection
- Picks practical iteration limits for lookup vs. deep research tasks
- Scopes tool actions to the minimum required set
- Chooses speed vs. quality settings based on the use case

```text
runResponseGeneration=False + output_format="text"     ->  ~30-40% faster
runResponseGeneration=True  + output_format="markdown" ->  richest output
```

### Sample queries to try

- **Web research agent** — *"Build an agent that searches the web and summarizes findings into a markdown report"*
- **Support triage** — *"Create a support agent that searches our KB, checks ticket history in Jira, and classifies by severity"*
- **Data analyst** — *"Build an agent that runs Python on uploaded CSVs and produces charts"*
- **Email assistant** — *"Make an agent that reads my Gmail, groups by topic, and drafts replies"*
- **Deploy** — *"Build this agent, deploy it to my workspace, and validate the first run"*
- **Debug** — *"Why did agent 69abc… return a hallucinated answer instead of using the KB?"*
- **Knowledge base** — *"Create an agent connected to our product docs KB that answers support questions"*

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
