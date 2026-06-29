# Governance & lifecycle: inspectors, debugger, evolver

## Inspectors — runtime guardrails

Inspectors evaluate an agent's input, intermediate steps, or output at runtime and then continue, halt, rewrite, or re-run. They attach to a (team) agent without changing agent code. They are **policy-agnostic** — you express a policy either as an LLM prompt (`ASSET` evaluator) or as a Python function (`FUNCTION` evaluator). There are no built-in named policies like "PII" or "hallucination" — you author the check.

```python
from aixplain.v2.inspector import (
    Inspector, InspectorAction, InspectorActionConfig, InspectorOnExhaust,
    InspectorSeverity, EvaluatorType, EvaluatorConfig, EditorConfig,
)
```

### Building blocks

`Inspector(name, action, evaluator, description=None, severity=None, targets=[], editor=None)`

- **`targets`** — list of strings: `"input"` (raw user query), `"output"` (final response), `"steps"` (intermediate sub-agent outputs).
- **`severity`** — `InspectorSeverity.LOW | MEDIUM | HIGH | CRITICAL`.
- **`action`** — an `InspectorActionConfig(type=..., max_retries=..., on_exhaust=...)`:

| `InspectorAction` | Behaviour |
|---|---|
| `ABORT` | Hard stop — halts the run, returns an error. `response.data.output` is `None`; check `response.status` first. |
| `RERUN` | Re-runs the target agent with the evaluator's critique injected. `max_retries` (keep 2–3) then falls back to `on_exhaust` (`InspectorOnExhaust.ABORT` or `CONTINUE`). |
| `EDIT` | Rewrites content inline before passing downstream. Requires an `editor=EditorConfig(...)`. |
| `CONTINUE` | Shadow / log-only — records the critique, changes nothing. |

- **`evaluator`** — an `EvaluatorConfig`:
  - `ASSET`: delegate the judgment to a marketplace LLM via a plain-English prompt. `EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=<llm_id>, prompt="...")`.
  - `FUNCTION`: your own `(str) -> bool` for deterministic checks. `EvaluatorConfig(type=EvaluatorType.FUNCTION, function=fn)`. Imports go inside the function; it runs synchronously, so no slow I/O.

### Example — block unsafe output (ASSET + ABORT)

```python
llm_id = aix.Model.get("openai/gpt-4o").id
guard = Inspector(
    name="hate-speech-guard",
    description="Blocks output containing hate speech.",
    severity=InspectorSeverity.CRITICAL,
    targets=["output"],
    action=InspectorActionConfig(type=InspectorAction.ABORT),
    evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id=llm_id,
        prompt="If the content contains hate speech, output a failure critique. Otherwise pass."),
)

team = aix.Agent(name="Guarded Agent", description="...", agents=[subagent], inspectors=[guard])
team.save(save_subcomponents=True)
r = team.run(query="...")
if r.status == "SUCCESS":
    print(r.data.output)        # None if the inspector aborted
```

### Example — self-correct (ASSET + RERUN)

```python
action=InspectorActionConfig(type=InspectorAction.RERUN, max_retries=2,
                             on_exhaust=InspectorOnExhaust.ABORT)
```

### Example — sanitize input (FUNCTION + EDIT)

```python
def looks_risky(text: str) -> bool:
    import re
    return any(re.search(p, text.lower()) for p in [r"\bbypass\b", r"\bexploit\b", r"\bhack\b"])

def sanitize(text: str) -> str:
    return "Provide high-level, ethical guidance only."

guard = Inspector(
    name="intent-guard", severity=InspectorSeverity.HIGH, targets=["input"],
    action=InspectorActionConfig(type=InspectorAction.EDIT),
    evaluator=EvaluatorConfig(type=EvaluatorType.FUNCTION, function=looks_risky),
    editor=EditorConfig(type=EvaluatorType.FUNCTION, function=sanitize),
)
```

Inspectors run in declaration order. To add one to an existing team: `team.inspectors.append(guard); team.save()` — re-saving is required, otherwise the inspector step won't appear in `response.data.steps`.

> **Verifying an inspector fires:** the platform's own Response Generator is safety-aligned and often refuses obviously-bad requests before your inspector would trip, so on a headline adversarial query you may see the inspector log `CONTINUE` (pass) rather than `ABORT`. That doesn't mean it's broken. To confirm the gate works, test with input that *deterministically* violates the policy (e.g. a subagent instructed to emit the forbidden value) — then you'll see the `ABORT`/`EDIT` action fire and replace the output. Check `response.data.steps` for the inspector's system-agent step.

Recommended severity → action mapping: `LOW`→`CONTINUE`; `MEDIUM`→`RERUN`(on_exhaust=`CONTINUE`) or `EDIT`; `HIGH`→`RERUN`(on_exhaust=`ABORT`) or `EDIT`; `CRITICAL`→`ABORT`.

> **Default LLM judge:** for an `ASSET` evaluator you can skip choosing a model and use the built-in default judge — `from aixplain.v2.inspector import AUTO_DEFAULT_MODEL_ID` and pass `asset_id=AUTO_DEFAULT_MODEL_ID`.

### Validate after every inspector change

Whenever you add or change an inspector, run exactly three probes and record the outcome of each — this catches both over-blocking and under-blocking:

| Probe | Expected behaviour |
|---|---|
| **Allowed** prompt | CONTINUE path; normal compliant answer |
| **Denied** prompt | Blocked/refused; no restricted data or action leaks |
| **Ambiguous** prompt | Conservative handling — deny or ask for clarification |

For each, capture: the prompt, the expected action, the observed run `status`, a one-line output summary, and pass/fail. (As noted above, the platform's own safety layer may handle the obvious "denied" case before your inspector — to prove *your* gate fires, also test a deterministic trigger.)

### Status semantics

Keep aiXplain's run status as-is: `IN_PROGRESS | SUCCESS | FAILED`. **Do not treat a policy block as `FAILED`** — an inspector that refuses unsafe content can still return run `status == "SUCCESS"` with a safe refusal in `data.output`. That's a governance block, not a runtime failure. Reserve `FAILED` for actual execution errors.

## Debugger — analyze a run

A meta-agent that explains what happened in a completed run. Reachable as `aix.Debugger()`.

```python
debugger = aix.Debugger()
r = agent.run(query="...")
result = debugger.debug_response(r)     # auto-extracts the execution id from the run
print(result.analysis)                   # plain-English explanation
# also: result.used_credits, result.run_time, result.session_id, result.request_id

# or analyze arbitrary content:
debugger.run(content="The agent returned an empty response...").analysis
```

> The Debugger interface ships in the SDK, but its backing service may not be available in all environments. If a call returns "Not Found", fall back to inspecting `response.data.steps` directly (see `references/agents.md`).

## Evolver — continuous improvement

The Evolver is aiXplain's meta-agent for automatically improving an agent from production signals (instruction refinement, tool selection, team composition, parameter tuning), with an auto-apply or human-review mode.

> As of the documented SDK it is **conceptual / not yet exposed as a stable Python API** — there is no documented `aix.Evolver()` class. (`agent.run(...)` does accept an `evolve` parameter, but its behaviour is not documented.) Do not fabricate an Evolver API. If a user asks for it, explain it is platform-side/forthcoming and point them to Studio, and offer the practical alternative: iterate with the Debugger + reasoning traces, and A/B different instructions/tools yourself.

## Bodyguard / access control

Bodyguard (asset-boundary access control, RBAC) is enforced at the platform/runtime level and via API-key scoping — see `references/deployment-access.md § API keys`. It is not a Python class you instantiate.
