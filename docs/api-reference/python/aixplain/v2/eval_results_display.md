---
sidebar_label: eval_results_display
title: aixplain.v2.eval_results_display
---

Display helpers for :class:`~aixplain.v2.agent_evaluator.AgentEvaluationRun` results.

Load CSV exports (from :meth:`~aixplain.v2.agent_evaluator.AgentEvaluationRun.to_dataframe`),
pivot long rows into side-by-side wide tables, summarize metrics by agent, and build
simple HTML for notebook widgets.

#### guess\_compare\_value\_columns

```python
def guess_compare_value_columns(df: pd.DataFrame) -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L39)

Columns to compare by default: ``output`` plus flattened metric payload columns.

#### load\_eval\_csv

```python
def load_eval_csv(path: Union[str, Path],
                  **read_csv_kwargs: Any) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L52)

Load a CSV written from evaluator results (e.g. ``df.to_csv(...)``).

For a structured :class:`~aixplain.v2.agent_evaluator.AgentEvaluationRun`, use
:meth:`~aixplain.v2.agent_evaluator.Eval.load_from_csv` instead.

**Arguments**:

- `path` - Path to the CSV file.
- `**read_csv_kwargs` - Forwarded to :func:`pandas.read_csv`.
  

**Returns**:

  DataFrame in the same long shape as :meth:`AgentEvaluationRun.to_dataframe`.

#### pivot\_agents\_wide

```python
def pivot_agents_wide(df: pd.DataFrame,
                      value_columns: Optional[Sequence[str]] = None,
                      *,
                      include_query: bool = True,
                      include_reference: bool = True) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L68)

Pivot long evaluator output so each case is one row and agents appear as columns.

Column index is a MultiIndex. Pivoted fields use ``(value_field, agent_name)``.
``query`` and ``reference`` use ``(field_name, &quot;&quot;)`` so they share two levels
and concatenate cleanly with pivoted columns.

**Arguments**:

- `df` - Long-format evaluation results.
- `value_columns` - Columns to pivot; defaults to :func:``0.
- ``1 - If True and ``query`` is present, join one query per ``case_index``.
- ``6 - Same for ``reference``.
  

**Returns**:

  Wide DataFrame indexed by ``case_index``.
  

**Raises**:

- ``1 - If required columns are missing or pivot inputs are invalid.

#### summarize\_by\_agent

```python
def summarize_by_agent(df: pd.DataFrame) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L144)

Per-agent row counts, failure counts, and means of numeric metric columns.

Non-numeric metric columns (e.g. string scores) are omitted from means.
Columns ending with ``__metric_pass`` add ``pass_rate__``, ``n_passed__``,
and ``n_evaluated__`` fields (threshold pass/fail) per agent.
``agent_run_failed`` is coerced from strings when loaded from CSV.

**Arguments**:

- ``0 - Long-format evaluation results.
  

**Returns**:

  One row per ``agent_name``.
  

**Raises**:

- ``3 - If ``agent_name`` is missing.

#### case\_rows

```python
def case_rows(df: pd.DataFrame, case_index: int) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L199)

Return long-format rows for a single ``case_index``.

#### case\_comparison\_html

```python
def case_comparison_html(df: pd.DataFrame,
                         case_index: int,
                         *,
                         max_output_chars: Optional[int] = 8000) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/eval_results_display.py#L204)

Build a simple HTML table comparing agents for one case (for notebooks).

