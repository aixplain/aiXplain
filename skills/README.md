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

Built for **non-technical builders**, **developers**, **power users**, and **AI teams** who want working agents without boilerplate.

### Quick start

1. Grab an [aiXplain API key](https://studio.aixplain.com/settings/keys).
2. Clone [`aixplain-agent-builder/`](./aixplain-agent-builder) into your AI coding agent (Claude Code, Cursor, etc.).
3. Describe the agent — e.g. *"Build an agent that searches the web for competitor pricing and drafts a summary report."*
4. Review the pre-build plan → **approve**.
5. Get back a deployed agent ID and two Studio links: [visual builder & traces](https://studio.aixplain.com/build/) and [analytics dashboard](https://studio.aixplain.com/dashboard/analytics/).

That's it — no pip installs, no config files, no environment setup.

#### How it works under the hood

- **One key, every provider.** The aiXplain API key is pay-as-you-go and pre-paid — a single key unlocks every model, tool, and integration on the marketplace. No per-provider billing, no separate vendor accounts.
- **Plan before build.** The skill searches the marketplace for the right models, tools, and integrations, then shows a pre-build plan: proposed architecture, tools to connect, output format, and any OAuth links you'll need to authorize. Nothing is created until you approve.
- **Deploy + smoke test.** On approval it creates the agent, wires the tools, runs a smoke test, and hands back a working agent ID — reusing existing agents instead of creating silent duplicates.
- **Two Studio links, always.** `studio.aixplain.com/build/<AGENT_ID>/schema` to edit the graph, tools, instructions, and inspect step-by-step traces; `studio.aixplain.com/dashboard/analytics/?agent=<AGENT_ID>` to monitor runs, latency, token usage, and errors over time.
- **Missing integration? No problem.** If a required tool isn't in the marketplace, the skill falls back to **Python Sandbox** — it writes a Python function for the missing capability, deploys it as a sandboxed tool, and attaches it to the agent automatically.
- **Safe key handling.** Keys are auto-discovered from `~/.env` → repo `.env` → environment variables, and always set as env vars — never hardcoded into generated files.

### What you can build

| Mode | What you say | What the skill does |
| --- | --- | --- |
| **Build** | *"Build an agent that searches the web and summarizes competitor pricing into a markdown report"* | Drafts the plan, tools, output format, and guardrails before creating anything |
| **Build** | *"Create a support triage agent connected to our knowledge base and Jira"* | Finds the right integrations, proposes the architecture, waits for approval |
| **Build** | *"Make a real-estate evaluator that looks up location data and computes cap rate"* | Picks models + tools, writes any missing logic as a Python Sandbox function |
| **Run / Debug** | *"Run agent 69ce064f44eef3c9e3850d95 with query: Austin TX, 450k asking price"* | Executes, inspects the step trace, and explains the result |
| **Run / Debug** | *"Debug why the agent isn't using the knowledge base"* | Inspects recent runs, diagnoses tool selection, suggests fixes |
| **Deploy** | *"Deploy this customer support agent and test it with a ticket triage prompt"* | Creates/updates the agent, connects tools, runs a smoke test |
| **Export** | *"Export agent 69abc… back to Python"* | Reverse-engineers a deployed agent into runnable SDK code |

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
- **Email assistant** — *"Make an agent that reads my Gmail inbox on demand, groups by topic, and drafts replies"*
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
