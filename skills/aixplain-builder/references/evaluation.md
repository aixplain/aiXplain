# Evaluation — Evals & Metrics

New in SDK 0.2.48: `aix.Eval` (experiment runner) and `aix.Metric` (LLM-judge assets) for measuring agent quality.

> ⚠️ **SDK-only and undocumented.** Neither `aix.Eval` nor `aix.Metric` appears anywhere in aiXplain's published documentation as of 2026-09, and the generated Python API reference has no page for them. Everything below is verified by **introspecting the installed SDK** — signatures and method names are real, but the end-to-end workflow is inferred from those signatures, not from a documented example. Treat it as a starting point: run a small experiment first and confirm the shapes before relying on it. Don't present it to a user as settled API.

## Metrics — LLM-judge assets

A `Metric` is a marketplace asset you can fetch, run, or attach as a tool.

```python
metric = aix.Metric.get("<metric_id_or_path>")     # or: aix.Metric.search("relevance")
metric.list_actions()                               # discover actions
metric.run(data={...})                              # score something
tool = metric.as_tool()                             # attach to an agent like any other tool
```

### Create a custom judge

```python
m = aix.Metric.create(
    name="Answer relevance",
    llm_path="openai/gpt-4o",              # the judging model
    metric_description="Scores how well the answer addresses the question.",
    prompt_template="...",                  # your rubric prompt
    score_type="number",                    # or categories=[...] for labels
    start_number=1, end_number=5,           # numeric range
    # categories=["good","bad"], detailed_rubric={...}, instruction="...", auto_complete=False
)
```

Verified signature: `Metric.create(name, llm_path, metric_description="", prompt_template=None, score_type=None, instruction=None, start_number=None, end_number=None, categories=None, detailed_rubric=None, auto_complete=False, allowed_actions=None, **kwargs)`.

> Gotcha: `Metric.create` **silently discards `allowed_actions`**, and metrics are created on the `aixplain/custom-llm-prompt/aixplain` integration.

## Evals — running experiments

```python
ev = aix.Eval(
    cache_experiments=True,        # cache runs locally (default True)
    experiment_cache_dir=None,     # where to cache
    autosave_eval_runs=None,       # persist runs server-side
)
```

Verified methods on `aix.Eval`:

| Method | Purpose |
|---|---|
| `create_experiment(...)` | Define an experiment (agent(s) + cases + metrics). |
| `evaluate(...)` | Run the evaluation and score it. |
| `load_from_csv(...)` | Build eval cases from a CSV of inputs/expected outputs. |
| `list_cached_experiments()` | List locally cached experiments. |
| `load_cached_experiment(...)` | Reload a cached experiment instead of re-running. |

Supporting types live in `aixplain.v2.eval_experiment` — `Experiment`, `ExperimentRun`, `EvalCase`, `Dataset`, `AgentEvaluationRow`, `AgentEvaluationRun`, `ExperimentLocalCache` — and in `aixplain.v2.agent_evaluator` (`AgentEvaluationResultsChatbot`, `BASE_METRIC_PROMPT_TEMPLATE`, …). Inspect these before writing a workflow:

```python
import inspect, aixplain.v2.eval_experiment as ee
print(inspect.signature(ee.Experiment.__init__))
print(inspect.signature(aix.Eval.create_experiment))
```

## How to use this responsibly

Because this surface is undocumented, the honest play when a user asks for agent evaluation is:

1. Say that aiXplain ships an evaluation API in the SDK but hasn't documented it yet.
2. Introspect the exact signatures in *their* installed version (they may differ from 0.2.48) and build from that.
3. Start with one metric and a handful of cases, confirm the result shape, then scale up.
4. If the API misbehaves in a way that looks aiXplain-caused, follow the "Report aiXplain issues" habit in `SKILL.md`.

For governance/guardrails at runtime (as opposed to offline scoring), see `references/governance.md`.
