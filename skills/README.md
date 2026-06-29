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
| [aixplain-builder](./aixplain-builder) | Build, run, and deploy anything on aiXplain across the full v2 SDK — direct model inference (LLMs, Whisper/speech, translation, vision, embeddings), single & team agents, knowledge bases/RAG, tools & integrations (Slack, Gmail, databases, MCP, custom Python), runtime governance/inspectors, memory, and REST/JS/OpenAI-compatible access. Ships a self-update pipeline (`tooling/`) that re-syncs the skill with the docs + SDK. |
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

### Step 1 — Download the skill

Get the skill folder onto your machine in either way.

**Clone the whole repo:**

```bash
git clone https://github.com/aixplain/aiXplain.git
```

**Or download just the skill folder:**

1. Copy the skill folder URL from this GitHub repo (e.g. the `aixplain-agent-builder` folder).
2. Go to [download-directory.github.io](https://download-directory.github.io).
3. Paste the URL and press Enter to download the ZIP, then unzip it.

> **Note:** `download-directory.github.io` is a third-party helper, not affiliated with or provided by aiXplain.

### Step 2 — Install the skill

**Claude Code (recommended).** Copy the skill folder into your Claude Code skills directory:

```bash
cp -r aiXplain/skills/aixplain-agent-builder ~/.claude/skills/
```

The skill is now available in any Claude Code session. Trigger it explicitly with `/aixplain-agent-builder`, or just describe your task ("build an aiXplain agent that…") and the agent loads it automatically. To scope a skill to a single project instead of globally, copy it into that project's `.claude/skills/` directory.

**Claude Desktop.** Open **Settings → Capabilities → Skills**, then drag and drop the skill folder (or its `.zip`) to upload it.

### Using with other agents (Codex, Cursor, Copilot, …)

The auto-discovery above is a Claude Code / Claude Desktop feature — those tools read `~/.claude/skills/` and load the skill automatically. Other agents don't scan that directory, but a skill is just markdown, so you can wire it in manually using each tool's own convention:

| Agent | How to wire it in |
|-------|-------------------|
| Codex | Reference or paste `SKILL.md` into your `AGENTS.md` |
| Cursor | Add `SKILL.md` as a rule under `.cursor/rules/` |
| GitHub Copilot | Add it to `.github/copilot-instructions.md` |
| Any chat / MCP client | Paste `SKILL.md` (and any needed `references/` files) into context |

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
