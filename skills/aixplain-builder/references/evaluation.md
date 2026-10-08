# Evaluation — Evals & Metrics

[Pieces](#the-pieces) · [End to end](#end-to-end) · [Datasets](#datasets--cases) · [Metrics](#metrics--llm-judge-assets) · [Running](#running-an-evaluation) · [Experiments](#experiments--tracking-runs-over-time) · [Reading results](#reading-results) · [Gotchas](#gotchas)

`aix.Eval` runs a dataset of queries through one or more agents, scores each answer with LLM-judge `aix.Metric` tools, and returns a structured, tabular result you can filter, gate, plot, and diff across runs. Offline scoring — not a runtime guardrail.

> **Now documented (as of 0.2.48).** The generated Python API reference has pages for `aixplain.v2.agent_evaluator`, `aixplain.v2.eval_experiment`, and `aixplain.v2.eval_results_display`, all listed in the docs sidebar. The **prose guides still say nothing** about evaluation — there is no tutorial, no worked example, and no mention of `Eval`/`Metric` outside the API reference. Everything below is cross-checked against **installed 0.2.48 by introspection**; where the reference text and the code disagree, the code wins and the gap is flagged.

## The pieces

| Object | Where it comes from | What it is |
|---|---|---|
| `Eval` | `aix.Eval` | The executor. Runs cases × agents, calls the metrics, owns the experiment cache. |
| `Metric` | `aix.Metric` | A judge asset — a `Tool` subclass backed by the custom-LLM-prompt integration. |
| `EvalCase` | `from aixplain.v2 import EvalCase` | One example: `query`, optional `reference`, optional `metadata`. |
| `Dataset` | `from aixplain.v2 import Dataset` | `name` + `cases` (+ `description`). Build with `from_queries` / `from_csv`. |
| `AgentEvaluationRow` | result object | One evaluated (case, agent) pair, with nested `metrics`. |
| `AgentEvaluationRun` | result of `evaluate()` | The collection of rows + all the analysis helpers. |
| `Experiment` / `ExperimentRun` | `from aixplain.v2 import Experiment` | A named, cached definition plus its appended runs, for trend/regression tracking. |

> **Only `Eval` and `Metric` are on the client.** `aix.Dataset`, `aix.EvalCase` and `aix.Experiment` do **not** exist — they raise `AttributeError`. Import those from `aixplain.v2` directly. (`aix.Metric` is a client-bound subclass of `aixplain.v2.agent_evaluator.Metric`, so `is` comparisons against the module class fail while `issubclass` holds.)

## End to end

```python
from aixplain import Aixplain
from aixplain.v2 import Dataset, EvalCase

aix = Aixplain(api_key="...")

# 1. A dataset
dataset = Dataset(name="support-smoke", cases=[
    EvalCase(query="How do I reset my password?", reference="Use the Forgot password link."),
    EvalCase(query="What are your business hours?", reference="9-5 Mon-Fri."),
])

# 2. A judge
relevance = aix.Metric.create(
    name="relevance",
    llm_path="openai/gpt-4o",
    metric_description="Scores how well the answer addresses the question.",
    score_type="numeric", instruction="Score answer relevance.",
    start_number=1, end_number=5,
)
relevance.agent_response_data_fields.query = True     # REQUIRED — see gotchas
relevance.agent_response_data_fields.output = True
relevance.threshold = 3.0                             # score > 3.0 -> metric_pass

# 3. Run it
ev  = aix.Eval()
run = ev.evaluate(agents=[agent_a, agent_b], dataset=dataset, metrics=[relevance])

# 4. Read it
print(run.summarize_by_agent())
print(run.metric_pass_rates())
run.to_dataframe().to_csv("results.csv", index=False)
```

## Datasets & cases

```python
EvalCase(query="...", reference=None, metadata=None)   # query required; the rest optional
Dataset(name="...", cases=[...], description=None)

Dataset.from_queries(["q1", "q2"], name="smoke")       # name is keyword-only
Dataset.from_csv("cases.csv", name=None, description=None,
                 query_column="query", reference_column="reference",
                 metadata_columns=None, **read_csv_kwargs)
```

`reference` is ground truth for your own scoring; `metadata` keys land on each result row as `case_meta__<key>`. `from_csv` raises `ValidationError` if the query column is missing or any row's query is empty; a header-only CSV yields an empty `cases` list. `Dataset` supports `len()` and iteration.

## Metrics — LLM-judge assets

A `Metric` is a marketplace asset: fetch an existing one, or create your own judge.

```python
metric = aix.Metric.get("<metric_id>")       # or aix.Metric.search("relevance")
metric.list_actions()
tool = metric.as_tool()                       # attach to an agent like any other tool
```

### Create a custom judge

Verified signature:

```
Metric.create(name, llm_path, metric_description="", prompt_template=None,
              score_type=None, instruction=None, start_number=None, end_number=None,
              categories=None, detailed_rubric=None, auto_complete=False,
              allowed_actions=None, **kwargs)
```

Give it **either** a ready-made `prompt_template` **or** generation parameters:

| `score_type` | Also required | Judge returns |
|---|---|---|
| `"numeric"` | `instruction`, `start_number`, `end_number` | `{"reasoning": str, "score": float}` |
| `"categorical"` | `instruction`, non-empty `categories` | `{"reasoning": str, "score": <one of categories>}` |
| `"boolean"` | `instruction` | `{"reasoning": str, "score": bool}` |

Anything else raises `ValidationError`. A non-blank `prompt_template` is used as-is and **all** generation parameters are ignored. Metrics are created on the `aixplain/custom-llm-prompt/aixplain` integration and `save()`d immediately.

### Thresholds

```python
metric.threshold = 3.0                 # numeric: metric_pass = score > threshold
metric.threshold = ["good", "great"]   # categorical: metric_pass = score in list
```

Setting a threshold adds a boolean `metric_pass` to every successful metric row, which is what `metric_pass_rates()` and the `__metric_pass` columns aggregate.

> `Metric.create` does **not** take `threshold` — assign it on the returned object (or on one you `get()`). Validation only runs in `__post_init__`, so a bad value assigned afterwards (e.g. a bare `bool`) is accepted silently and misbehaves at scoring time.

> `Metric.initialize(name, prompt_template, llm_path, ...)` is **deprecated** — it exists only to preserve the historical argument order. Use `create`.

## Running an evaluation

```python
ev = aix.Eval(
    cache_experiments=True,        # keyword-only; write Experiment snapshots to disk
    experiment_cache_dir=None,     # default: ~/.cache/aixplain/experiments (XDG/LOCALAPPDATA aware)
    autosave_eval_runs=None,       # DEPRECATED alias for cache_experiments
)

run = ev.evaluate(agents, dataset, metrics=None, **agent_run_kwargs)
```

`agents` is one `Agent` or a sequence. Extra kwargs are forwarded to every `agent.run()` call (so `timeout=`, `variables=`, etc. apply). The result has one row per (case, agent). **Failures are recorded, not raised** — a failed agent run yields a row with `agent_run_failed=True` and its metrics marked `metric_skipped`; a failed metric yields `metric_error` on that bucket only.

> **It is strictly serial.** `evaluate` is a plain nested loop — no threads, no async, no batching. Cost is `len(cases) × len(agents) × (1 agent run + len(metrics) judge runs)` round-trips, one at a time. Size your first dataset accordingly.

## Experiments — tracking runs over time

An `Experiment` pins a dataset plus agent/metric snapshots so you can re-run it later and compare.

```python
exp  = ev.create_experiment(agents, dataset, metrics=None, metadata={"branch": "main"})
r1   = exp.run()                                   # appends an ExperimentRun
# ... change the agent's prompt, save() ...
r2   = exp.run()                                   # appends another; r1 is kept

exp.runs_comparison_dataframe()                    # one row per run
exp.plot_runs_regression(y="Pass rate (relevance)")  # plotly; needs `pip install plotly`

d = exp.diff(baseline=r1, candidate=r2, metric_prefix="relevance")
print(d.summary())                                 # "3 regressions, 1 improvement, 196 unchanged"
d.regressions.to_dataframe()
```

`Experiment.run(*, agents=None, metrics=None, run_metadata=None, **agent_run_kwargs)` — all keyword-only. `diff` is keyed by `case_index`, needs exactly one row per case after filtering (pass `agent_name=` when several agents ran), reads `metrics[metric_prefix]["score"]`, and takes `categorical_order=[worst, …, best]` for non-numeric scores.

Cache round-trip:

```python
ev.list_cached_experiments()                 # [{id, created_at, metadata, run_count}, ...]
exp = ev.load_cached_experiment("<id>")      # binds this Eval as executor
exp.run(agents=[agent])                      # REQUIRED: live agents are not restored
```

> A cached experiment stores **snapshots** (`to_dict()`), not live objects. Calling `exp.run()` on a reloaded experiment without `agents=` raises `ValidationError: No agents available to run`. `Experiment.bind_executor(ev)` covers the other half if you restored via `Experiment.from_cache_payload`.

## Reading results

`AgentEvaluationRun` supports `len()`, iteration and truthiness, and carries the whole analysis surface:

| Method | Returns |
|---|---|
| `to_dataframe()` | Long-format DataFrame, one row per (case, agent). |
| `to_json_records()` | One dict per row; metrics flattened as `prefix__key`. |
| `summarize_by_agent()` | Per-agent counts, failures, numeric metric means, pass rates. |
| `metric_pass_rates()` | `{prefix: {passed, evaluated, pass_rate, by_agent}}`. Empty without thresholds. |
| `run_summary(include_executive_summary=True, …)` | Aggregate stats (`total_cost`, `total_time_seconds`, `agent_failure_rate`, `total_tool_calls`, `metric_highlights`, `per_agent`, …) + optional LLM narrative. |
| `evaluate_quality_gates(metric_score_criteria=…, run_aggregate_gates=…)` | CI-style pass/fail with `by_agent`, `all_agents_pass`, and a `debug_dataframe`. |
| `compare_agents_side_by_side()` / `pivot_agents_wide()` | One row per case, agents as columns. |
| `case_rows(i)` / `case_comparison_html(i)` / `subset_for_case(i)` | Drill into one case. |
| `filter(...)` / `filter_base(...)` / `filter_where(pred)` | New run with matching rows. |
| `metric_prefixes()` / `metric_inner_key_is_numeric()` | Discover and type-check metric keys. |
| `plot_metric_by_agent()` (+ `_mean_` / `_enum_` variants) | plotly figures. |
| `to_llm_context(layout="markdown", …)` / `chatbot()` / `executive_summary()` | LLM-ready text, Q&A, narrative. |

Each row's `metrics` is `{prefix: {...}}` where the prefix is the metric tool's `name`, else its `id`, else `metric_<n>`. Inside a bucket: `metric_status`, `metric_completed`, the judge's own JSON keys (`reasoning`, `score`), `metric_pass` when a threshold is set, `metric_error`/`metric_error_type` on failure, `metric_skipped`/`metric_skip_reason` when the agent run failed.

### Filtering and gates

```python
bad = run.filter(metric="relevance", op="lt", value=3)          # ops: lt le gt ge eq ne in
slow = run.filter(metric="latency", op="gt", value=30)          # reserved: run_time/latency, used_credits/credits_used/cost

report = run.evaluate_quality_gates(
    metric_score_criteria={"relevance": 3.0, "tone": ["polite", "neutral"]},
    run_aggregate_gates={"agent_failure_rate": {"bound": 0.05, "operator": "lt"}},
)
assert report["all_agents_pass"]
```

Aggregate gates are evaluated **per agent** against that agent's slice. A metric gate whose rows were all skipped **fails** — nothing was verified.

### CSV round-trip

```python
run.to_dataframe().to_csv("results.csv", index=False)
run2 = aix.Eval.load_from_csv("results.csv")        # classmethod; rebuilds the structured run
```

`load_from_csv` normalizes dtypes by default and splits flat `prefix__field` columns back into `metrics`; unknown columns are ignored. For a raw frame instead of a structured run, `aixplain.v2.eval_results_display` offers `load_eval_csv`, `normalize_eval_results_dataframe`, `pivot_agents_wide`, `summarize_by_agent`, `case_rows`, and `case_comparison_html`.

### LLM-backed insights

`executive_summary()`, `run_summary()` and `chatbot()` need a model. Without one they fall back to `AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH` (`openai/gpt-5.4-mini/openai`), which is only resolvable after you bind your client:

```python
from aixplain.v2 import AgentEvaluationRun
AgentEvaluationRun.configure_insights(aix)     # so Model.get uses your key and URLs
AgentEvaluationRun.ensure_insight_model_loaded()

bot = run.chatbot()
print(bot.ask("Which agent regressed on refund questions, and why?"))
bot.reset_conversation()
```

Without `configure_insights`, `executive_summary()` degrades to a deterministic template. `run_summary(include_executive_summary=False)` skips the extra model call entirely.

## Gotchas

> **The judge gets an empty prompt unless you flip the field flags.** The API reference's `Eval` docstring says each metric is invoked "with `run` payload `data` containing at least `output` … and `reference`." **That is wrong.** The code calls `metric.measure(result.data)`, which builds a flat string from `metric.agent_response_data_fields` — and all three flags (`query`, `trace`, `output`) default to **`False`**, so a freshly `create`d metric sends an empty `data` string. Set `metric.agent_response_data_fields.output = True` (plus `query` / `trace` as the rubric needs) before evaluating.

> **`reference` never reaches the metric.** There is no code path from `EvalCase.reference` into the metric payload — it is carried on the result row for *your* analysis only. For reference-based judging, put the expected answer in the query text or use `metric.additional_input_prompt`.

> **`Metric.create` discards `allowed_actions` and `**kwargs`** — the first statement of the body is literally `del allowed_actions, kwargs`. The docs now admit this ("currently unused" / "reserved for future use"), but it is silent, not a warning. `create` also leaves `score_type`, `threshold` and `agent_response_data_fields` unset on the returned object.

> **Row credits come straight from `result.used_credits`**, which agent runs frequently report as `0.0` (see `references/agents.md`). `run_summary()["total_cost"]` inherits that understatement; treat eval cost figures as a lower bound.

> **plotly is not a dependency.** Every `plot_*` helper and `Experiment.plot_runs_regression` needs `pip install plotly`, plus `nbformat>=4.2.0` for inline notebook display.

When the installed version differs from 0.2.48, introspect before trusting any of the above:

```python
import inspect, aixplain.v2.agent_evaluator as ae
print(inspect.signature(ae.Eval.evaluate), inspect.signature(ae.Metric.create))
```

If something here misbehaves in a way that looks aiXplain-caused, follow the "Report aiXplain issues" habit in `SKILL.md`.

For governance/guardrails at runtime (blocking or rewriting a live answer) rather than offline scoring, see `references/governance.md`.
