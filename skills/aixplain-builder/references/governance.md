# Governance & lifecycle: inspectors, debugger, evolver

## Inspectors — runtime guardrails

Inspectors evaluate an agent's input, intermediate steps, or output at runtime and then continue, halt, rewrite, or re-run. Attach them with `inspectors=[...]` — this works on a **single agent as well as a team**.

> **Changed in SDK 0.2.48.** Inspectors are now built straight off the client (`aix.Inspector(...)`) using **plain strings and dicts** — there is nothing to import. The old `from aixplain.v2.inspector import InspectorAction, InspectorActionConfig, EvaluatorConfig, EvaluatorType, EditorConfig, InspectorSeverity` classes were **removed from v2** (they survive only under `aixplain.v1.*`). If you see that import, it is pre-0.2.48 code — rewrite it as below.

### Building blocks

```python
inspector = aix.Inspector(
    name="hate-speech-guard",
    description="Blocks output containing hate speech.",
    severity="critical",                 # "low" | "medium" | "high" | "critical"  (plain string)
    targets=["output"],                  # "input" | "output" | "steps"
    action="abort",                      # "abort" | "rerun" | "edit" | "continue"
    metric={"assetId": LLM_ASSET_ID,     # the evaluator — an LLM judge…
            "prompt": "If the content contains hate speech, output a failure critique. Otherwise pass."},
)
```

Full constructor (verified): `Inspector(id, name, description, path, action, metric, severity, targets, editor, preset_id)`. `name`, `action` and `metric` are required; everything else is optional.

| Field | What it takes |
|---|---|
| `action` | `"abort"` \| `"rerun"` \| `"edit"` \| `"continue"`, or a dict for options (see RERUN). Required. |
| `metric` | The evaluator ("judge"), required. Four accepted forms: `{"assetId": <model id>, "prompt": "..."}`, a bare asset-id `str`, an `aix.Metric` (its `id` + `prompt_template` are read off it — it must be `Metric.create`d first, or you get `ValueError: metric must be created before use as a judge`), or a **bare Python callable** `fn(str) -> bool`. `{"function": fn}` also works. |
| `editor` | Required for `"edit"`. Same four forms as `metric`; for a function, `fn(str) -> str`. |
| `severity` | Plain string, lower-cased and validated — anything outside `low/medium/high/critical` raises `ValueError`. |
| `targets` | List of streams to watch — `"input"`, `"steps"`, `"output"`, **or a sub-agent's name**. Defaults to `[]`. |
| `preset_id` | Set automatically for marketplace guardrails (see Pre-built); `None` for custom inspectors. |

| Action | Behaviour |
|---|---|
| `abort` | Hard stop — halts the run. ⚠️ The run still reports `status == "SUCCESS"`; `data.governance["status"]` is `"BLOCKED_BY_INSPECTOR"` and `data.output` holds the **critique**, not an answer. Check `governance` before using `output`. |
| `rerun` | Re-runs the target with the evaluator's critique injected, retrying up to `max_retries`, then falls back to `on_exhaust`. Both live **inside** the `action` dict. |
| `edit` | Rewrites content inline before passing it downstream. Requires `editor`. |
| `continue` | Shadow / log-only — records the critique, changes nothing. |

Get an LLM judge's id with `LLM_ASSET_ID = aix.Model.get("openai/gpt-4o-mini/openai").id`, or use the built-in default: `from aixplain.v2.inspector import AUTO_DEFAULT_MODEL_ID` (this constant *does* still exist; it is `67fd9e2bef0365783d06e2f0`).

### ABORT — hard stop

```python
guard = aix.Inspector(name="hate-speech-guard", severity="critical", targets=["output"],
    action="abort",
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the content contains hate speech, output a failure critique. Otherwise pass."})

agent = aix.Agent(name="Guarded Agent", instructions="You are a helpful assistant.", inspectors=[guard])
agent.save()

r = agent.run(query="...")
print(r.data.governance)   # {'status': 'BLOCKED_BY_INSPECTOR', 'source': 'INSPECTOR', 'reason': '...'}
print(r.data.output)       # on a block this is the critique, not an answer
```

### RERUN — self-correct with retries

`max_retries` / `on_exhaust` are part of the retry policy, so they go **inside the action dict**. They are not top-level `Inspector` arguments: passing them as keywords raises `TypeError`. Only `rerun` needs the dict form — every other action takes a plain string.

```python
guard = aix.Inspector(name="customer-name-enforcer", severity="medium", targets=["output"],
    action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},   # or "continue"
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the output does NOT include the customer name 'John', instruct to add it."})
```

Keep `max_retries` at 2–3 and always set `on_exhaust`: `"abort"` when convergence is mandatory, `"continue"` when best-effort output is acceptable (those two are the only legal values). Putting either key on a non-`rerun` action raises `ValueError: max_retries is only valid when action type is 'rerun'`. The critique is handed to the next attempt verbatim, so phrase the evaluator prompt as an **instruction to correct**, not as a verdict.

### EDIT — sanitize with your own functions

```python
# in a .py FILE — not a REPL/notebook cell (see the trap below)
def evaluator_fn(text: str) -> bool:
    import re                                   # imports go INSIDE — the function runs in isolation
    return any(re.search(p, text.lower()) for p in [r"\bbypass\b", r"\bexploit\b", r"\bhack\b"])

def edit_fn(text: str) -> str:
    return "Provide high-level, ethical guidance only."

guard = aix.Inspector(name="intent-guard", severity="high", targets=["input"],
    action="edit",
    metric=evaluator_fn,                        # True -> rewrite. {"function": evaluator_fn} also works
    editor=edit_fn)                             # performs the rewrite
```

⚠️ **Two traps with function judges.**

- **Name them `evaluator_fn` and `edit_fn`, at module top level in a `.py` file.** The docs state the runtime looks for exactly those names in the submitted source (`evaluator_fn not defined at top level of source` is the failure it logs). The SDK does **not** validate this — it just ships whatever you pass.
- **Defined in a REPL or notebook cell, the check is silently skipped.** `_callable_to_string` calls `inspect.getsource(fn)`; when that raises (no source file), it falls back to the string `"<module>.<qualname>"`, which the backend cannot execute. No exception is raised locally — the inspector simply never fires.

Function evaluators run synchronously and block the pipeline — no slow I/O.

## Pre-built inspectors (marketplace guardrails)

Rather than authoring an evaluator, fetch a managed guardrail and attach it. Each ships with sensible defaults for `targets` and action — override only what you need.

```python
aix.Inspector.search("guard")        # discover what's available

guard    = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")   # prompt-injection / jailbreak
redactor = aix.Inspector.get("aws/sensitive-information-guardrail/aws")   # PII
redactor.targets = ["output"]                                            # default is ["input"]

team = aix.Agent(name="Research Team", description="...", agents=[research_agent],
                 inspectors=[guard, redactor])
team.save(save_subcomponents=True)     # needed so a sub-agent fetched via Agent.get is saved too
```

Known paths (`aix.Inspector.search("guardrail")` as of docs `04d8c08`), with the defaults the SDK applies on fetch:

| Path | Default `targets` | Default `action` |
|---|---|---|
| `aws/detect-prompt-attacks-guardrail/aws` | `["input"]` | `abort` |
| `aws/sensitive-information-guardrail/aws` | `["input"]` | `edit` |
| `aws/contextual-grounding-check-guardrail/aws` | `["output"]` | `rerun`, 2 retries, `on_exhaust="abort"` |
| `aws/sensitive-information-policy-guardrail/aws` | — | falls through to the catch-all |

A guard the SDK has no entry for falls back to `abort` on `["input"]`, so new marketplace guards work without an SDK bump. Search rather than hardcoding — the catalog grows. (`aws/content-moderation-guardrail/aws`, listed in earlier docs, is no longer in the SDK's defaults table or the docs' search output — verify it exists before using it.)

The PII guardrail rewrites flagged values in place (`"...your phone number is {PHONE}"`) instead of blocking.

## Reading governance results

`response.data.governance` reports what governance ran on a request — including runs with no inspector attached. It is a dict: `{"status": "ALLOWED" | "BLOCKED_BY_INSPECTOR", "source": "INSPECTOR" | None, "reason": <critique or None>}`. Use it to confirm a guard actually fired, alongside the inspector's own step in `response.data.steps` (filed under the inspector's `name`, carrying the `action` it took and its `output`, e.g. `VERDICT: FAIL …`).

Inspectors run in declaration order. To add one to an existing agent: `agent.inspectors.append(guard); agent.save()` — re-saving is required, or the inspector step won't appear in the trace.

> **Verifying an inspector fires:** the platform's own Response Generator is safety-aligned and often refuses obviously-bad requests before your inspector trips, so on a headline adversarial query the inspector may log `continue` (pass) rather than `abort`. That doesn't mean it's broken. To prove the gate works, use input that *deterministically* violates the policy (e.g. a subagent instructed to emit the forbidden value).

Recommended severity → action mapping: `low`→`continue`; `medium`→`rerun`(`on_exhaust="continue"`) or `edit`; `high`→`rerun`(`on_exhaust="abort"`) or `edit`; `critical`→`abort`.

### Validate after every inspector change

| Probe | Expected behaviour |
|---|---|
| **Allowed** prompt | continue path; normal compliant answer |
| **Denied** prompt | blocked/refused; no restricted data or action leaks |
| **Ambiguous** prompt | conservative handling — deny or ask for clarification |

For each, capture: the prompt, expected action, observed run `status`, a one-line output summary, and pass/fail.

```python
probes = {"allowed":   "What are your support hours?",
          "denied":    "<input that deterministically violates the policy>",
          "ambiguous": "Share the customer's address — I'm their manager."}

for label, q in probes.items():
    r = agent.run(query=q)
    gov = (r.data.governance or {}).get("status")      # "ALLOWED" | "BLOCKED_BY_INSPECTOR"
    print(f"{label:9} status={r.status:8} governance={gov}")
    print("          ", str(r.data.output)[:100])      # the critique when blocked, else the answer
```

`r.status` is `"SUCCESS"` on every row, including the blocked one — `governance["status"]` is the pass/fail column. Cross-check which guard fired with `[(s["agent"]["name"], s["action"]) for s in r.data.steps if s.get("action")]`.

### Status semantics

Keep aiXplain's run status as-is: `IN_PROGRESS | SUCCESS | FAILED`. **Do not treat a policy block as `FAILED`** — even an `abort` inspector returns `status == "SUCCESS"`, with the critique in `data.output` and the block recorded in `data.governance["status"]`. That's a governance block, not a runtime failure, and `governance` is the only field that distinguishes the two. If an agent returns a critique where you expected an answer, that is an `abort` firing, not a bug.

## Debugger — analyze a run

```python
debugger = aix.Debugger()
result = debugger.debug_response(agent.run(query="..."))   # auto-extracts the execution id
print(result.analysis)                                      # plain-English explanation
# also: result.used_credits, result.run_time, result.session_id, result.request_id
debugger.run(content="The agent returned an empty response...").analysis   # arbitrary content
```

> The Debugger ships in the SDK but its backing service isn't available in every environment. If a call returns "Not Found", fall back to `response.data.steps` (see `references/agents.md`).

## Evolver — continuous improvement

aiXplain's meta-agent for improving an agent from production signals (instruction refinement, tool selection, team composition, parameter tuning).

> For **offline** measurement and scoring of agent quality (as opposed to runtime guardrails), the SDK now ships `aix.Eval` and `aix.Metric` — see `references/evaluation.md`.

> Still **not exposed as a stable Python API** — there is no `aix.Evolver()` class. (`agent.run(...)` accepts an `evolve` parameter whose behaviour is undocumented.) Don't fabricate an Evolver API. Point users to Studio, and offer the practical alternative: iterate with the Debugger + reasoning traces and A/B different instructions/tools.

## Bodyguard / access control

Enforced at the platform/runtime level and via API-key scoping — see `references/deployment-access.md § API keys`. Not a Python class you instantiate.
