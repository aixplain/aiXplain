# Koder skills — reference

How Koder finds, offers and loads a skill. Checked against the aixplainCode `main`
branch, 2026-10-14. If behaviour differs on the user's version (`koder --version`),
trust what `koder debug skill` shows.

## Where Koder looks

Koder scans these places when a session starts. Any folder holding a `SKILL.md`
(any letter case) is a skill.

| Location | Scope | Notes |
|---|---|---|
| `<project>/.koder/skills/<name>/SKILL.md` (also `skill/`) | This project | **Only when the project is trusted.** Commit it to share with the team. Legacy spelling `.aixplain-code/` still works. |
| `~/.koder/skill/<name>/SKILL.md` (also `skills/`) | Every project | Where `koder skill install` puts platform skills. Best place for a personal skill. |
| Koder's global config folder `skill/` or `skills/` (for example `~/.config/koder/skills/`) | Every project | Same rules as the line above. |
| `~/.agents/skills/<name>/SKILL.md` | Every project | The shared cross-agent skills folder; skills there are picked up as-is. |
| `<project>/.agents/skills/…` (walking up to the repo root) | This project | Trusted projects only. |
| `skills.paths` in `koder.json` | As configured | Each path is scanned for `**/SKILL.md`; `~/` is expanded; relative paths are from the project. |
| `skills.urls` in `koder.json` | As configured | HTTPS only. Each URL serves `index.json` = `{"skills":[{"name":"x","files":["SKILL.md","references/a.md"]}]}`; files are fetched from `<url>/<name>/<file>`. |

Environment switch: `KODER_DISABLE_EXTERNAL_SKILLS=1` turns off the `.agents` scans
(and Koder's other external skill folders).

Two skills with the same `name`: the one loaded last wins and a warning is logged. A
user skill named like a built-in one (for example `customize-aixplain-code`) replaces
the built-in — avoid that unless it is the intent.

## Frontmatter Koder reads

```yaml
---
name: terraform-plan-review          # required; lowercase-hyphen, ≤64 chars, = folder name
description: Use when …              # required in practice — see below
paths: ["*.tf", "terraform/**"]      # optional; a list, or a single string
license: Apache-2.0                  # optional
compatibility: koder>=0.3            # optional
metadata: {owner: platform-team}     # optional, string → string
---
```

- **No `name:`** → the skill is dropped and Koder shows "Skill ignored: … needs a
  `name:`".
- **No `description:`** → the skill loads but is **never shown to the model**, so it
  can never be chosen. This is the most common "my skill does nothing" cause.
- **Bad YAML** → the skill is dropped and Koder shows a parse error. Quote any
  description containing `: ` or starting with a special character.
- **`paths:`** keeps the skill out of the catalog until the turn mentions or touches a
  matching file (matched against the full path, the path relative to the project, and
  the bare file name). Then Koder adds a `<skills_available>` notice. Use it for
  file-type-specific skills so they do not cost prompt space elsewhere. Do not use it
  for skills triggered by a request rather than a file — they would never appear.
- Any other key (`tools:`, `activation:`, `requires:`, `allowed-tools:`) is ignored by
  Koder. It does no harm, but do not rely on it here.

## How a skill is used

1. Every session prompt lists each visible skill's `name` and `description`.
2. The model calls the `skill` tool with a name; the body (everything after the
   frontmatter) is injected as a `<skill_content name="…">` block.
3. The body tells the model which bundled files to read or run. Files are not loaded
   automatically — the body must point to them.

Agents can be barred from skills with the `skill` permission in `koder.json`, either
for all skills or by name:

```json
{ "agent": { "reviewer": { "permission": { "skill": { "*": "allow", "deploy-*": "deny" } } } } }
```

The **last** matching pattern wins, so put the broad `"*"` first and the exceptions
after it.

## Testing

```bash
koder debug skill            # every skill Koder loaded, as JSON (name, description, location, paths)
koder debug skill | grep -A3 '"name": "my-skill"'
```

Then open a **new** session and try the trigger prompts. `koder run "<prompt>"`
works for a quick non-interactive check; the transcript shows whether the `skill`
tool was called.

## Not showing up — checklist

1. Is the file literally inside `<location>/<name>/SKILL.md`, one level under
   `skills/` or `skill/`?
2. Does `koder debug skill` list it? If not: missing `name:`, YAML error, wrong
   folder, or an untrusted project (project-level skills need trust).
3. Listed but never used: missing or vague `description:`, or a `paths:` scope that
   nothing in the turn matched, or an agent `skill` permission set to `deny`.
4. Still the old version: start a new session — discovery happens at session start.
5. Another skill with the same name took its place (check `location` in the debug
   output).
