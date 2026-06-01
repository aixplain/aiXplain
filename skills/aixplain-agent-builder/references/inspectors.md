# Inspector Reference

Inspector policy patterns and post-change validation for aiXplain agents.
Linked from the main skill — consult when adding inspectors.

See `agent-patterns.md § Add Inspector` for the full v2 construction code. Use the v2 API (`aixplain.v2.inspector`), not the v1 `aixplain.modules.team_agent.inspector` path.

---

## Policy Guidelines

- Set the policy via `InspectorActionConfig(type=...)`. Valid `InspectorAction` values: `CONTINUE | RERUN | ABORT | EDIT`.
- Prefer `ABORT` for hard policy violations.
- Use `RERUN` for recoverable quality issues — it is the only action type that accepts `max_retries` and `on_exhaust` (`CONTINUE | ABORT`); setting them on any other type raises.
- `EDIT` requires an `editor=EditorConfig(...)`.
- For existing deployments: fetch the team agent, modify `inspectors`/`inspector_targets`, call `.save()`.

---

## Status Semantics

Keep aiXplain run status as-is: `IN_PROGRESS | SUCCESS | FAILED`.
Do not overload `FAILED` for policy blocks — a policy block can still return run `SUCCESS` with a safe refusal output. Treat that as a governance block, not a runtime failure.

---

## Inspector Action Values

`InspectorAction` SDK values: `continue | rerun | abort | edit`.

---

## Post-Change Validation (Mandatory)

After adding/updating inspectors, run exactly 3 prompts:

| Test | Expected Behavior |
|------|-------------------|
| **Allowed prompt** | Continue path, compliant normal answer |
| **Denied prompt** | Blocked/denial, no restricted data/action |
| **Ambiguous prompt** | Conservative handling (deny or ask clarification) |

For each case capture: `prompt`, `expected_action`, `observed_run_status`, `observed_output_summary`, `pass_fail`.
