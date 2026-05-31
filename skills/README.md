# aiXplain Skills

A curated library of **Agent Skills** for the [aiXplain](https://aixplain.com) platform.

A skill is a folder of instructions and reference material that teaches an AI coding agent (Claude Code, Claude Desktop) how to do a real task on aiXplain — building agents, wiring tools and integrations, deploying, and debugging — using the aiXplain SDK. Install a skill and your agent gains expert, up-to-date knowledge of how to use aiXplain correctly.

---

## What is a skill?

Each skill is a self-contained folder:

```
aixplain-agent-builder/
├── SKILL.md            # the entry point the agent loads
└── references/         # deeper guides loaded on demand
    ├── agent-patterns.md
    ├── integration-playbooks.md
    └── inspectors.md
```

The agent reads `SKILL.md` first and pulls in the reference files only when it needs them. Every code path is verified against a specific aiXplain SDK version (noted at the top of each `SKILL.md`).

---

## Available skills

| Skill | Description |
|-------|-------------|
| [aixplain-agent-builder](./aixplain-agent-builder) | Design, deploy, run, debug, and export production agents on aiXplain — single agents, team agents, tools, OAuth integrations, and inspectors. |

> More skills coming soon. See [Contributing](#contributing) to add one.

---

## Prerequisites

- **Python 3** and `pip`
- The aiXplain SDK: `pip install --upgrade aixplain`
- An **aiXplain API key** — create one at [studio.aixplain.com](https://studio.aixplain.com) → Settings → API Keys, then expose it:
  ```bash
  export AIXPLAIN_API_KEY="your_key_here"
  ```
  (or add it to a local `.env` file)

---

## Installation

### Option A — Claude Code (recommended)

Copy the skill folder into your Claude Code skills directory:

```bash
git clone https://github.com/aixplain/aiXplain.git
cp -r aiXplain/skills/aixplain-agent-builder ~/.claude/skills/
```

The skill is now available in any Claude Code session. Trigger it explicitly with `/aixplain-agent-builder`, or just describe your task ("build an aiXplain agent that…") and the agent loads it automatically.

To scope a skill to a single project instead of globally, copy it into that project's `.claude/skills/` directory.

### Option B — Claude Desktop

1. Download or zip the skill folder (e.g. `aixplain-agent-builder/`).
2. In Claude Desktop, open **Settings → Capabilities → Skills**.
3. Drag and drop the skill folder (or its `.zip`) to upload it.

### Updating

Pull the latest and re-copy:

```bash
cd aiXplain && git pull
cp -r skills/aixplain-agent-builder ~/.claude/skills/
```

---

## Contributing

1. Create a folder under `skills/<your-skill-name>/` with a `SKILL.md` entry point.
2. Put deep-dive material in a `references/` subfolder; keep `SKILL.md` lean and load references on demand.
3. Verify every code snippet against a known SDK version and note that version at the top of `SKILL.md`.
4. Keep skills self-contained — a user should never need to leave the skill to consult external SDK source.
5. Open a pull request into `main`.

---

## License

See the repository [LICENSE](../LICENSE).
