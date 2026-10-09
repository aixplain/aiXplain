---
sidebar_label: eval_experiment
title: aixplain.v2.eval_experiment
---

`from aixplain import EXPERIMENT_COMPARISON_COL_RUN_CREATED_AT, EXPERIMENT_COMPARISON_COL_RUN_INDEX, Experiment, ExperimentLocalCache, ExperimentRun, ExperimentRunDiff, ExperimentRunDiffCase, ExperimentRunDiffCaseList, default_experiment_cache_dir`


Experiment definitions and local filesystem cache for agent evaluations.

#### default\_experiment\_cache\_dir

```python
def default_experiment_cache_dir() -> Path
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L74)

Return the default directory for experiment cache files.

### ExperimentRunDiffCase Objects

```python
@dataclass
class ExperimentRunDiffCase()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L309)

One ``case_index`` outcome from `Experiment.diff`.

**Attributes**:

- `case_index` - Dataset row index for the compared sample.
- `baseline_value` - Metric score on the baseline run.
- `candidate_value` - Metric score on the candidate run.
- `baseline_output` - Primary agent output on the baseline run (``output``, else ``agent_response``).
- `candidate_output` - Primary agent output on the candidate run.

### ExperimentRunDiffCaseList Objects

```python
class ExperimentRunDiffCaseList(UserList)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L336)

List-like container of `ExperimentRunDiffCase` with `to_dataframe`.

#### to\_dataframe

```python
def to_dataframe() -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L339)

One row per case (columns match `ExperimentRunDiffCase` fields).

### ExperimentRunDiff Objects

```python
@dataclass
class ExperimentRunDiff()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L351)

Per-case comparison of two `ExperimentRun` results on one metric (see `Experiment.diff`).

``regressions``, ``improvements``, and ``unchanged`` are `ExperimentRunDiffCaseList` instances
(list-like) with `to_dataframe` for each bucket, for example
``experiment_diff.unchanged.to_dataframe()``.

#### summary

```python
def summary() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L364)

Return a short human-readable tally (for example ``3 regressions, 1 improvement, 196 unchanged``).

### Experiment Objects

```python
@dataclass
class Experiment()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L463)

Definition of an evaluation (dataset, agent snapshots, metric snapshots) plus appended runs.

Use `runs_comparison_dataframe` to tabulate each `ExperimentRun`, and
`plot_runs_regression` for a line chart (with optional polynomial trend) across runs.
Use `diff` to classify per-case changes between two runs on one metric.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L482)

Validate required fields after construction.

#### bind\_executor

```python
def bind_executor(executor: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L491)

Attach an `Eval` (e.g. after loading from cache).

#### run

```python
def run(*,
        agents: Optional[Union[Agent, Sequence[Agent]]] = None,
        metrics: Optional[Sequence[Metric]] = None,
        run_metadata: Optional[Dict[str, Any]] = None,
        **agent_run_kwargs: Any) -> ExperimentRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L495)

Execute the experiment and append a new `ExperimentRun` (does not replace prior runs).

#### diff

```python
def diff(*,
         baseline: ExperimentRun,
         candidate: ExperimentRun,
         metric_prefix: str,
         categorical_order: Optional[Sequence[Any]] = None,
         agent_name: Optional[str] = None) -> ExperimentRunDiff
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L541)

Compare two runs of this experiment on one metric, keyed by ``case_index``.

Each ``case_index`` must map to exactly one row **after** optional filtering. Baseline and
candidate must belong to this `Experiment` (``run.parent is self``). Agent run
failures are not treated specially; missing metric scores still raise.

When an evaluation uses multiple agents per case, there are multiple rows per
``case_index``; pass ``agent_name`` to restrict the diff to one agent (matched as a string
against `agent_name`).

Numeric mode (default): reads ``metrics[metric_prefix]['score']`` on each side and
compares as floats (strings are parsed when possible). Lower is worse, higher is better.

Categorical mode: pass ``categorical_order`` as a sequence from **worst to best**; scores
must appear in that list. Better means a higher index in ``categorical_order``.

**Arguments**:

- `baseline` - Earlier `ExperimentRun`.
- `candidate` - Later `ExperimentRun`.
- `metric_prefix` - Key under `metrics`.
- `categorical_order` - When set, compare categorical scores by rank in this list
  (first element = worst, last = best).
- `agent_name` - When set, only rows for this agent name are compared per case.
  

**Returns**:

  `ExperimentRunDiff` with ``regressions``, ``improvements``, and ``unchanged``.

#### runs\_comparison\_dataframe

```python
def runs_comparison_dataframe(*,
                              human_column_names: bool = True) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L630)

Tabular view of each `ExperimentRun` for trend / regression plots.

Rows are ordered by ``run.created_at``. By default columns use readable titles
(for example ``"Run index"``, ``"Total credits (sum)"``, ``"Pass rate (m1)"``,
``"Average metric: m1 / score"``, ``"agent_a: Credits used (sum)"``). Set
``human_column_names=False`` for the legacy machine-oriented names
(``run_index``, ``total_cost``, ``metric_pass_rate__m1``, …).

**Arguments**:

- `human_column_names` - When True (default), column names are chosen for notebooks
  and charts; when False, internal stable keys are preserved.
  

**Returns**:

  Empty DataFrame when `runs` is empty.

#### plot\_runs\_regression

```python
def plot_runs_regression(*,
                         y: Union[str, Sequence[str]],
                         x: Optional[str] = None,
                         human_column_names: bool = True,
                         show_trendline: bool = True,
                         trendline_degree: int = 1,
                         show_trendline_in_legend: bool = False,
                         title: Optional[str] = None,
                         figsize: Optional[Tuple[float, float]] = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L654)

Line chart of one or more series across experiment runs, with optional polynomial fit.

Fits the trend against run order (0, 1, …) while the chart **x-axis** uses the
column given by ``x``. When ``human_column_names`` is True (default), ``x`` defaults
to `EXPERIMENT_COMPARISON_COL_RUN_INDEX` (``"Run index"``); otherwise it
defaults to ``"run_index"``.

**Arguments**:

- `y` - Column name(s) from `runs_comparison_dataframe` — for example
  ``"Total credits (sum)"``, ``"Avg credits per evaluation row"``,
  ``"Pass rate (my_metric)"``, or ``"Average metric: m1 / score"`` when
  ``human_column_names`` is True.
- `x` - Column to use as x-axis; if omitted, uses ``Run index`` or ``run_index``
  depending on ``human_column_names``.
- `human_column_names` - Passed to `runs_comparison_dataframe` (default True).
- `show_trendline` - When True (default), overlay a least-squares polynomial per ``y``.
- `trendline_degree` - Polynomial degree (at least ``1``); capped by run count.
- `show_trendline_in_legend` - When False (default), dashed trend lines are omitted from
  the legend so only the data series names appear (e.g. ``Total credits (sum)``).
- `title` - Plot title; default describes the experiment and ``y``.
- `figsize` - Optional ``(width, height)`` in inches for layout sizing.
  

**Returns**:

  A `plotly.graph_objects.Figure`.
  

**Raises**:

- `ValidationError` - If there are no runs or requested columns are missing.
  

**Notes**:

  Requires plotly (``pip install plotly``).

#### to\_cache\_payload

```python
def to_cache_payload() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L780)

Serialize experiment and all runs for the local cache.

#### from\_cache\_payload

```python
@classmethod
def from_cache_payload(cls,
                       data: Dict[str, Any],
                       *,
                       executor: Any = None) -> Experiment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L804)

Restore an experiment from `to_cache_payload` JSON structure.

### ExperimentRun Objects

```python
@dataclass
class ExperimentRun()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L836)

One execution of an `Experiment` with concrete `AgentEvaluationRun` results.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L845)

Validate required fields after construction.

### ExperimentLocalCache Objects

```python
class ExperimentLocalCache()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L853)

Filesystem-backed store for `Experiment` (including all `ExperimentRun` records).

#### \_\_init\_\_

```python
def __init__(base_dir: Union[str, Path]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L856)

Create a cache rooted at ``base_dir`` (created if missing).

#### path\_for

```python
def path_for(experiment_id: str) -> Path
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L861)

Return the JSON path for a given experiment id.

#### save

```python
def save(experiment: Experiment) -> Path
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L866)

Write ``experiment`` to disk atomically.

#### list\_experiments

```python
def list_experiments() -> List[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L876)

Summarize cached experiments (id, creation time, metadata, run count).

#### load\_experiment

```python
def load_experiment(experiment_id: str, *, executor: Any = None) -> Experiment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_experiment.py#L896)

Load a full experiment and runs from the cache.

