# Inspectors and governance (SDK v2)

Use inspectors only when runtime policy or quality enforcement is required. Least-privilege tool actions remain necessary; inspectors do not replace permissions.

## Stable 0.2.47 surface

The published `0.2.47` wheel intentionally uses a small, plain-data API: strings for `action`, `targets`, and `severity`; a Metric, asset ID, callable, or judge dict for `metric`. There are no public `InspectorActionConfig` or `EvaluatorConfig` classes in this release.

```python
from aixplain.v2.inspector import Inspector, AUTO_DEFAULT_MODEL_ID

inspector = Inspector(
    name="Content Gate",
    description="Blocks output that violates the approved content policy.",
    severity="high",                         # low | medium | high | critical
    targets=["output"],                      # input | steps | output | subagent name
    action="abort",                          # continue | rerun | abort | edit
    metric={
        "asset_id": AUTO_DEFAULT_MODEL_ID,
        "prompt": "Fail output that violates the approved content policy.",
    },
)

team.inspectors = [inspector]
team.save()
```

Do not import from `aixplain.modules.team_agent.inspector`; that is v1. Do not generate the older typed config-class form for SDK `0.2.47`.

## Action choice

- `abort`: hard policy violation.
- `rerun`: recoverable quality problem. Retry settings use a dict:

```python
action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}
```

- `edit`: sanitize output and requires `editor=` using the same accepted forms as `metric`.
- `continue`: observe/log without intervention.

A custom callable can act as the judge:

```python
def contains_required_citation(text: str) -> bool:
    return "http" in text

inspector = Inspector(
    name="Citation Check",
    targets=["output"],
    action="rerun",
    metric=contains_required_citation,
)
```

For reusable/model-backed judges, prefer an onboarded `aix.Metric` object or an asset ID plus prompt.

## Mandatory policy verification

After every inspector change, run exactly three cases:

| Case | Expected behavior |
|---|---|
| Allowed | normal compliant answer |
| Denied | blocked/refused; restricted action or data absent |
| Ambiguous | conservative refusal or clarification request |

Capture:

```yaml
prompt: ...
expected_action: ...
observed_run_status: ...
observed_governance: ...
observed_output_summary: ...
pass_fail: ...
```

A policy block can return run status `SUCCESS`. Always read `result.data.governance` and inspect output; never equate `SUCCESS` with permission or completion.

## Product boundary

Debugger/Evolver meta-agents and dynamic self-improvement are not part of this skill's GA build path. Do not fabricate APIs. Use traces, controlled A/B changes, and explicit user review instead.
