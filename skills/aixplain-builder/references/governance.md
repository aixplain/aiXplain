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

| Field | What it takes |
|---|---|
| `action` | `"abort"` \| `"rerun"` \| `"edit"` \| `"continue"`, or a dict for options (see RERUN). |
| `metric` | The evaluator. LLM judge → `{"assetId": <model id>, "prompt": "..."}`; Python check → `{"function": fn}` where `fn(str) -> bool`. |
| `editor` | Required for `"edit"` → `{"function": fn}` where `fn(str) -> str`. |
| `severity` | Plain string. |
| `targets` | List of streams to watch. |
| `preset_id` | Set automatically for marketplace guardrails (see Pre-built). |

| Action | Behaviour |
|---|---|
| `abort` | Hard stop — halts the run. `response.data.output` is `None`; check `response.status` first. |
| `rerun` | Re-runs the target with the evaluator's critique injected, then falls back to `on_exhaust`. |
| `edit` | Rewrites content inline before passing it downstream. Requires `editor`. |
| `continue` | Shadow / log-only — records the critique, changes nothing. |

Get an LLM judge's id with `LLM_ASSET_ID = aix.Model.get("openai/gpt-4o").id`, or use the built-in default: `from aixplain.v2.inspector import AUTO_DEFAULT_MODEL_ID` (this constant *does* still exist).

### ABORT — hard stop

```python
guard = aix.Inspector(name="hate-speech-guard", severity="critical", targets=["output"],
    action="abort",
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the content contains hate speech, output a failure critique. Otherwise pass."})

agent = aix.Agent(name="Guarded Agent", instructions="You are a helpful assistant.", inspectors=[guard])
agent.save()

r = agent.run(query="...")
print(r.data.output if r.status == "SUCCESS" else f"Run halted: {r.status}")
```

### RERUN — self-correct with retries

`max_retries` / `on_exhaust` go **inside the action dict**. Passing them as top-level keyword arguments raises `TypeError` on 0.2.48 (the published docs show that form — it is wrong).

```python
guard = aix.Inspector(name="customer-name-enforcer", severity="medium", targets=["output"],
    action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},   # or "continue"
    metric={"assetId": LLM_ASSET_ID,
            "prompt": "If the output does NOT include the customer name 'John', instruct to add it."})
```

Keep `max_retries` at 2–3 and always set `on_exhaust`: `"abort"` when convergence is mandatory, `"continue"` when best-effort output is acceptable.

### EDIT — sanitize with your own functions

```python
def looks_risky(text: str) -> bool:
    import re                                   # imports go INSIDE — the function runs in isolation
    return any(re.search(p, text.lower()) for p in [r"\bbypass\b", r"\bexploit\b", r"\bhack\b"])

def sanitize(text: str) -> str:
    return "Provide high-level, ethical guidance only."

guard = aix.Inspector(name="intent-guard", severity="high", targets=["input"],
    action="edit",
    metric={"function": looks_risky},           # True  -> rewrite
    editor={"function": sanitize})              # performs the rewrite
```

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

Known paths: `aws/detect-prompt-attacks-guardrail/aws`, `aws/sensitive-information-guardrail/aws`, `aws/content-moderation-guardrail/aws`. Search rather than hardcoding — the catalog grows.

The PII guardrail rewrites flagged values in place (`"...your phone number is {PHONE}"`) instead of blocking.

## Reading governance results

`response.data.governance` reports what governance ran on a request — including runs with no inspector attached. Use it to confirm a guard actually fired, alongside the inspector's system-agent step in `response.data.steps`.

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

### Status semantics

Keep aiXplain's run status as-is: `IN_PROGRESS | SUCCESS | FAILED`. **Do not treat a policy block as `FAILED`** — an inspector that refuses unsafe content can still return `status == "SUCCESS"` with a safe refusal in `data.output`. That's a governance block, not a runtime failure.

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
