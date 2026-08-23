# aixplain agent-builder bug and quirk ledger

Working log for reproducible issues discovered while using this skill. This file is evidence for later engineering issues; it is not a substitute for reproducing a defect.

## Logging rules

- Log only behavior attributable to the aixplain SDK, runtime, integration, or public docs—not user input or ordinary configuration mistakes.
- Reproduce with SDK v2 and the current stable package before adding an entry.
- Redact API keys, emails, customer data, workspace IDs, agent IDs, and workspace-bound tool IDs.
- Keep minimal repros safe and non-destructive.
- Do not open a public GitHub issue without user approval.
- Target approved issues to https://github.com/aixplain/aiXplain.

## Entry template

```markdown
### BUG-NNN — Short title

- **Status:** candidate | reproduced | workaround-verified | filed | fixed | closed
- **Found:** YYYY-MM-DD
- **SDK:** aixplain X.Y.Z
- **Runtime/environment:** PROD | DEV | TEST | on-prem | unknown
- **Surface:** Agent | Tool | Integration | Session | Budget | Inspector | Docs
- **Severity:** blocker | high | medium | low
- **Expected:**
- **Actual:**
- **Impact:**
- **Minimal v2 repro:**
  ```python
  # redacted, self-contained reproduction
  ```
- **Exact error/trace:**
- **Workaround:**
- **Evidence/notes:**
- **Public issue:** not filed | URL
```

## Open candidates

### BUG-001 — Newer skill source uses an inspector API absent from the stable wheel

- **Status:** reproduced
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** local isolated stable wheel
- **Surface:** Inspector / Docs
- **Severity:** high
- **Expected:** Current agent-builder guidance should match the public `0.2.47` wheel.
- **Actual:** The newer source skill used `InspectorActionConfig` + `EvaluatorConfig`, but the stable wheel intentionally exposes plain strings for `action`, `targets`, and `severity`, plus a Metric/asset ID/callable/dict for `metric`. The stable constructor is `(id, name, description, path, action, metric, severity, targets, editor, preset_id)`.
- **Impact:** Code generated from the newer source skill fails to import the typed config classes against the stable package.
- **Minimal v2 repro:**
  ```python
  import inspect
  from aixplain.v2.inspector import Inspector
  print(inspect.signature(Inspector))
  # No InspectorActionConfig or EvaluatorConfig is required or exported.
  ```
- **Exact error/trace:** Import failure when attempting to use the stale typed config-class example.
- **Workaround:** Use `Inspector(name="gate", targets=["output"], action="abort", metric={"asset_id": "<MODEL_ID>", "prompt": "..."})`.
- **Evidence/notes:** Reproduced from an isolated installation of the public `0.2.47` wheel; corrected in `references/inspectors.md`.
- **Public issue:** not filed

### BUG-002 — `agent.run(budget=...)` is silently ignored

- **Status:** reproduced
- **Found:** 2026-08-18
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Agent / Budget
- **Severity:** high
- **Expected:** A supplied run budget should apply or raise a clear error.
- **Actual:** The run path removes the `budget` kwarg without warning; the agent's existing `agent.budget` is used.
- **Impact:** A developer can believe a run is capped when it is not.
- **Minimal v2 repro:**
  ```python
  from aixplain.v2 import Budget
  agent.run(query="test", budget=Budget(max_cost=0.01))
  ```
- **Exact error/trace:** No warning or error.
- **Workaround:** Assign `agent.budget` (or mutate its fields) before `run()`, then restore it if the cap is one-off.
- **Evidence/notes:** Previously reproduced against PROD and documented in the newer source skill.
- **Public issue:** not filed

### BUG-003 — Budget cost cap can materially overshoot billed credits

- **Status:** reproduced
- **Found:** 2026-08-18
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Agent / Budget / Team
- **Severity:** high
- **Expected:** A cost cap should bound billed cost closely and report all delegated spend.
- **Actual:** Enforcement occurs between steps and subagent spend meters separately. A measured team run with a `0.0020` credit cap billed `0.0115` credits (5.7×), while governance reported a smaller observed amount.
- **Impact:** `max_cost` cannot be treated as a billing ceiling.
- **Minimal v2 repro:** Requires a billable team run; do not reproduce casually.
- **Exact error/trace:** Run may return `SUCCESS` with `BLOCKED_BY_BUDGET` governance.
- **Workaround:** Treat budget as a circuit breaker, cap lead iterations, and use `execution_stats['credits']` as actual spend.
- **Evidence/notes:** Previously reproduced against PROD and documented in the newer source skill.
- **Public issue:** not filed

### BUG-004 — Marketplace search response key is easy to misdocument

- **Status:** workaround-verified
- **Found:** 2026-08-18
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Tool / Docs
- **Severity:** medium
- **Expected:** Examples use the actual response shape.
- **Actual:** Older examples use `items`; live Marketplace Search responses use `results` under each asset kind.
- **Impact:** Search loops silently return no assets and coding agents may incorrectly conclude that no integration exists.
- **Minimal v2 repro:**
  ```python
  search = aix.Tool.get("6960f934f316da19e5f22494")
  result = search.run(action="search", data={"query": "calendar"})
  print(result.data["integration"].keys())
  ```
- **Exact error/trace:** No error; iteration over a default empty `items` list returns nothing.
- **Workaround:** Read `result.data[kind]["results"]`.
- **Evidence/notes:** Corrected in this skill.
- **Public issue:** not filed

### BUG-005 — Integration tools returning JSON objects can fail only inside agent loops

- **Status:** reproduced
- **Found:** 2026-08-18
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Tool / Agent / Integration
- **Severity:** high
- **Expected:** A tool output accepted by direct `tool.run()` should be accepted when invoked by an agent.
- **Actual:** Some connectors that return a JSON object fail on OpenAI Responses-API models with `Invalid type for 'input': ... got an object`, while direct execution succeeds.
- **Impact:** A verified connector can appear broken only after attachment.
- **Minimal v2 repro:** Connector-specific and requires credentials; use a redacted provider integration that returns an object.
- **Exact error/trace:** `Invalid type for 'input': ... got an object`.
- **Workaround:** Use a compatible Gemini/Mistral model or call the connector directly in deterministic application code.
- **Evidence/notes:** Previously reproduced with a provider connector against PROD.
- **Public issue:** not filed

### BUG-007 — HTML and ZIP uploads can fall back to `text/csv`

- **Status:** workaround-verified
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** stable wheel source
- **Surface:** FileUploader / MIME detection
- **Severity:** medium
- **Expected:** `.html` and `.zip` files receive their standard MIME types.
- **Actual:** Neither extension exists in `MimeTypeDetector.EXTENSION_MAPPING`; when content sniffing returns no type, the fallback is `text/csv`.
- **Impact:** Browsers and downstream tools can receive the wrong content type or filename behavior.
- **Minimal v2 repro:**
  ```python
  from aixplain.v2.upload_utils import MimeTypeDetector
  print(MimeTypeDetector.detect_mime_type("report.html"))
  ```
- **Exact error/trace:** No error; incorrect fallback MIME type.
- **Workaround:** Add `.html: text/html` and `.zip: application/zip` to `EXTENSION_MAPPING` before upload.
- **Evidence/notes:** Confirmed in the public `0.2.47` wheel source and documented in `integration-playbooks.md`.
- **Public issue:** not filed

### BUG-008 — `Resource.create_from_file()` does not upload until `save()`

- **Status:** source-verified quirk
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** stable wheel source
- **Surface:** Resource / file upload
- **Severity:** low
- **Expected:** A method named `create_from_file` could reasonably return an uploaded resource with a usable URL.
- **Actual:** It only constructs `Resource(file_path=...)`; `.url` remains empty until `.save()` calls the uploader.
- **Impact:** Tool configs can receive `None` when callers immediately read `.url`.
- **Minimal v2 repro:**
  ```python
  resource = aix.Resource.create_from_file("data.db")
  assert resource.url is None
  ```
- **Exact error/trace:** No error; URL is empty.
- **Workaround:** Construct or call `create_from_file`, then call `resource.save()` before reading `resource.url`.
- **Evidence/notes:** Confirmed from the stable wheel implementation and documented in `integration-playbooks.md`.
- **Public issue:** not filed

### BUG-009 — `Agent.get()` widens hydrated tool action scopes

- **Status:** reproduced
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Agent / Tool / deserialization
- **Severity:** high
- **Expected:** A fetched agent's tools preserve each backend tool entry's scoped `actions` as `allowed_actions`.
- **Actual:** The raw agent correctly persisted SQLite as `["schema", "query"]` and the KB as `["search", "get"]`, but `Agent.get()` hydrated SQLite as `["query", "commit", "schema"]` and the KB as every available action, including `delete` and `upsert`. `_build_tool_tool()` derives `allowed_actions` from all `parameters` and ignores the raw entry's `actions` field.
- **Impact:** A get→mutate→save cycle can silently broaden a previously least-privilege agent, enabling database writes or KB deletion/upsert.
- **Minimal v2 repro:**
  ```python
  raw = aix.Agent.context.client.get(f"v2/agents/{agent_id}")
  loaded = aix.Agent.get(agent_id)
  print(raw["tools"][0]["actions"])
  print(loaded.tools[0].allowed_actions)
  ```
- **Exact error/trace:** No error or warning; the hydrated object reports broader permissions.
- **Workaround:** Before update/export, read raw `v2/agents/<ID>`, map each tool ID to its raw `actions`, and reassign those values to the corresponding hydrated tool's `allowed_actions`. Recheck the raw payload after save.
- **Evidence/notes:** Reproduced by the complex practical test; runtime execution used only intended actions and the backend raw payload remained correctly scoped.
- **Public issue:** not filed

### BUG-010 — Static `tasks` execution can skip an attached required tool

- **Status:** reproduced; behavior/contract needs clarification
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** Agent / static task graph / tools
- **Severity:** medium
- **Expected:** An agent with Code Execution scoped to `run`, instructions requiring Code Execution, and three static tasks that each require deterministic calculation or verification invokes the tool.
- **Actual:** The static-task agent returned the correct result, but its trace contained only three GPT-5.4 units and no Code Execution unit. Identical adaptive and planner agents both invoked Code Execution.
- **Impact:** A static task graph can appear deterministic while calculations are performed by the model instead of the required tool.
- **Minimal v2 repro:** Run `scripts/execution_strategy_test.py`; compare `code_execution_used` for `adaptive`, `static_tasks`, and `planner`.
- **Exact error/trace:** No error. Static trace: `["GPT-5.4", "GPT-5.4", "GPT-5.4"]`.
- **Workaround:** When tool invocation is mandatory, use adaptive or planner execution and assert the expected tool unit appears in `result.data.steps`. Do not infer tool use from code-formatted output.
- **Evidence/notes:** Reproduced by `scripts/execution_strategy_test.py` for sum-of-squares result `2870`; persisted config had three tasks, no planner, and Code Execution scoped to `run`.
- **Public issue:** not filed

### BUG-011 — Agent listing/hydration emits budget warnings

- **Status:** reproduced
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** PROD
- **Surface:** `Agent.search()` / deserialization
- **Severity:** low
- **Expected:** Listing and reloading saved agents is warning-free when their persisted budgets are valid.
- **Actual:** Recovery via `Agent.search(page_number=..., page_size=...)` emitted a dataclasses-json warning for a null non-optional budget; running a reloaded result also emitted a conflicting `max_iterations`/budget warning.
- **Impact:** Noisy CI and automation; callers may mistake a hydration warning for invalid saved state.
- **Exact warnings:**
  ```text
  RuntimeWarning: 'NoneType' object value of non-optional type budget detected when decoding Agent.
  UserWarning: Both 'max_iterations' and budget.max_iterations are set; budget.max_iterations takes precedence.
  ```
- **Workaround:** Prefer direct `Agent.get(id)` when the ID is known. In recovery/listing utilities, suppress only these exact known warnings after separately validating raw persisted budget fields.
- **Evidence/notes:** Reproduced while recovering the three execution-strategy test agents after a partial harness failure.
- **Public issue:** not filed

### BUG-012 — SDK persists `response_generator`, but runtime ignores the responder role

- **Status:** source-verified intentional deprecation / compatibility mismatch
- **Found:** 2026-08-22
- **SDK:** aixplain 0.2.47
- **Runtime/environment:** `aixplain-agents` 1.3.0, commit `028a81acdcaca4e8e4f406ad2a1cb5801f937403`
- **Surface:** Agent model roles / payload adapter / final response generation
- **Severity:** medium
- **Expected:** Passing a configured model as `response_generator=` and seeing it persisted under backend `responder` causes a dedicated final-response model pass.
- **Actual:** The runtime explicitly deprecates and ignores `run_response_generation`. `_APPLIED_ROLE_BUCKETS` contains only `llm` and `planner`; populated `supervisor`, `responder`, and `inspector` model-parameter buckets emit “not applied yet” warnings. Runtime design documentation says the separate responder LLM pass was deliberately dropped.
- **Impact:** SDK round-trip checks can falsely suggest the responder model and its parameters are active, leading to incorrect behavior and cost assumptions.
- **Minimal v2 repro:** Save an agent with `response_generator=<Model>`, verify the raw `responder` payload exists, then inspect runtime adapter warnings and execution traces; no dedicated responder pass occurs.
- **Exact warning:** `modelParameters.responder is not applied yet — only llm / planner are honoured`.
- **Workaround:** Do not configure `response_generator` in new builds. Put final-answer requirements in the primary agent instructions or model them as an explicit task/subagent whose execution is visible in the trace.
- **Evidence/notes:** `aixplain_agents/adapter/payload_adapter.py` deprecates `run_response_generation`, defines applied role buckets as `llm` and `planner`, and warns on `responder`. `docs/feature-gap-agentification-vs-aixplain-agents.md` marks the separate second-LLM pass as intentionally deprecated.
- **Public issue:** not filed; runtime documentation describes this as intentional

## Fixed or historical

### BUG-006 — `Agent.get()` then `save()` could overwrite the configured LLM

- **Status:** fixed
- **Found:** before 2026-07-22
- **SDK:** affected 0.2.43/0.2.44; fixed 0.2.47
- **Runtime/environment:** SDK
- **Surface:** Agent
- **Severity:** high
- **Expected:** A read-modify-save cycle preserves the configured model.
- **Actual:** Earlier versions populated `.llm` with the workspace default and persisted it on save.
- **Impact:** Editing instructions could silently change model behavior and cost.
- **Minimal v2 repro:** Historical; see release `0.2.47` notes.
- **Exact error/trace:** Silent behavior; no error.
- **Workaround:** Upgrade to `0.2.47`. If a regression is observed, compare backend model before/after and open a new entry rather than reviving this one.
- **Evidence/notes:** Fixed by the public `0.2.47` release.
- **Public issue:** fixed upstream
