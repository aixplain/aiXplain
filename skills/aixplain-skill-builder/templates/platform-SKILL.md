---
name: {{name}}
description: "Use when … (what it does, then when to load it — name every tool it carries). Do not use for …"
activation: conditional   # or: always
# tools:
#   - type: aixplain
#     tool_id: <asset id or team/name path>
#   - type: script
#     name: my_function
#     description: What the function does.
#     parameters: {text: {type: string}}
#     required: [text]
#     script_file: scripts/my_function.py
---

# {{title}}

One or two sentences: what this skill produces and why it exists.

## Steps

1. …
2. …

## Tools

- `<tool>` — when to call it, and what to do with its result.
- If the tool is not available (for example when this skill runs inside Koder), …

## When things go wrong

- If … then …
