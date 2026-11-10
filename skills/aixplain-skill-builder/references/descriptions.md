# Writing a description that routes

The model sees only `name` + `description` when it decides whether to load a skill.
A skill that is not chosen does nothing, and there is no error — so most of a
skill's reliability is in this one field.

## Rules

1. **What + when.** One clause on what it does, then when to use it. Third person:
   "Use when…", not "I help you…".
2. **Use the user's words.** Front-load the nouns, verbs and file names people
   actually type ("invoice", "receipt", "`.tf`", "Dockerfile", "migration").
   Synonyms count: "transcribe / speech-to-text / captions".
3. **Name every capability.** If the skill does three things, all three appear. A
   capability missing from the description is a capability that never routes.
4. **Fence off neighbours.** If another skill covers nearby ground, end with "Do not
   use for X — use Y." This stops the skill loading on the near-miss.
5. **Be a little pushy.** Models tend to under-load skills. "Use whenever the task
   involves…, even if the user does not say 'skill'" helps for central skills.
6. **Short.** Aim for 200–700 characters; hard ceiling ~1024. Every description is in
   every prompt.
7. **Quote it** in YAML if it contains `: `, `#`, or starts with a quote or bracket.

## Examples

Weak — no trigger words, no "when":

```yaml
description: Helps with documents.
```

Strong:

```yaml
description: "Use when the user wants to fill, read, or merge PDF forms — 'fill this
  PDF', 'extract the fields from form.pdf', 'merge these PDFs'. Handles AcroForm fields
  and flattening. Do not use for Word (.docx) files."
```

Weak — one capability hides another (the places tool never routes):

```yaml
description: Search the web for news and cite sources.
```

Strong — split into two skills, or name both:

```yaml
description: "Use for current events and news searches with citations, AND for finding
  local places (shops, restaurants, branches, opening hours) in a named city."
```

## Testing a description

Write the three trigger prompts and the near-miss *before* the description. After
each change, run all four again. If a trigger misses, add its key word; if the
near-miss fires, add a "Do not use for…" clause naming it.
