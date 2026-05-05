# Inspector Analytics Contract

Inspector policy patterns, analytics schema, and validation requirements.
Linked from the main skill — consult when adding inspectors.

---

## Policy Guidelines

- Prefer `InspectorPolicy.ABORT` for hard policy violations.
- Prefer `InspectorPolicy.ADAPTIVE` for recoverable quality issues.
- Configure `RERUN` inspectors with explicit `max_retries` and `on_exhaust` behavior.
- For existing deployments: fetch `TeamAgent`, modify `inspectors`/`inspector_targets`, call `.save()`.

---

## Status Semantics

Keep aiXplain run status as-is: `IN_PROGRESS | SUCCESS | FAILED`.
Do not overload `FAILED` for policy blocks.

### Governance Status Enum (App-Level)

| Status | Meaning |
|--------|---------|
| `ALLOWED` | Inspector passed, normal execution |
| `BLOCKED_BY_INSPECTOR` | Inspector aborted the run |
| `REQUIRES_HUMAN_REVIEW` | Inspector flagged for manual review |
| `INSUFFICIENT_AUTH_CONTEXT` | Missing role/scope context |
| `RESTRICTED_SCOPE` | Request exceeds allowed scope |

### Inspector Action Values

SDK values: `continue | rerun | abort`.

If product UI uses `CONT|RERUN|ABORT|EDIT`, map explicitly:
- `CONT` -> `continue`
- `RERUN` -> `rerun`
- `ABORT` -> `abort`
- `EDIT` -> app-derived extension (not native inspector action)

---

## Per-Run Inspector Event Fields

Minimum fields to capture per inspector evaluation:

| Field | Description |
|-------|-------------|
| `run_id` | Parent run identifier |
| `inspector_event_id` | Unique event ID |
| `inspector_name` | Inspector name |
| `target` | `INPUT | STEPS | OUTPUT` |
| `decision` | `continue | rerun | abort` |
| `reason_code` | Machine-readable reason |
| `severity` | `LOW | MEDIUM | HIGH | CRITICAL` |
| `final_effect` | `none | rerouted | blocked` |
| `timestamp_start_utc` | Evaluation start |
| `timestamp_end_utc` | Evaluation end |
| `latency_ms` | Evaluation duration |
| `retries_used` | Number of retries consumed |
| `governance_status` | App-level governance status |
| `access_policy` | Nullable policy object |
| `approval_status` | `DRAFT | PENDING_REVIEW | APPROVED | REJECTED` (nullable) |
| `run_total_latency_ms` | Total run duration |
| `token_or_credit_usage` | Nullable; fallback to run-level |

---

## Required Mapping Rules

| Decision | Governance Status | Final Effect |
|----------|-------------------|--------------|
| `abort` | `BLOCKED_BY_INSPECTOR` | `blocked` |
| `rerun` (successful retry) | — | `rerouted` |
| `continue` (no intervention) | — | `none` |

Policy block can still return run `SUCCESS` with safe refusal output — treat as governance block, not runtime failure.

---

## Post-Change Validation Matrix (Mandatory)

After adding/updating inspectors, run exactly 3 prompts:

| Test | Expected Behavior |
|------|-------------------|
| **Allowed prompt** | Continue path, compliant normal answer |
| **Denied prompt** | Blocked/denial, no restricted data/action |
| **Ambiguous prompt** | Conservative handling (deny or ask clarification) |

For each case capture:
- `prompt`
- `expected_action`
- `observed_run_status`
- `observed_governance_status`
- `observed_output_summary`
- `pass_fail`

---

## Per-Inspector KPI Cards

When an agent is selected, show these metrics per inspector:

| Metric | Description |
|--------|-------------|
| `inspector_id` | Unique ID |
| `inspector_name` | Display name |
| `inspector_desc` | Description |
| `target` | Input/Steps/Output |
| `policy/action_mode` | Policy type |
| `severity_model` | Severity classification |
| `evaluation_count` | Inspector evaluations (not agent runs) |
| `pass_rate_pct` | Pass rate (explicit formula required) |
| `block_rate_pct` | Abort outcomes rate |
| `rerun_rate_pct` | Rerun rate |
| `edit_rate_pct` | Edit rate (if applicable) |
| `avg_reruns_per_evaluation` | Average retries |
| `retry_exhausted_count` | Exhausted retry count |
| `avg_latency_ms` | Average evaluation latency |
| `p95_latency_ms` | 95th percentile latency |
| `avg_credits_per_evaluation` | Credit cost per evaluation |
| `last_config_change_at` | Last modification timestamp |
| `last_config_change_by` | Last modifier |
| `config_version` | Configuration version |
| `drift_7d_vs_30d_pass_delta` | 7-day vs 30-day pass rate drift |
| `drift_7d_vs_30d_block_delta` | 7-day vs 30-day block rate drift |

### Trend Chart (Daily)

Track per inspector: `pass_count`, `block_count`, `rerun_count`, `override_count`.
