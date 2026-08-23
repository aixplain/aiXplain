# aixplain plugin

One Claude Code plugin for two connected jobs:

- **Discover:** search the live aixplain marketplace through the bundled Marketplace Search MCP, inspect real schemas, and generate runnable SDK, REST, or MCP code.
- **Build:** create, verify, debug, update, and export production aixplain agents with the bundled Agent Builder skill.

Install it once, then use either skill as the task requires:

```text
/plugin marketplace add aixplain/aiXplain
/plugin install aixplain@aixplain
```

**Prefer a visual walkthrough?** Open the interactive [Install & Use aixplain guide](./install-guide.html) for copyable commands, first-use examples, and a standalone Agent Builder fallback.


Driven by the first-party Marketplace Search tool (`6960f934f316da19e5f22494`). A hosted equivalent —
the **Marketplace Concierge** agent — is published on the marketplace at
`aixplain/marketplace-concierge/aixplain` for anyone who would rather ask in Studio than in an editor.
Neither depends on the other.

## Sharing this with someone

**If they use Claude Code and you can send them files** — two steps, no repo access needed:

1. Add the server:
   ```bash
   claude mcp add --transport http aixplain-marketplace-search \
     https://models-mcp.aixplain.com/mcp/6960f934f316da19e5f22494 \
     --header "Authorization: Bearer THEIR_API_KEY"
   ```
2. Send them `skills/marketplace-search/SKILL.md` to save at
   `~/.claude/skills/marketplace-search/SKILL.md`.

That is the whole thing. The plugin wrapper is a convenience for installing both at once — it is not
required, and the skill works standalone.

**If they use Codex, Cursor, or another MCP client** — the server works anywhere; only the skill
packaging is Claude Code specific. See [Other clients](#other-clients) below.

**As an installable plugin** — one command:

```
/plugin marketplace add aixplain/aiXplain
```

then install `aixplain`. This also installs the `marketplace-search` skill and wires up the
MCP server in one step.

## Other clients

The MCP server is client-agnostic. The skill is not — `SKILL.md` is a Claude Code format.

**Codex** (`~/.codex/config.toml`) — Codex supports remote HTTP MCP servers via a bare `url =`. For a
static auth header the reliable path is the `mcp-remote` stdio bridge:

```toml
[mcp_servers.aixplain-marketplace-search]
command = "npx"
args = ["-y", "mcp-remote", "https://models-mcp.aixplain.com/mcp/6960f934f316da19e5f22494", "--header", "Authorization:${AUTH_HEADER}"]

[mcp_servers.aixplain-marketplace-search.env]
AUTH_HEADER = "Bearer YOUR_API_KEY"
PATH = "/opt/homebrew/bin:/usr/bin:/bin"
```

To give Codex the same query knowledge, paste the body of `skills/marketplace-search/SKILL.md` into
`~/.codex/AGENTS.md`.

**Claude Desktop and older clients** without native remote MCP use the same `mcp-remote` bridge in
JSON form — see the MCP config block inside the skill.

## Install

```bash
export AIXPLAIN_API_KEY=your_aixplain_api_key
```

Get a key from https://studio.aixplain.com under account settings, then add this plugin. The bundled
`.mcp.json` wires up the marketplace search MCP server with that key — no config editing.

The server is PROD, so you are searching the live catalog.

## What you get

The `marketplace-search` skill, plus the MCP server it drives. Ask in plain language:

```
Do we have a Whisper model? Who hosts it and what does it cost?
How many LLMs are on aixplain? How many hosted by OpenAI?
Which integrations are developed by aixplain?
Find me a speech-to-text model and show me how to call it
Find a web search tool and attach it to a new agent
```

One `search` spans agents, models, tools, and integrations at once — you do not need to know the asset
type up front.

## What works today

Verified against PROD on 2026-08-18:

| | |
|---|---|
| Search across agents, models, tools, integrations in one call | yes |
| Filter by category, developer, supplier, host, function, type | yes |
| Read pricing, host, supplier, status | yes |
| Read an asset's real input schema | yes |
| Emit SDK / REST / MCP / agent-attach code from that schema | yes |
| Run and test an asset via generated SDK code | yes |
| Sort results (cheapest, newest) | no — no sort parameter; sort locally after paging |
| Run an asset via the MCP `run_*` actions | no — broken, use generated code instead |

## Beyond search

The skill reads each asset's real input schema (`list_inputs_*`) before writing a snippet, so the code
it emits uses the asset's actual parameter names rather than placeholders. From a single hit it can
produce:

- a Python SDK call
- an `aix.Agent(tools=[...])` block that attaches the asset to a new agent
- a REST call with the right endpoint for that asset type
- an MCP config block so another client can use that specific asset directly

## Layout

```
plugins/aixplain/
  .claude-plugin/plugin.json    manifest
  .mcp.json                     Marketplace Search MCP, ${AIXPLAIN_API_KEY}
  skills/marketplace-search/    marketplace discovery and runnable-code guidance
  skills/aixplain-agent-builder/ agent build, verification, update, and export guidance
```

The skill is usable on its own: copy `skills/marketplace-search/SKILL.md` to
`~/.claude/skills/marketplace-search/SKILL.md` and add the MCP server separately.

## Notes

- Models and tools are individually available over hosted MCP; agents and integrations are not.
- Pricing comes back in two shapes — per-unit (`price` + `unit_type`) and per-token (`input_price` /
  `output_price`). The skill reports whichever applies.
- The search MCP tool ID (`6960f934f316da19e5f22494`) is stable across environments.


## Agent Builder

Use the bundled `aixplain-agent-builder` skill to build, run, verify, debug, update, or export aixplain agents with SDK v2. It uses the same `AIXPLAIN_API_KEY` and can use Marketplace Search to discover an asset before attaching it to an agent.

The skill validates generated export code before presenting it, keeps iteration limits in `agent.budget`, requires explicit consent before external connections, and verifies real runs before reporting success.
