<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/aixplain-logo-on-dark.svg">
    <img alt="aixplain" src="docs/assets/aixplain-logo.svg" width="240">
  </picture>
</p>

<h1 align="center">aixplain Agents SDK</h1>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-2ea44f?style=flat-square" alt="License"></a>
  <a href="https://discord.gg/aixplain"><img src="https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
</p>

<p align="center">
  <b>The fastest way to turn an AI agent into an API.</b><br>
  Describe it in Python, call <code>.save()</code>, and it is live. You pay only when someone uses it.
</p>

<p align="center">
  <a href="https://docs.aixplain.com/getting-started/quick-start/">Quickstart</a> ·
  <a href="https://docs.aixplain.com">Docs</a> ·
  <a href="https://docs.aixplain.com/api-reference/python/">API reference</a> ·
  <a href="https://github.com/aixplain/koder">Koder</a>
</p>

## Quickstart

```bash
pip install aixplain
```

Get an API key at [app.aixplain.com](https://app.aixplain.com/team/settings?tab=api-keys), then deploy an agent:

```python
from aixplain import Aixplain

aix = Aixplain(api_key="YOUR_API_KEY")

agent = aix.Agent(
    name="Research agent",
    tools=[aix.Tool.get("tavily/tavily-web-search/tavily")],
).save()

result = agent.run("What are the top AI papers this week?")
print(result.data.output)
```

The agent is now an API. Call it from any language with `agent.id`:

```bash
curl -X POST "https://platform-api.aixplain.com/v2/agents/YOUR_AGENT_ID/run" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top AI papers this week?"}'
```

The response holds a URL to poll for the answer. See the [REST API guide](https://docs.aixplain.com/getting-started/integration/).

## What you get

- **Any model.** 1,000+ models, tools and integrations, one API key.
- **Any tool.** Web search, Slack, Gmail, MCP servers or your own Python.
- **In control.** Budgets cap cost, time and steps. Inspectors check every step.
- **See everything.** Every run's steps, cost and status, in code and in the dashboard.

## Deploy

`.save()` is the deployment. There is no server, container or queue to manage, and the agent keeps its endpoint as you update it.

- **Cloud** is the default: aixplain hosts and scales the agent for you.
- **On-prem** runs the same agent on your own infrastructure, including air-gapped.
- **Local** runs it on your own machine.

See [deployment](https://docs.aixplain.com/deployment/).

## Control

Set limits on the agent and every run respects them:

```python
agent.budget.max_cost = 0.10            # credits per run
agent.budget.max_duration_seconds = 60
agent.budget.max_iterations = 10
agent.save()

result = agent.run("Summarize this week's AI news in three bullets.")
print(result.status, result.used_credits, len(result.data.steps))
```

- **Budgets** cap cost, time and steps per run.
- **Inspectors** check inputs, intermediate steps and final answers, with your own rules or an LLM judge. See [inspectors](https://docs.aixplain.com/assets/agents/inspectors/).
- **Every run** returns its steps, cost and status, and shows up in the [dashboard](https://app.aixplain.com/dashboard).

## Let Koder build it

[Koder](https://github.com/aixplain/koder) builds and deploys aixplain agents for you. Describe the agent; Koder writes, tests and deploys it with the agent builder skill, and you review every change.

Using Claude Code? Install the aixplain plugin from this repo:

```text
/plugin marketplace add aixplain/aiXplain
/plugin install aixplain@aixplain
```

It bundles the agent builder skill and marketplace search. See the [plugin guide](plugins/aixplain), or use the [agent builder skill](skills/aixplain-agent-builder) on its own.

## Learn more

- [Documentation](https://docs.aixplain.com)
- [Example agents](https://github.com/aixplain/cookbook)
- [Marketplace](https://app.aixplain.com/marketplace)
- [Pricing](https://aixplain.com/pricing/) and [security](https://aixplain.com/security/)
- [Run metadata](docs/run-metadata.md): each agent run sends a `metaData` object, including approximate location from one `ipinfo.io` lookup
- [Migration guide](MIGRATION.md): upgrading older code to 0.3.0, where this API is the only one

## Community and support

- Ask questions on [Discord](https://discord.gg/aixplain)
- Report bugs and request features in [GitHub issues](https://github.com/aixplain/aiXplain/issues)
- Talk with the team at [care@aixplain.com](mailto:care@aixplain.com)

## License

Apache License 2.0. See [LICENSE](LICENSE).
