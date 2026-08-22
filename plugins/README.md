# aixplain Plugins

Claude Code **plugins** for the [aixplain](https://aixplain.com) platform.

A plugin bundles a [skill](../skills/README.md) together with the MCP servers it needs, so one install
gives your coding agent both the knowledge and the live connection. Where a skill teaches an agent how
to do something, a plugin also hands it the tools.

---

## Available plugins

| Plugin | Description |
|--------|-------------|
| [aixplain-marketplace](./aixplain-marketplace) | Search the aixplain marketplace from your editor — find agents, models, tools, and integrations in one call, read pricing and hosting, and get working code to call any asset via SDK, REST, or MCP. |
| [aixplain-agent-builder](./aixplain-agent-builder) | Build, connect, deploy, verify, debug, update, and export production aixplain agents with the SDK v2. |

---

## Install

```
/plugin marketplace add aixplain/aiXplain
```

Then install the plugin you want. Each plugin's README lists the environment variables it expects —
typically just an aixplain API key:

```bash
export AIXPLAIN_API_KEY=your_api_key
```

Create a key at [studio.aixplain.com](https://studio.aixplain.com) under Settings → API Keys.

---

## Plugin or skill?

Both work. Pick by what you need:

| | Skill alone | Plugin |
|---|---|---|
| Teaches the agent aixplain patterns | yes | yes |
| Connects live MCP servers | no — add them yourself | yes, bundled |
| Install | copy a folder to `~/.claude/skills/` | one command |

A plugin's skill can always be lifted out and used on its own — copy its `skills/<name>/SKILL.md` to
`~/.claude/skills/<name>/SKILL.md` and configure the MCP server separately. Useful for clients that
read skills but not Claude Code plugins.

---

## Layout

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json   # manifest: name, description, author
├── .mcp.json                    # MCP servers, keys referenced as ${ENV_VAR}
├── README.md                    # what it does, install, what works
└── skills/<skill-name>/
    └── SKILL.md                 # the instructions the agent loads
```

`.mcp.json` must never contain a literal API key — reference an environment variable
(`"Authorization": "Bearer ${AIXPLAIN_API_KEY}"`) so nothing secret is committed.

---

## Other MCP clients

The MCP servers a plugin declares are client-agnostic and work in Cursor, VS Code, Codex, and Claude
Desktop. Only the plugin *packaging* is Claude Code specific. Each plugin's README documents the
equivalent config for other clients.

---

## Contributing

Add a folder under `plugins/`, following the layout above, and register it in the `plugins` array of
[`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) at the repo root. Verify every
documented call against a real run before committing it — a plugin that describes behavior the platform
does not have is worse than no plugin.
