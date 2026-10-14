---
name: aixplain-skill-builder
description: Use when the user wants to create, write, scaffold, improve, debug, or publish a skill (a SKILL.md folder) — either a local Koder skill that Koder's own coding agent loads, or an aiXplain platform skill that aiXplain agents use (optionally bundling its own tools). Triggers include "make a skill", "new SKILL.md", "turn this workflow into a skill", "why isn't my skill showing up", "my skill never triggers", "publish my skill to aiXplain", "attach a skill to my agent". Do not use for other Koder configuration (agents, MCP servers, permissions, koder.json) — that is customize-aixplain-code.
metadata: {"author": "Mohamed Elbadrashiny (@elbadrashiny)", "requires": {"env": ["AIXPLAIN_API_KEY"], "bins": ["python3"]}}
---

# aiXplain skill builder

> **Verified against:** aiXplain SDK `0.2.47` (the version Koder pins) and `0.2.48`, and Koder `main` as of 2026-10-14.
> `AIXPLAIN_API_KEY` is needed only to publish platform skills; Koder skills need nothing but `python3` for the checker.

Help the user turn a repeatable task into a skill that loads at the right moment and
does the job well. A skill is a folder whose `SKILL.md` has YAML frontmatter (the
**description** is what the model reads to decide whether to load it) and a markdown
body (what the model follows once it is loaded). Supporting files sit beside it and
are read only when the body points to them.

There are two destinations. Ask which one before writing anything, because the
frontmatter, the location and the test loop differ:

| | **Koder skill** | **aiXplain platform skill** |
|---|---|---|
| Who runs it | Koder's coding agent, on this machine | An aiXplain agent, on the platform |
| Lives in | `.koder/skills/<name>/` or `~/.koder/skill/<name>/` | Uploaded asset (`aix.Skill`), attached with `aix.Agent(skills=[...])` |
| Extra frontmatter | `paths:` (only offer it when matching files are touched) | `activation:`, `tools:` (bundled tools), `requires:` |
| Test | `koder debug skill`, then a fresh session | Run the agent once — the runtime parses `tools:`, the SDK does not |
| Share | Commit the folder, or a `skills.urls` index | `privacy`, and Koder users `koder skill install <name>` |

If the user wants both, write one folder that works in both (a body that does not
depend on bundled tools), then add the platform-only keys. Note that Koder **ignores**
`tools:` and `activation:` — a platform skill installed into Koder becomes
instructions only, so its body must say what to do when the tool is not there.

Details for each destination: `references/koder-skills.md` and
`references/platform-skills.md`. How to write a description that routes:
`references/descriptions.md`. Read the one you need before step 3.

## Workflow

### 1. Capture intent

Start from what already exists. If the conversation shows the user doing the task
(commands they ran, corrections they made), pull the steps and their fixes from it
and confirm rather than re-asking. Otherwise ask, a few at a time:

1. What should the skill let the model do? What does a finished result look like?
2. When should it load? Get **three real prompts** a user would type, and **one
   near-miss** that sounds similar but should *not* load it. These become the tests.
3. Koder, aiXplain platform, or both? For Koder: this project only, or every project?
4. Does it need a script (a step that must be exact every time — parsing, validation,
   an API call) or reference files (long tables, schemas, policy text)?
5. For platform skills: which tools should travel with it (aiXplain asset ids, a
   Python script, an MCP server), and should it load always or on demand?

Do not move on until you can state the trigger and the output in one sentence each.

### 2. Pick the name and location

- `name`: lowercase letters, digits and hyphens, at most 64 characters, and **the same
  as the folder name**. Make it say the job (`terraform-plan-review`, not `helper`).
- Check it does not collide: run `koder debug skill` and look at the `name` fields.
  A duplicate name silently replaces the other skill (last one loaded wins).
- Location (Koder): the project's `.koder/skills/<name>/` to share with the repo, or
  `~/.koder/skill/<name>/` for the user only. See `references/koder-skills.md` for all
  locations and the trust rule (project skills load only in a trusted project).
- Location (platform): any working folder; it is uploaded from there.

### 3. Write the description first

It is the only part the model sees before deciding, and a missed route fails
silently — the model just answers without the skill. Follow
`references/descriptions.md`. In short: say what it does **and** when to use it, in
the third person ("Use when…"); front-load the words and file names users actually
type; name every capability the skill carries; add a "Do not use for…" clause when
there is a neighbouring skill it could steal from. Keep it under ~1024 characters —
every description is in every prompt.

### 4. Scaffold

```bash
python3 scripts/skill_tool.py new <name> --target koder --dir <parent-folder>
python3 scripts/skill_tool.py new <name> --target platform --dir <parent-folder>
```

(Paths are relative to this skill's folder.) This writes `SKILL.md` from
`templates/`, plus empty `references/` and `scripts/`. Then write the body.

### 5. Write the body

- **Imperative steps in order**, the way you would brief a capable colleague. Say
  *why* a rule exists when it is not obvious; the model generalises from reasons
  better than from capital letters.
- **Concrete over abstract**: one worked example (input → output) beats a paragraph
  of description. Show exact commands, file paths, and the shape of the output.
- **Progressive disclosure**: keep `SKILL.md` under ~400 lines. Move long material to
  `references/<topic>.md` and say in the body *when* to read each one. Put exact,
  repeatable work in `scripts/` and tell the model to run them, not re-derive them.
- **Failure paths**: what to do when an input is missing, a command fails, or a tool
  is unavailable. Say when to stop and ask the user.
- **No secrets**: never put API keys or tokens in the folder. Read them from the
  environment (`AIXPLAIN_API_KEY`). Platform skills are uploaded and may be shared.
- **Self-contained paths**: refer to bundled files by path relative to the skill
  folder; do not depend on files outside it.

### 6. Validate

```bash
python3 scripts/skill_tool.py check <path-to-skill-folder> [--target koder|platform]
```

It checks the frontmatter (name format and folder match, description present and
sized, `paths:` shape, platform `tools:` shape), that files the body links to exist,
and scans for committed secrets. Fix every error; read every warning.

### 7. Test that it routes and works

Routing and behaviour are separate questions; test both.

**Koder:** `koder debug skill` must list it (if not, see "Not showing up" in
`references/koder-skills.md`). Then start a **new** session (skills are discovered
when a session starts) and send the three trigger prompts and the near-miss. Check
the transcript shows the skill being loaded for the three and not for the near-miss,
and that the result is right. A `paths:`-scoped skill only appears after a matching
file is mentioned or touched — test with one.

**Platform:** follow the test loop in `references/platform-skills.md`: upload, attach
to a test agent, run each prompt, and read the agent's steps to see which tools fired.
Routing is stochastic — run each prompt at least twice before trusting a result.

### 8. Iterate

When a route is missed, fix the **description** (add the words the user typed). When
the skill loads but does the wrong thing, fix the **body** (add the missing step,
example, or reason). Re-run the same prompts after each change and compare. Stop when
all trigger prompts route, the near-miss does not, and the outputs are right.

### 9. Ship

Hand the user: the folder path, the final description, the test prompts with what
happened, and how to share it (commit the `.koder/skills/<name>` folder; or publish
to aiXplain and give teammates the `koder skill install <name>` line). For a platform
skill, give the asset id and the agent ids it is attached to.

## Improving an existing skill

Read the whole folder first. Ask what went wrong (didn't load / loaded when it
shouldn't / loaded but did badly) — each points to a different fix (step 8). Run
`check` before and after. Keep the `name` unchanged unless the user asks: renaming
breaks permissions, agents and other skills that refer to it.
