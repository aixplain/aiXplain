<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/aixplain-logo-light.svg">
    <source media="(prefers-color-scheme: light)" srcset="docs/assets/aixplain-logo-dark.svg">
    <img src="docs/assets/aixplain-logo-dark.svg" alt="aixplain" width="420">
  </picture>
</p>

<h1 align="center">aixplain SDK</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-2ea44f?style=flat-square" alt="License"></a>
  <a href="https://studio.aixplain.com/browse"><img src="https://img.shields.io/badge/Marketplace-900%2B%20models%20%26%20tools-0b74de?style=flat-square" alt="Marketplace size"></a>
  <a href="https://console.aixplain.com/settings/keys"><img src="https://img.shields.io/badge/%F0%9F%94%91%20PAYG%20API%20key-Settings-0b74de?style=flat-square" alt="PAYG API key"></a>
  <a href="https://discord.gg/aixplain"><img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**Build, deploy, and run autonomous AI agents — governed by default, in a few lines of Python.**

_The fastest way to ship managed, multi-agent systems with guardrails built in — on any infrastructure._

aixplain is the operating system for autonomous AI — **multi-agent orchestration and runtime governance across cloud, on-prem, edge, and fully air-gapped environments**. It spans the full lifecycle — **development → evaluation → deployment → monitoring → evolution** — so you ship faster instead of stitching tools together. Agents plan, call models and tools, run code, and adapt at runtime, with **agents-in-the-loop** governance enforced on every execution.

**Build any kind of agent on one runtime** — knowledge (RAG), data, custom-logic, integration, and team agents — with built-in memory, multimodality, and file handling.

Develop your way — **SDK, API, CLI, and MCP** environments all run on the same runtime layer, backed by an integrated marketplace of **900+ AI models, tools, and integrations from 70+ vendors** (OpenAI, Anthropic, Gemini, Firecrawl, Tavily, SerpAPI, a code-execution sandbox, and more). **One API key, one bill**, pay as you go — no per-vendor keys or contracts.

## Why aixplain

Less to build, less to operate:

- **Deploy with one call** — `agent.save()` promotes an agent to a persistent, versioned endpoint; no Dockerfiles, queues, or autoscaling to manage.
- **No integration glue** — reach [900+ models, tools, and integrations](#mcp-server-marketplace) through one key; skip per-provider SDKs, auth, and rate-limit handling.
- **Guardrails you don't have to build** — allow-lists, per-asset permissions, rate and usage limits, and access control enforced at runtime.
- **Self-debugging** — step-level traces of every plan, tool call, and outcome.
- **Run it anywhere** — the same definition runs serverless, on-prem, at the edge, or fully air-gapped.

| | aixplain SDK | Other agent frameworks |
|---|---|---|
| Guardrails & control | Asset/action allow-lists, per-asset permissions, rate and usage limits, and access control | Usually custom code or external guardrails |
| Models and tools | 900+ models and tools with one API key | Provider-by-provider setup |
| Deployment | Cloud (instant) or on-prem | Usually self-assembled runtime and infra |
| Observability | Built-in traces and dashboards | Varies by framework |
| [Coding-agent workflows](https://github.com/aixplain/aiXplain/tree/main/skills/aixplain-agent-builder) | Works natively with MCP-compatible coding agents and IDEs | Usually not a first-class workflow target |

## Agentic OS

Agentic OS is the portable runtime platform behind aixplain agents — orchestration, governed asset serving, and observability across Cloud (instant), on-prem, edge, and air-gapped deployments. See the [documentation](https://docs.aixplain.com) for the full architecture.

---

## Quick start

> **This README documents SDK v2, the default API.** SDK v1 (the legacy factory API) keeps working until **end of July 2026**, after which v2 is the only supported surface.

```bash
pip install aixplain
```

Get your API key from your [aixplain account](https://console.aixplain.com/settings/keys), then expose it to the SDK:

```bash
export AIXPLAIN_API_KEY=<your-key>
```

### Create and run your first agent

```python
from aixplain import Aixplain

aix = Aixplain()  # reads AIXPLAIN_API_KEY from the environment

search_tool = aix.Tool.get("tavily/tavily-web-search/tavily")
search_tool.allowed_actions = ["search"]

agent = aix.Agent(
    name="Research agent",
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
    name="noop-output-inspector",
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
    name="Researcher",
    instructions="Find and summarize reliable sources.",
    tools=[search_tool],
)

team_agent = aix.Agent(
    name="Research team",
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

Execution order:

```text
Human prompt: "Compare OpenAI and Anthropic in exactly 5 concise bullet points."

Team agent
├── Planner: breaks the goal into research and synthesis steps
├── Orchestrator: routes work to the right subagent
├── Researcher subagent
│   └── Tavily search tool: finds and summarizes reliable sources
├── Inspector: validates the output against a runtime policy
└── Orchestrator: composes and returns the final answer
```

> **SDK 1 (legacy):** available until end of July 2026 — see the [SDK 1 docs](https://docs.aixplain.com/1.0/).

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

## Core concepts

| Concept | What it is |
|---|---|
| **Agent** | An autonomous entity that reasons, plans, and uses tools to complete a task. |
| **Team agent** | Multiple specialized agents coordinated by a planner and orchestrator at runtime. |
| **Tool** | A capability an agent can invoke — a model, an integration, or code (Python/SQL). |
| **Model** | An LLM, utility, or index asset from the [marketplace](https://studio.aixplain.com/browse). |
| **Integration** | A connector to an external service (Slack, Airtable, Gmail, and more) that an agent can act through. |
| **Micro-agents** | Built-in agents that run inline on every execution: Planner (plans and decomposes the goal), Orchestrator (routes and coordinates), Inspector (validation — e.g. block pip installs or network access), and Bodyguard (access control and permissions at the asset boundary). |
| **Meta-agent** | An agent that improves other agents — the Evolver monitors production signals and refines behavior over time. |

See the [documentation](https://docs.aixplain.com) for the full API reference.

---

## Data handling and deployment

aixplain applies runtime governance and enterprise controls by default:

- **We do not train on your data** — your data is not used to train foundation models.
- **No data retained by default** — agent memory is opt-in (short-term and long-term).
- **SOC 2 Type II certified** — enterprise security and compliance posture.
- **Runtime policy enforcement** — Inspector and Bodyguard govern every agent execution, with allow-lists for assets and actions, per-asset permissions, rate and usage limits, and enterprise RBAC.
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
