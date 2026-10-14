# aiXplain platform skills — reference

A platform skill is the same kind of folder (a `SKILL.md` plus `references/`,
`scripts/`), uploaded as an aiXplain asset and attached to aiXplain agents. It can
also carry the tools its instructions use, so the agent itself needs none.

Checked against the aiXplain Python SDK (`aix.Skill`, 0.2.47 — the version Koder
pins — through `main` in October 2026).

## Frontmatter

```yaml
---
name: invoice-extraction
description: "Use when the user uploads or links an invoice/receipt and wants fields
  extracted (vendor, date, totals, line items) or checked against a PO."
activation: conditional      # conditional (default): loaded when the description matches
                             # always: bound before the agent's first LLM call
tools:                       # optional — tools that travel with the skill
  - type: aixplain           # a marketplace or workspace asset
    tool_id: 6a8e0f757fc4032716e39e6d    # hex asset id, or a path like aixplain/web-search/aixplain
    actions: [search]                    # optional: limit which actions are exposed
    parameters: {num_results: 5}         # optional: fixed parameters
  - type: script             # a Python function shipped in the folder
    name: total_check
    description: Recompute line-item totals and report mismatches.
    parameters: {items: {type: array, items: {type: object}}}
    required: [items]
    script_file: scripts/total_check.py  # relative to the skill folder
  - type: mcp                # an MCP server (url or command)
    url: https://example.com/mcp
  # type: builtin also exists (a built-in runtime toolkit); check the platform docs
  # for its keys before using it.
requires: []                 # optional: tool paths the skill expects the agent to have
---
```

### Rules that matter

- **The SDK does not check `tools:`.** It reads only `name`, `description` and
  `requires`, then uploads the folder as-is. The **agent runtime** parses `tools:`, so
  a typo shows up only when the agent runs — never at `save()`. Always run the agent
  once after editing `tools:` (and run `skill_tool.py check --target platform`).
- **One capability per skill, and the description must name every tool it carries.**
  The agent routes on the description alone. A tool hidden behind a description about
  something else is silently never used — the agent answers from memory instead.
- **Safety and always-needed rules stay in the agent's own instructions**, or in an
  `activation: always` skill. A conditional skill that fails to route drops its rules
  without any error.
- **Every skill's description is in every prompt**, loaded or not. Keep them short.
- When matching tool calls in an agent's `steps`, use `unit["id"]`, not the name: a
  bundled tool reports a display name.

## Publish

Run with the user's key from the environment — never write the key into the folder.
Inside Koder, `koder skill run aixplain-agent-builder -- publish.py` runs a script
with Koder's managed SDK and the signed-in user's key already set.

```python
# publish.py
from aixplain import Aixplain
import os

aix = Aixplain(api_key=os.environ["AIXPLAIN_API_KEY"])

skill = aix.Skill(file_path="./invoice-extraction")   # folder with SKILL.md (or a single .md)
skill.save()                                          # uploads the folder, registers the asset
print("skill id:", skill.id)

agent = aix.Agent(
    name="invoice-assistant-test",
    description="Test agent for the invoice-extraction skill",
    instructions="You help with invoices.",
    skills=[skill],          # Skill objects or ids
)
agent.save()
print("agent id:", agent.id)
```

Other calls: `aix.Skill.get("<id or team/name>")`, `aix.Skill.search("invoice")`,
`skill.download()`, `skill.list_files()`, `skill.delete()`.

To attach to an existing agent and keep its id:
`agent = aix.Agent.get("<agent id>"); agent.skills = [*agent.skills, skill]; agent.save()`.

### Updating a published skill

- On the SDK Koder pins (0.2.47), saving the same `Skill` object again after editing
  the folder does **not** re-upload. Newer SDKs re-upload on `save()`, but files you
  deleted locally stay in the uploaded copy.
- The dependable path on every version: **delete and re-create** the skill, then put
  the new id on each agent that used the old one (`agent.skills = [...]; agent.save()`
  keeps the agent's id). Do this for renames too.

## Test loop

1. Publish to a **test agent** (not a production agent).
2. Run each trigger prompt and the near-miss, at least twice each:

   ```python
   for prompt in PROMPTS:
       r = agent.run(prompt)
       print(prompt, "→", r.data.output[:200])
       for step in r.data.steps or []:
           print("   step:", step.get("unit", {}).get("id"), step.get("unit", {}).get("name"))
   ```

3. Expect: the bundled tool ids appear in `steps` for the trigger prompts, and not for
   the near-miss. A plausible answer with **no** tool call means the skill did not
   route — fix the description.
4. Routing varies run to run; compare two passes before calling a change better or
   worse.
5. Delete the test agent when done, or keep it as the skill's regression harness.

## Sharing and installing in Koder

- `privacy` on the asset controls who can see it (private by default).
- Koder users list and install platform skills with:

  ```bash
  koder skill list            # your private skills
  koder skill list --public   # include shared ones
  koder skill install <id|name>
  koder skill installed
  koder skill remove <name>
  ```

  Installs land in `~/.koder/skill/<slug>/`. If the uploaded `SKILL.md` has no
  frontmatter, Koder adds `name`/`description` from the platform metadata.
- In Koder the skill is **instructions only** — Koder ignores `tools:` and
  `activation:`. Write the body so it still helps without the bundled tools (for
  example, "if the `total_check` tool is not available, recompute the totals with a
  short Python snippet").
