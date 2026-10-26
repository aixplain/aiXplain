---
name: model-selection
description: Help someone choose the right aixplain model for their project. Starts from the job, applies the hard limits first (data retention, modality, context, budget, speed), shortlists 2–3 current models from the live marketplace with a reviewed tier for each, estimates cost, and then compares the shortlist on the user's own examples. Use whenever the user asks which model to use, "what's the best LLM for X", "cheaper/faster model than Y", "should I switch my agent's model", "which models keep no data (ZDR)", or wants to compare models for an agent, a pipeline, transcription, translation, vision or embeddings, even if they never say "model selection".
---

# Choosing a model on aixplain

The catalog changes every week, so this skill never answers from memory. It combines three sources:

| Source | What it gives | Changes |
|---|---|---|
| Marketplace Search MCP (`mcp__aixplain-marketplace-search__*`) | what exists now: id, path, price, ZDR, description | live |
| `references/tiers.json` | the team's reviewed tier and strengths per LLM | weekly PR |
| A test run on the user's examples | which candidate actually works for their project | per project |

Every model name, price and ZDR value you report must come from a tool result or `tiers.json`. Never
rank a model by its name or by what you remember about it. If the MCP tools are missing, the plugin's
server has not connected: ask the user to `export AIXPLAIN_API_KEY=...` (keys at
https://studio.aixplain.com, account settings).

## 1. Pin down the job and the hard limits

Get these from the request. Ask one short question only if a hard limit is unknown and would change the
answer; otherwise assume the default and say so.

| | Default if unsaid |
|---|---|
| Job: agent with tools, chat, extraction/classification, coding, long documents, vision, speech, translation, embeddings | — (ask) |
| Data retention: must the provider keep no prompts? | no requirement |
| Input: text only, or images / audio / video / PDFs | text |
| Context: largest input in one call | normal (under 100K tokens) |
| Volume and budget: calls per day, cost ceiling | moderate |
| Speed: user waiting in real time, or background | real time |
| Language: Arabic or another non-English language | English |

If the user just wants an agent built and has no special need, say the platform default is a good
start and they can change it later (`agent.llm = "<id>"`, see the aixplain-builder skill). Only
continue when they want to choose.

## 2. Pull the current candidates

Use the live catalog, filtered by the hard limits:

```
search_models(query: "", categories: ["LLM"], zdr: ["true"], sort: "newest", page_size: 100)
```

- Drop `zdr` when retention is not a requirement. `zdr: "unknown"` means unverified, not safe: never
  present an unknown as zero retention.
- `sort` takes `relevance`, `price_asc`, `price_desc` or `newest`. For "cheapest" use `price_asc`.
- Not an LLM job? Filter by `function` instead (`speech-recognition`, `translation`, …) or by
  `categories` (`Speech`, `OCR`, `Image`, …), then sort by price. Tiers below cover LLMs only; for
  other models go straight to step 4 with 2–3 candidates.
- Read context length and modality from the description. If it does not say, write "not listed".
- Skip models whose description says they are uncensored, "cracked" or built for a narrow domain,
  unless the user asked for exactly that. `tiers.json` lists them under `excluded`.

## 3. Rank with the tiers

Load `references/tiers.json`. Each reviewed model has a `tier` and `good_for` tags:

| Tier | Use it for |
|---|---|
| `frontier` | hard reasoning, long multi-step agent work, complex coding, high-stakes answers |
| `balanced` | most agents with tools, chat, analysis: the usual starting point |
| `fast` | high volume or real time: extraction, classification, routing, summaries, simple agent steps |

Start from the tier the job needs, match `good_for` to the job, and keep only models that are in the
live results from step 2 (a model in `tiers.json` but not in the catalog has been removed: skip it).
A model in the catalog but not in `tiers.json` is new and unreviewed: you may include it, labelled
"new, not yet reviewed", judged only from its description.

## 4. Shortlist and price it

Give 2–3 candidates: usually the best fit, a cheaper option one tier down, and a ZDR or alternative
provider option if relevant. For each, estimate monthly cost from the listed prices:

```
cost per call ≈ input_tokens × input_price + output_tokens × output_price
```

State your token assumptions (an agent step with tools is often 3–10K input tokens). Prices are as
listed by the marketplace, per token.

**Price sanity check.** Per-token prices on the catalog are tiny (around 1e-8 to 1e-4). A listed
`input_price` above 0.001 is almost certainly in a different unit: do not compare it, and tell the
user the price needs confirming. For exact pricing call `get_asset_details`, which also returns
`supplier`, `hosted_by` and `data_retention`.

## 5. Test on the user's examples

General tiers narrow the list; the user's own examples decide. Ask for 3–5 real inputs (or offer to
draft realistic ones), and ask before running, since every call spends credits. Then run:

```python
import os
from aixplain import Aixplain

aix = Aixplain(api_key=os.environ["AIXPLAIN_API_KEY"])
candidates = ["<id-1>", "<id-2>", "<id-3>"]
examples = ["<example 1>", "<example 2>", "<example 3>"]

for model_id in candidates:
    model = aix.Model.get(model_id)
    for text in examples:
        r = model.run(text=text)
        print(model.name, r.status, round(r.run_time or 0, 1), "s", r.used_credits, "credits")
        print(r.data, "\n")
```

For an agent, compare the whole agent instead: build it once, set `agent.llm = "<id>"` (not
`llm_id`), `save()`, run the same queries, and repeat per candidate. For non-text models, pass the
input names `list_inputs_models` returns.

Show the results side by side: output, time, credits. Point out where a candidate failed or drifted
from the instructions. Let the user judge quality on their own task; do not declare a winner on one
example.

## 6. Answer

Lead with the recommendation and one line of why, then a short table:

| Model | Path | Tier | Price in / out (per token) | ZDR | Why it's here |
|---|---|---|---|---|---|

Then how to use it (`aix.Model.get("<path>")`, or `agent.llm = "<id>"`), and what you assumed.
Say when a tier is "new, not yet reviewed". Never paste raw tool JSON.

## Keeping this skill current (maintainers)

- `references/tiers.json` is reviewed by people. Edit it by hand: add new models, move tiers, mark
  removals. Each entry says where its judgment came from.
- `references/catalog.json` is a snapshot of every LLM on the marketplace, written by
  `tooling/refresh.py`.
- `.github/workflows/model-selection-refresh.yaml` runs the refresh every Monday. It opens a PR with
  the new snapshot and a report: new models to tier, removed models still in `tiers.json`, price and
  ZDR changes, and prices that look like the wrong unit. A reviewer updates `tiers.json` in the same
  PR before merging.
