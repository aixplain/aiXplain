# aiXplain Agents SDK

**Build and deploy autonomous AI agents on production-grade infrastructure, instantly.**

---

## aiXplain agents

aiXplain Agents SDK gives developers Python and REST APIs to build, run, and deploy autonomous multi-step agents on AgenticOS. Agents run as runtime systems, not fixed workflow graphs: on each run, they can break goals into steps, select tools dynamically, call models and data sources, execute code tools, evaluate intermediate outputs, retry or switch strategy, and continue until completion criteria are met.

Build with a vendor-agnostic catalog of 900+ AI models, tools, and integrations, swap models and tools without rewriting pipelines, and use SDK/API or aiXplain Studio on the same runtime and policies. A single API key provides unified access with consolidated billing. Micro-agents handle runtime planning, orchestration, policy checks, and response shaping, while meta-agents (for example, Evolver) optimize behavior over time from trace and KPI feedback.

<div align="center">
  <img src="docs/assets/aixplain-workflow-teamagent.png" alt="aiXplain team-agent runtime flow" title="aiXplain"/>
</div>

## Why aiXplain for developers

- **Autonomous runtime loop** — plan, call tools/models, reflect, and continue without fixed flowcharts.
- **Multi-agent execution** — delegate work to specialized agents at runtime.
- **Governance by default** — inspectors and policy controls execute on every run.
- **Production observability** — use validation traces and run telemetry for debugging and operations.
- **Model and tool portability** — swap assets without rewriting application glue code.
- **Flexible deployment** — run serverless or on-prem (private).

## AgenticOS

AgenticOS is the runtime behind SDK/API and aiXplain Studio, designed around **speed**, **trust**, and **sovereignty**. It provides routing with fallbacks, unified policies and traces, flexible serverless/private deployment, and BYO support for keys, files, models, databases, code, and MCP servers.

<div align="center">
  <img src="docs/assets/aixplain-agentic-os-architecture.png" alt="aiXplain AgenticOS architecture" title="aiXplain"/>
</div>

---

## Quick start

### Installation

```bash
pip install aixplain
```

Get your API key from your [aiXplain account](https://console.aixplain.com/settings/keys).

<details open>
  <summary><strong>v2 (default)</strong></summary>

### Create and run your first agent (v2)

```python
from aixplain import Aixplain

aix = Aixplain(api_key="<AIXPLAIN_API_KEY>")

search_tool = aix.Tool.get("tavily/tavily-web-search/tavily")

agent = aix.Agent(
    name="Research agent",
    description="Answers questions with concise web-grounded findings.",
    instructions="Use the search tool when needed and cite key findings.",
    tools=[search_tool],
)
agent.save()

result = agent.run(query="Summarize the latest AgenticOS updates.")
print(result.data.output)
```

### Build a multi-agent team (v2)

```python
from aixplain import Aixplain

aix = Aixplain(api_key="<AIXPLAIN_API_KEY>")
search_tool = aix.Tool.get("tavily/tavily-web-search/tavily")

planner = aix.Agent(
    name="Planner",
    instructions="Break requests into clear subtasks."
)

researcher = aix.Agent(
    name="Researcher",
    instructions="Find and summarize reliable sources.",
    tools=[search_tool],
)

team_agent = aix.Agent(
    name="Research team",
    instructions="Delegate work to subagents, then return one final answer.",
    subagents=[planner, researcher],
)
team_agent.save()

response = team_agent.run(query="Compare top open-source agent frameworks in 5 bullets.")
print(response.data.output)
```

</details>

<details>
  <summary><strong>v1 (legacy)</strong></summary>

### Create and run your first agent (v1)

```python
from aixplain.factories import AgentFactory, ModelFactory

weather_tool = ModelFactory.get("66f83c216eb563266175e201")

agent = AgentFactory.create(
    name="Weather Agent",
    description="Answers weather queries.",
    instructions="Use the weather tool to answer user questions.",
    tools=[weather_tool],
)

result = agent.run("What is the weather in Liverpool, UK?")
print(result["data"]["output"])
```

You can still access legacy docs at [docs.aixplain.com/1.0](https://docs.aixplain.com/1.0/).

</details>

---

## Security, compliance, and privacy

aiXplain applies runtime governance and enterprise controls by default:

- **SOC 2 Type II certified** — enterprise security and compliance posture.
- **No training on your data** — prompts and outputs are not used to train foundation models.
- **Runtime policy enforcement** — Inspector and Bodyguard govern every agent execution.
- **Sovereign deployment options** — serverless or private (on-prem, VPC, and air-gapped).
- **Encryption** — TLS 1.2+ in transit and encrypted storage at rest.

Learn more at [aiXplain Security](https://aixplain.com/security/) and [Sovereignty](https://aixplain.com/sovereignty/).

---

## Pricing

Start free, then scale with usage-based pricing.

- **Builder credits at signup** — start without upfront cost.
- **Pay as you go** — prepaid usage with no surprise overage bills.
- **Subscription plans** — reduce effective consumption-based rates.
- **Consolidated billing** — track spend across models, tools, and integrations in one place.

Learn more at [aiXplain Pricing](https://aixplain.com/pricing/).

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
