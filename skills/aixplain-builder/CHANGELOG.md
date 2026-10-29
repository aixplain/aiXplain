# Changelog — aixplain-builder

What changed in this skill, newest first. Each entry records the **aiXplain SDK version** and the **`sdk-documentation` commit** the content was derived from and verified against, so any release can be traced back to its sources.

Maintained with `tooling/refresh_skill.py` (see `tooling/README.md`): `check` detects drift, `publish` ships the loadable skill.

---

## 2026-10-29 — Tracing, and the docs restructure
**SDK 0.2.48** (unchanged) · **docs [`04d8c08`](https://github.com/aixplain/sdk-documentation/commit/04d8c08)** · 54 doc changes, 0 API drift

Upstream split the agents documentation into focused pages (`budgets`, `files`, `sessions`, `skills`, `triggers`, `tracing`) and consolidated others (`databases` replaces `sqlite` + `postgresql`; `team-agents` and `shared-memory` were removed and folded elsewhere).

### Added
- **`references/tracing.md`** — new reference: reading `response.data.steps`, execution metrics, tracing subagents in a team, watching a run live (`progress_format` / `progress_verbosity` / `AgentProgressTracker`), and the dashboard.
- Budgets: the full `governance` triple (`ALLOWED` / `BLOCKED_BY_BUDGET` / `BLOCKED_BY_INSPECTOR`) and per-run budget overrides.
- Files: the `reference_files/` runtime surface, plus the three known limits (no `File.delete()`, `url` can be `None`, a file id is not a run input).
- Sessions: `Session.get`, server-side resume, `SessionMessage` fields, `history` vs `session`.
- Skills/Triggers: constructor overrides of `SKILL.md` frontmatter; `interval` / `timezone` semantics.
- SQL: rewritten from `databases.md` — PostgreSQL has **no `commit`** (writes go through `query`) and is **not yet supported inside agents**.
- Usage examples for previously example-free sections (marketplace search, Web Search, Marketplace Search, Code Execution, the travel/multi-source pattern, REST upload, v1→v2 migration, inspector validation, dashboard lookup).

### Fixed — three things this skill had wrong
- **An `abort` inspector does not null the output.** The run still returns `SUCCESS` and `data.output` holds the inspector's **critique**; the block is reported in `data.governance["status"]`. Check governance, not `output`.
- **Agents do expose an MCP endpoint** (`/agent/mcp/<id>`) — the previous "agents have no MCP server" note was wrong.
- **`inputs.reset()` restores the cached default**, it does not unset to `None`.

### Changed
- Tavily's canonical path is now `tavily/tavily-web-search/tavily`; the old `tavily/tavily-search-api` is **Legacy** — kept only as a "don't use" marker.
- Asset references moved to canonical three-segment paths throughout.
- Tooling: `publish` now defaults to the **`development`** branch (this repo's convention); `DOC_TO_REF` learned the new documentation paths.

---

## 2026-10-08 — Documentation catch-up; Arabic retired
**SDK 0.2.48** (unchanged) · **docs [`6d7ec31`](https://github.com/aixplain/sdk-documentation/commit/6d7ec31)** · 40 doc changes, 0 API drift

### Added
- **Files** on agents: a local folder uploads as one asset with its full tree; a public URL is streamed to the platform on `save()`.
- **RLM (Recursive Language Model)** in `models.md` — long-context analysis via an orchestrator/worker REPL sandbox.
- `references/evaluation.md` rewritten against the now-published `eval_experiment` / `agent_evaluator` / `eval_results_display` pages: real `Experiment` / `EvalCase` / `Dataset` / quality-gate workflow.

### Removed
- **Arabic (`.ar.md`) translations** — no longer maintained. Translation support was also removed from the refresh pipeline, so the validator now checks every shipped file.

### Reported upstream
- `sdk-documentation#271` (filed in the previous release) was **closed** — all three breaking doc bugs fixed.
- Filed `aiXplain#1170`: `Metric.create()` metrics score an **empty string** (`agent_response_data_fields` defaults to all-`False`, `create()` never sets it, so `measure()` posts `{"data": ""}`).
- Filed `sdk-documentation#288`: stale `reset_input()` example, `rlm.md` missing the `rag` mode, and `num_results` vs `top_k`. All three have since been fixed upstream.

---

## 2026-09-11 — SDK 0.2.48: breaking changes
**SDK 0.2.44 → 0.2.48** · **docs [`f5c016a`](https://github.com/aixplain/sdk-documentation/commit/f5c016a)** · 37 doc changes, 18 API diffs, 3 broken snippets

### Fixed — code that no longer runs
- **Inspectors redesigned.** The `aixplain.v2.inspector` config classes (`InspectorAction`, `EvaluatorConfig`, `EditorConfig`, …) were **removed from v2**. Guardrails are now plain strings and dicts: `aix.Inspector(action="abort", metric={"assetId": …, "prompt": …})`. Retries go **inside** the action dict — `action={"type":"rerun","max_retries":2,"on_exhaust":"abort"}`; top-level kwargs raise `TypeError`.
- `FileUploader` moved out of `aixplain.v2.file` (now `from aixplain.v2 import FileUploader`).
- `model.inputs` helpers renamed: `.required`, `dict(items())`, `.reset(k)`, `.reset()`.

### Fixed — two **silent** failures (no error raised)
- `agent.max_iterations = N` after construction never reaches the payload — set `agent.budget.max_iterations`.
- `generate_session_id()` / `create_session()` were removed and `session_id=` is **silently stripped** from a run, giving a stateless run with no warning. Use `aix.Session`.

### Added
- Sessions, Skills, Triggers, `Budget`, `aix.File`, pre-built marketplace guardrails (`aix.Inspector.get/search`), `response.data.governance`, Desktop deployment, MCP marketplace access.
- Field-verified runtime gotchas promoted into `SKILL.md` so they are always in context: `agent.save()` resets `agent.llm`; `Budget(max_cost=)` is persisted but only checked **between steps**; aiR index search honours `num_results` (`top_k` is ignored); `model.as_tool()` breaks video input.

---

## 2026-06-29 — Initial release
**SDK 0.2.44** · **docs [`dc57609`](https://github.com/aixplain/sdk-documentation/commit/dc57609)**

First version: a `SKILL.md` router plus per-domain references covering models, agents and team agents, tools and integrations, knowledge bases / RAG and memory, runtime governance, deployment and the access APIs, and a pattern cookbook. Validated against the live platform with a with-skill vs. baseline benchmark across transcription, RAG, web research and a governed team.
