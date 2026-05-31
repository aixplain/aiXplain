<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/aixplain-logo-light.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/aixplain-logo-dark.png">
    <img src="docs/assets/aixplain-logo-dark.png" alt="aixplain" width="520">
  </picture>
</p>

<h1 align="center">aixplain SDK</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-2ea44f?style=flat-square" alt="License"></a>
  <a href="https://studio.aixplain.com/browse"><img src="https://img.shields.io/badge/Marketplace-900%2B%20models%20%26%20tools-0b74de?style=flat-square" alt="Marketplace size"></a>
  <a href="https://console.aixplain.com/settings/keys"><img src="https://img.shields.io/badge/%F0%9F%94%91%20PAYG%20API%20key-Settings-0b74de?style=flat-square" alt="PAYG API key"></a>
  <a href="https://discord.gg/aixplain"><img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**The operating system for autonomous AI — multi-agent orchestration and runtime governance across cloud, on-prem, edge, and fully air-gapped environments.**

aixplain is the operations layer over your AI stack, spanning **development → evaluation → deployment → monitoring → evolution** — so you ship faster instead of stitching tools together. The SDK gives you Python and REST access to that runtime: agents that plan, call models and tools, run code, and adapt at runtime, with governance enforced on every execution.

Develop your way — **SDK, API, CLI, and MCP** environments all run on the same runtime layer, backed by an ecosystem of models, tools, and services: an integrated marketplace of **900+ AI models, tools, and integrations from 70+ vendors**.

**One API key. One bill.** Pay as you go across every provider and tool — OpenAI, Anthropic, Gemini, Firecrawl, Tavily, SerpAPI, RAG data ingestion, and a sandbox for code execution — with no per-vendor keys or contracts.

Build the full range on one runtime — **multi-step agents**, **managed agents**, and **deployed agents**.

## Why aixplain

- **Ship faster** — one runtime spans the full lifecycle (build, evaluate, deploy, monitor, evolve); no glue code to assemble.
- **Multi-agent orchestration** — delegate work to specialized subagents that plan, reflect, and adapt at runtime.
- **Runtime governance by default** — allow-list assets and per-asset actions, set rate and usage limits, enforce enterprise RBAC, and block pip installs or network access mid-execution.
- **One key, one bill** — [900+ models, tools, and integrations](#mcp-server-marketplace) from 70+ vendors, billed in one place.
- **Production observability** — step-level traces, tool calls, and outcomes for fast debugging.
- **Develop your way** — SDK, API, CLI, and MCP clients on the same runtime layer.
- **Deploy anywhere** — the same agent definition runs serverless, on-prem, at the edge, or fully air-gapped.

| | aixplain SDK | Other agent frameworks |
|---|---|---|
| Governance | Asset/action allow-lists, per-asset permissions, rate and usage limits, and enterprise RBAC | Usually custom code or external guardrails |
| Models and tools | 900+ models and tools with one API key | Provider-by-provider setup |
| Deployment | Cloud (instant) or on-prem | Usually self-assembled runtime and infra |
| Observability | Built-in traces and dashboards | Varies by framework |
| [Coding-agent workflows](TODO-agent-builder-skill-url) | Works natively with MCP-compatible coding agents and IDEs | Usually not a first-class workflow target |

## Agentic OS

Agentic OS is the portable runtime platform behind aixplain agents:

- **Agent Engine** — orchestrates planning, execution, and delegation for autonomous agents.
- **Asset Serving** — standardizes every model, tool, and data source behind a uniform interface, enabling swappability, governance, identity and auth, and rich telemetry.
- **Observability** — captures traces, metrics, and monitoring for every production run.

It runs across Cloud (instant) and on-prem deployments.

---

## MCP Server Marketplace

[aixplain Marketplace](https://studio.aixplain.com/browse) now also exposes MCP servers for **900+ models and tools**, allowing external clients to access selected **tool, integration, and model assets**, for example **Opus 4.6, Kimi, Qwen, Airtable, and Slack**, through **aixplain-hosted MCP endpoints** with a single API key 🔑.

Read the full MCP setup guide in the [MCP servers docs](https://docs.aixplain.com/api-reference/mcp-servers).

```json
{
  "ms1": {
    "url": "https://models-mcp.aixplain.com/mcp/<AIXPLAIN_ASSET_ID>",
    "headers": {
      "Authorization": "Bearer <AIXPLAIN_APIKEY>",
      "Accept": "application/json, text/event-stream"
    }
  }
}
```

---

## Quick start

> **This is the aixplain SDK 2.** SDK 1 (the legacy factory API) keeps running until **end of July 2026**; after that, SDK 2 is the only supported surface. <!-- TODO: confirm SDK 2 release version/date -->

```bash
pip install aixplain
```

Get your API key from your [aixplain account](https://console.aixplain.com/settings/keys), then expose it to the SDK:

```bash
export AIXPLAIN_API_KEY=<your-key>
```

### Create and run your first agent

```python
from uuid import uuid4
from aixplain import Aixplain

aix = Aixplain()  # reads AIXPLAIN_API_KEY from the environment

search_tool = aix.Tool.get("tavily/tavily-web-search/tavily")
search_tool.allowed_actions = ["search"]

agent = aix.Agent(
    name=f"Research agent {uuid4().hex[:8]}",
    description="Answers questions with concise web-grounded findings.",
    instructions="Use the search tool when needed and cite key findings.",
    tools=[search_tool],
)
agent.save()

result = agent.run(
    query="Who is the CEO of OpenAI? Answer in one sentence.",
)
print(result.data.output)
```

> Runs return typed objects — read outputs with `result.data.output`, not dict indexing.

### Build a multi-agent team

```python
from uuid import uuid4
from aixplain import Aixplain
from aixplain.v2 import EditorConfig, EvaluatorConfig, EvaluatorType, Inspector, InspectorAction, InspectorActionConfig, InspectorSeverity, InspectorTarget

aix = Aixplain()  # reads AIXPLAIN_API_KEY from the environment
search_tool = aix.Tool.get("tavily/tavily-web-search/tavily")
search_tool.allowed_actions = ["search"]

def never_edit(text: str) -> bool:
    return False

def passthrough(text: str) -> str:
    return text

noop_inspector = Inspector(
    name=f"noop-output-inspector-{uuid4().hex[:8]}",
    severity=InspectorSeverity.LOW,
    targets=[InspectorTarget.OUTPUT],
    action=InspectorActionConfig(type=InspectorAction.EDIT),
    evaluator=EvaluatorConfig(
        type=EvaluatorType.FUNCTION,
        function=never_edit,
    ),
    editor=EditorConfig(
        type=EvaluatorType.FUNCTION,
        function=passthrough,
    ),
)

researcher = aix.Agent(
    name=f"Researcher {uuid4().hex[:8]}",
    instructions="Find and summarize reliable sources.",
    tools=[search_tool],
)

team_agent = aix.Agent(
    name=f"Research team {uuid4().hex[:8]}",
    instructions="Research the topic and return exactly 5 concise bullet points.",
    subagents=[researcher],
    inspectors=[noop_inspector],
)
team_agent.save(save_subcomponents=True)

response = team_agent.run(
    query="Compare OpenAI and Anthropic in exactly 5 concise bullet points.",
)
print(response.data.output)
```

<div align="center">
  <img src="docs/assets/aixplain-workflow-teamagent.png" alt="aixplain team-agent runtime flow" title="aixplain" width="70%"/>
</div>

Execution order:

```text
Human prompt: "Compare OpenAI and Anthropic in exactly 5 concise bullet points."

Team agent
├── Planner: breaks the goal into research and synthesis steps
├── Orchestrator: routes work to the right subagent
├── Researcher subagent
│   └── Tavily search tool: finds and summarizes reliable sources
├── Inspector: checks the final output through a simple runtime policy
├── Orchestrator: decides whether another pass is needed
└── Responder: returns one final answer
```

> **SDK 1 (legacy):** available until end of July 2026 — see the [SDK 1 docs](https://docs.aixplain.com/1.0/).

---

## Core concepts

| Concept | What it is |
|---|---|
| **Agent** | An autonomous entity that reasons, plans, and uses tools to complete a task. |
| **Team agent** | Multiple specialized agents coordinated by a planner and orchestrator at runtime. |
| **Tool** | A capability an agent can invoke — a model, an integration, or code (Python/SQL). |
| **Model** | An LLM, utility, or index asset from the [marketplace](https://studio.aixplain.com/browse). |
| **Integration** | A connector to an external service (Slack, Airtable, Gmail, and more) that an agent can act through. |
| **Micro-agents** | Built-in governance components that run inline on every execution: Mentalist (planning), Orchestrator (routing), Inspector (validation — e.g. block pip installs or network access), Bodyguard (security), Responder (formatting). |
| **Meta-agent** | An agent that improves other agents — the Evolver monitors KPIs and refines behavior over time. |

See the [documentation](https://docs.aixplain.com) for the full API reference.

---

## Data handling and deployment

aixplain applies runtime governance and enterprise controls by default:

- **We do not train on your data** — your data is not used to train foundation models.
- **No data retained by default** — agent memory is opt-in (short-term and long-term).
- **SOC 2 Type II certified** — enterprise security and compliance posture.
- **Runtime policy enforcement** — Inspector and Bodyguard govern every agent execution (e.g. block pip installs or network access during code runs).
- **Granular access controls** — allow-lists for assets and actions, per-asset permissions, rate and usage limits, and RBAC for enterprise.
- **Portable deployment options** — Cloud (instant) or on-prem (including VPC and air-gapped environments).
- **Encryption** — TLS 1.2+ in transit and encrypted storage at rest.

Learn more at aixplain [Security](https://aixplain.com/security/) and aixplain [pricing](https://aixplain.com/pricing/).

---

## Pricing

Start free, then scale with usage-based pricing.

- **Pay as you go** — prepaid usage with no surprise overage bills.
- **Subscription plans** — reduce effective consumption-based rates.
- **Custom enterprise pricing** — available for advanced scale and deployment needs.

Learn more at aixplain [pricing](https://aixplain.com/pricing/).

---

## Community & support

- **Documentation:** [docs.aixplain.com](https://docs.aixplain.com)
- **Example agents**: [https://github.com/aixplain/cookbook](https://github.com/aixplain/cookbook)
- **Learn how to build agents**: [https://academy.aixplain.com/student-registration/](https://academy.aixplain.com/student-registration/)
- **Meet us in Discord:** [discord.gg/aixplain](https://discord.gg/aixplain)
- **Talk with our team:** [care@aixplain.com](mailto:care@aixplain.com)

---

## License

This project is licensed under the Apache License 2.0. See the [`LICENSE`](LICENSE) file for details.
