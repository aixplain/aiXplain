---
sidebar_label: agent_evaluator
title: aixplain.v2.agent_evaluator
---

Agent evaluation utilities for aiXplain v2 SDK.

Provides a minimal executor that runs a :class:`Dataset` of :class:`EvalCase`
rows through one or more :class:`~aixplain.v2.agent.Agent` instances, runs optional
:class:`Metric` instances, and returns a structured :class:`AgentEvaluationRun`.
Use :meth:`AgentEvaluationRun.to_dataframe` for tabular export and
:meth:`Eval.load_from_csv` to reload from disk.

### MetricResponse Objects

```python
@dataclass_json

@dataclass(repr=False)
class MetricResponse(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L74)

Result for a metric tool run after validation and cleanup.

Extends Result with optional metric-specific fields populated by
post-processing (response validation and cleanup).

### AgentResponseDataFields Objects

```python
@dataclass_json

@dataclass
class AgentResponseDataFields()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L86)

Fields that are required from AgentResponseData.

#### give\_codes

```python
def give_codes() -> Dict[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L93)

Return placeholder codes for query, trace, and output fields.

#### give\_metric\_input

```python
def give_metric_input(agent_response: AgentResponseData) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L104)

Build metric input string from agent response fields.

### Metric Objects

```python
@dataclass_json

@dataclass(repr=False)
class Metric(Tool)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L118)

Tool wrapper for creating a tool from a metric integration.

Adds optional pre-processing before creation (placeholder) and
post-processing (response validation and cleanup) when running.

Optional :attr:`threshold` marks each evaluated row with ``metric_pass`` when
set: for string/enum scores use a list of passing values; for numeric scores
use a single float (pass when ``score &gt; threshold``).

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L140)

Initialize metric and validate threshold.

#### create

```python
@classmethod
def create(cls,
           name: str,
           llm_path: str,
           metric_description: str = "",
           prompt_template: Optional[str] = None,
           score_type: Optional[str] = None,
           instruction: Optional[str] = None,
           start_number: Optional[float] = None,
           end_number: Optional[float] = None,
           categories: Optional[list[str]] = None,
           detailed_rubric: Optional[dict] = None,
           auto_complete: bool = False,
           allowed_actions: Optional[List[str]] = None,
           **kwargs: Any) -> "Metric"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L185)

Create and persist a :class:`Metric` backed by the custom LLM prompt integration.

Provide either a ready-made ``prompt_template`` **or** generation parameters
(``score_type``, ``instruction``, and type-specific fields). When
``prompt_template`` is a non-empty string, it is used as-is and generation
parameters are ignored.

**Arguments**:

- `name` - Name of the metric tool.
- ``0 - The path or ID of the LLM to use.
- ``1 - Optional description of the metric tool.
- ``2 - Full prompt template for the LLM. If omitted or blank,
  a template is built via :meth:``3.
- ``4 - One of ``numeric``, ``categorical``, or ``boolean`` (required
  when ``prompt_template`` is not set).
- ``3 - Task instruction embedded in the generated template (required
  when ``prompt_template`` is not set).
- ``6 - Scale lower bound for ``numeric`` metrics.
- ``9 - Scale upper bound for ``numeric`` metrics.
- ``2 - Allowed labels for ``categorical`` metrics.
- ``5 - Optional extra rubric lines appended to the rubric section.
- ``6 - Reserved for future use; passed through to template generation.
- ``7 - Optional list of allowed actions (currently unused).
- ``8 - Reserved for future :class:``9 construction options.
  

**Returns**:

  The saved :class:`Metric` instance.
  

**Raises**:

- ``1 - When neither a usable template nor valid generation inputs are given.

#### initialize

```python
@classmethod
def initialize(cls,
               name: str,
               prompt_template: str,
               llm_path: str,
               metric_description: str = "",
               allowed_actions: Optional[List[str]] = None,
               **kwargs: Any) -> "Metric"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L279)

Deprecated. Use :meth:`create` instead.

Preserves the historical argument order ``(name, prompt_template, llm_path)``.

#### trim\_and\_load\_json

```python
@staticmethod
def trim_and_load_json(input_string: str) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L321)

Extract and parse JSON from a string response.

#### measure

```python
def measure(agent_response: AgentResponseData) -> MetricResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L342)

Run metric tool with agent response data.

#### handle\_run\_response

```python
def handle_run_response(response: MetricResponse,
                        **kwargs: Any) -> MetricResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L367)

Validate and cleanup response, then return a MetricResponse.

#### metric\_pass\_rates\_from\_rows

```python
def metric_pass_rates_from_rows(
        rows: Sequence[AgentEvaluationRow]) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L984)

Aggregate pass counts and rates for each metric prefix that has ``metric_pass``.

Only rows with a coercible boolean ``metric_pass`` under a prefix are counted.
Structure::

\{
&quot;&lt;prefix&gt;&quot;: \{
&quot;passed&quot;: int,
&quot;evaluated&quot;: int,
&quot;pass_rate&quot;: float,
&quot;by_agent&quot;: \{
&quot;&lt;agent_name&gt;&quot;: \{&quot;passed&quot;: int, &quot;evaluated&quot;: int, &quot;pass_rate&quot;: float},
...
},
},
...
}

**Arguments**:

- `rows` - Evaluation rows (typically :attr:`AgentEvaluationRun.rows`).
  

**Returns**:

  Empty dict when no ``metric_pass`` fields are present.

### EvalCase Objects

```python
@dataclass
class EvalCase()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1087)

One evaluation example (input plus optional reference and metadata).

**Attributes**:

- `query` - Passed to ``agent.run(query, **agent_run_kwargs)``.
- `reference` - Optional ground truth or expected value for metrics.
- `metadata` - Optional extra fields merged into the result row as ``case_meta__&lt;key&gt;``.

### Dataset Objects

```python
@dataclass
class Dataset()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1102)

Named evaluation dataset: a list of :class:`EvalCase` with optional description.

Use :meth:`from_csv` or :meth:`from_queries` to build common shapes, or construct
with ``Dataset(name=..., cases=[EvalCase(...), ...])``.

#### \_\_iter\_\_

```python
def __iter__() -> Iterator[EvalCase]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1113)

Iterate over evaluation cases.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1117)

Return number of evaluation cases.

#### from\_queries

```python
@classmethod
def from_queries(cls,
                 queries: Sequence[str],
                 *,
                 name: str,
                 description: Optional[str] = None) -> Dataset
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1122)

Build a dataset from plain query strings (one :class:`EvalCase` per string).

#### from\_csv

```python
@classmethod
def from_csv(cls,
             path: Union[str, Path, Any],
             *,
             name: Optional[str] = None,
             description: Optional[str] = None,
             query_column: str = "query",
             reference_column: Optional[str] = "reference",
             metadata_columns: Optional[Sequence[str]] = None,
             **read_csv_kwargs: Any) -> Dataset
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1137)

Build a :class:`Dataset` from a CSV with at least a query column.

**Arguments**:

- `path` - CSV path or file-like accepted by :func:`pandas.read_csv`.
- `name` - Human-readable name; defaults to the path stem when ``path`` is
  a :class:`str` or :class:`pathlib.Path`, otherwise ``&quot;dataset&quot;``.
- `path`0 - Optional longer description of the dataset.
- `path`1 - Column name used as :attr:`path`2.
- `path`3 - Column for :attr:`path`4, or ``None`` to skip.
- `path`7 - Optional column names merged into each case&#x27;s ``metadata``.
- `pandas.read_csv`0 - Forwarded to :func:`pandas.read_csv`.
  

**Returns**:

  Dataset with ``cases`` populated; header-only CSV yields an empty ``cases`` list.
  

**Raises**:

- `pandas.read_csv`6 - If the query column is missing or a row has an empty query.

### AgentEvaluationRow Objects

```python
@dataclass
class AgentEvaluationRow()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1199)

One evaluated (case, agent) pair including nested metric tool fields.

``metrics`` maps each metric tool prefix (see :func:`_metric_prefix`) to
a dict of flattened keys (for example ``metric_status``, ``score``,
``metric_pass`` when the tool defines a :attr:`~Metric.threshold`) matching
the former ``&lt;prefix&gt;__&lt;key&gt;`` column names without the ``&lt;prefix&gt;__`` prefix.

``per_asset_stats`` maps a stable asset label (``type`` and ``name`` from each
step&#x27;s ``unit``, joined as ``type:name``, or breakdown keys from
``execution_stats`` when steps are absent) to ``run_time``, ``used_credits``,
and ``n_steps`` aggregates.

#### metric\_value

```python
def metric_value(tool_prefix: str, key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1234)

Return ``metrics[tool_prefix][key]`` when present, else ``None``.

### AgentEvaluationRun Objects

```python
@dataclass
class AgentEvaluationRun()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1240)

Structured output of :meth:`Eval.evaluate`.

Convenience methods (filtering, LLM-ready text, summaries, HTML, optional plots,
and :meth:`chatbot`) build on :meth:`to_dataframe` and
:mod:`aixplain.v2.eval_results_display`.

Default LLM-backed insight features (:meth:`executive_summary`, :meth:`chatbot`
without ``model=``) resolve the model at :attr:`DEFAULT_INSIGHT_MODEL_PATH`
using the client bound by :meth:`configure_insights`. After creating
``aix = Aixplain(...)``, call ``AgentEvaluationRun.configure_insights(aix)``
so :meth:`chatbot`4 with the path-style model id uses the same API key and
URLs as your agents. :attr:`chatbot`5 stays ``None`` until the
first successful resolution; call :meth:`chatbot`8 to
populate it without generating a summary.

#### configure\_insights

```python
@classmethod
def configure_insights(cls, client: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1264)

Bind default insight model resolution to an :class:`~aixplain.v2.core.Aixplain` client.

Clears any cached default model so the next resolution uses ``client.Model``.

**Arguments**:

- `client` - An initialized ``Aixplain`` instance (same one used for
  ``client.Agent.get``, ``client.Model``, etc.).

#### ensure\_insight\_model\_loaded

```python
@classmethod
def ensure_insight_model_loaded(cls) -> Optional[Model]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1277)

Resolve and cache :attr:`DEFAULT_INSIGHT_MODEL` from :attr:`DEFAULT_INSIGHT_MODEL_PATH`.

Call after :meth:`configure_insights`. Idempotent when a model is already cached.

**Returns**:

  The cached :class:`~aixplain.v2.model.Model`, or ``None`` if get/search fails.

#### \_\_iter\_\_

```python
def __iter__() -> Iterator[AgentEvaluationRow]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1328)

Iterate over evaluation rows.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1332)

Return number of evaluation rows.

#### \_\_bool\_\_

```python
def __bool__() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1336)

Return True if there are evaluation rows.

#### to\_dataframe

```python
def to_dataframe() -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1340)

Materialize rows into a long-format :class:`pandas.DataFrame` (CSV / pivot helpers).

#### compare\_agents\_side\_by\_side

```python
def compare_agents_side_by_side(
        *,
        value_columns: Optional[Sequence[str]] = None,
        include_query: bool = True,
        include_reference: bool = False) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1395)

Pivot to one row per case with agents in columns; see :func:`compare_agents_side_by_side`.

#### filter\_base

```python
def filter_base(*,
                case_indices: Optional[Sequence[int]] = None,
                agent_names: Optional[Sequence[str]] = None,
                agent_run_failed: Optional[bool] = None) -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1410)

Return a new run containing only rows matching structural filters.

Filters by evaluation case index, agent name, and/or agent run failure flag.
For metric score, latency, or credits filters use :meth:`filter` instead.

#### filter

```python
def filter(*,
           case_indices: Optional[Sequence[int]] = None,
           agent_names: Optional[Sequence[str]] = None,
           agent_run_failed: Optional[bool] = None,
           metric: Optional[str] = None,
           op: Optional[str] = None,
           value: Any = _FILTER_VALUE_UNSPECIFIED,
           inner_key: str = "score") -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1435)

Return a new run after structural filters and an optional metric clause.

Structural arguments (``case_indices``, ``agent_names``, ``agent_run_failed``)
are applied first via :meth:`filter_base`, then rows are kept that satisfy the
metric clause when ``metric`` is set.

``metric`` is either a key under :attr:``1 (the same
prefix used by :meth:``2 and
``metrics[prefix][&#x27;score&#x27;]`` in :func:``5),
or a reserved per-row field alias: ``run_time`` / ``latency`` (row latency),
``used_credits`` / ``credits_used`` / ``cost`` (row credits).

``op`` supports ``lt``, ``le``, ``gt``, ``ge``, ``eq``, ``ne``, and ``in``.
For ``in``, pass ``value`` as a non-empty list or tuple (numeric membership for
numeric scores and row-level metrics; string membership otherwise).

**Arguments**:

- ``6 - Optional set of case indices to keep.
- ``7 - Optional set of agent names to keep.
- ``8 - When set, keep only rows with this failure flag.
- ``9 - Metric tool prefix or reserved row field name.
- ``0 - Comparison operator (required when ``metric`` is set).
- ``3 - Right-hand side: scalar for numeric/string compare, or sequence for ``in``.
- ``6 - Bucket field to read when ``metric`` is a tool prefix (default ``score``).
  

**Returns**:

  New :class:`filter_base`1 with matching rows.
  

**Raises**:

- `filter_base`2 - When ``metric``, ``op``, and ``value`` are inconsistent.

#### filter\_where

```python
def filter_where(
        predicate: Callable[[AgentEvaluationRow], bool]) -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1504)

Return a new run with rows for which ``predicate(row)`` is true.

#### subset\_for\_case

```python
def subset_for_case(case_index: int) -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1508)

Return a new run with only rows for ``case_index``.

#### metric\_pass\_rates

```python
def metric_pass_rates() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1512)

Aggregate pass counts and rates for metrics that recorded ``metric_pass``.

**Returns**:

  Mapping from metric tool prefix to ``passed``, ``evaluated``, ``pass_rate``,
  and nested ``by_agent`` (same keys per agent). Empty when no thresholds
  were applied. See :func:``0.

#### evaluate\_quality\_gates

```python
def evaluate_quality_gates(
        *,
        metric_score_criteria: Optional[Mapping[str, Any]] = None,
        run_aggregate_gates: Optional[Mapping[str,
                                              Any]] = None) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1522)

Assess pass/fail against custom metric score rules and run-level aggregates.

**Metric scores** (per :class:`Metric` prefix in :attr:`rows` ``metrics``):

- A bare number uses the same rule as :attr:`Metric.threshold` for numeric scores
(pass when ``score &gt; threshold``).
- A list/tuple of strings passes when the score string is in that set (enum-style).
- A dict supports ``threshold``, optional ``operator`` (``lt`` / ``le`` / ``gt`` / ``ge`` /
``eq``), and optional ``score_key`` (defaults to ``&quot;score&quot;``).

Rows with ``metric_skipped`` or missing ``score_key`` are omitted from that metric&#x27;s
evaluation count. If every row is omitted, that metric gate **fails** (nothing to verify).

**Per-sample latency and cost** use the same criterion shapes as numeric metrics but
reserved criterion names (not metric prefixes): ``run_time`` / ``latency`` compare
:attr:``3; ``used_credits`` / ``credits_used`` / ``cost``
compare :attr:`Metric.threshold`0. Every row is evaluated; list/enum
criteria are not allowed for these fields.

**Run aggregate gates** use the same **field names** as overall :meth:`Metric.threshold`1
(``agent_failure_rate``, ``total_time_seconds``, ``total_cost``, ``n_agent_failures``,
``total_tool_calls``, ``rows_evaluated``, plus aliases ``credits_used``, ``run_time``).
They are evaluated **per agent** against that agent&#x27;s slice (sums / counts / failure
rate for that agent&#x27;s rows only).

Each gate is ``\{&quot;bound&quot;: float, &quot;operator&quot;: &quot;lt&quot;}`` (default operator ``lt``).

**Arguments**:

- ``2 - Map metric prefix or reserved per-row field name → criterion.
- ``3 - Map run-summary-style field → ``\{&quot;bound&quot;, &quot;operator&quot;}``.
  

**Returns**:

  Dict with ``by_agent`` (each agent&#x27;s ``overall_pass``, ``metric_gates``,
  ``aggregate_gates``), ``all_agents_pass`` (conjunction across agents), ``agents``,
  ``criteria`` echoing inputs, and ``debug_dataframe`` — a long-format
  :class:``2 with ``query`` / ``input``, ``agent_name``, ``output``,
  ``agent_response``, core row fields, ``&lt;metric_prefix&gt;__&lt;metric_field&gt;`` columns
  (``score``, ``metric_pass``, ``metric_status``, ``metric_error``, skip fields, etc.),
  plus ``&lt;key&gt;__criteria_pass`` / ``&lt;key&gt;__criteria_reason`` when the corresponding
  ``metric_score_criteria`` entry applies to that row. Rows with missing ``agent_name``
  are grouped under ``&quot;__unnamed__&quot;`` in ``by_agent``; the debug frame lists raw
  ``agent_name`` values.

#### to\_llm\_context

```python
def to_llm_context(*,
                   layout: str = "markdown",
                   max_output_chars: Optional[int] = 8000,
                   case_indices: Optional[Sequence[int]] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1634)

Build a single string suitable for pasting into an LLM prompt (review / compare).

Includes per-row fields needed for analysis: ``reference``, ``run_time``,
``used_credits``, ``request_id``, ``assets_used``, ``total_tool_calls``,
``per_asset_stats``, ``status``, completion and failure flags, errors,
``case_metadata``, ``metrics``, ``output``, and ``agent_response`` (both
long text fields respect ``max_output_chars`` when set). When any row has
``metric_pass`` under a metric prefix, a leading section summarizes overall
and per-agent pass rates (same data as :meth:``8).

**Arguments**:

- ``9 - ``markdown`` (headings and bullets) or ``text`` (plain lines).
- ``4 - Truncate ``output`` and ``agent_response``; ``None`` for no limit.
- ``1 - If set, only include rows whose ``case_index`` is listed.

#### to\_json\_records

```python
def to_json_records() -> List[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1753)

One JSON-serializable dict per row (metrics flattened as ``prefix__key``).

Run-level pass-rate aggregates live under :meth:`run_summary`&#x27;s
``metric_pass_rates`` (not duplicated on each record).

#### executive\_summary

```python
def executive_summary(model: Optional[Model] = None,
                      *,
                      prompt_input_kw: Optional[str] = None,
                      max_context_chars: int = 24_000,
                      quality_gates_report: Optional[Mapping[str, Any]] = None,
                      **model_run_kwargs: Any) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1896)

Generate an executive summary, optionally using an LLM for dynamic insights.

**Arguments**:

- `model` - Optional :class:`~aixplain.v2.model.Model` used to generate
  richer narrative insights from run statistics and compact context.
  If omitted, :attr:`AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH` is
  resolved via :meth:`AgentEvaluationRun.configure_insights` (bound
  ``client.Model``); otherwise a deterministic template summary is returned.
- `prompt_input_kw` - Optional explicit keyword for ``model.run`` (for
  example ``&quot;text&quot;`` or ``&quot;data&quot;``). When omitted it is inferred
  from model parameters.
- `~aixplain.v2.model.Model`3 - Maximum size of embedded evaluation context passed
  to the model.
- `~aixplain.v2.model.Model`4 - Optional mapping from :meth:`~aixplain.v2.model.Model`5
  (or its ``by_agent`` slice only); embedded as JSON for LLM/template context.
  ``debug_dataframe`` is stripped automatically.
- `AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH`0 - Extra kwargs forwarded to ``model.run`` when
  ``model`` is provided.

#### run\_summary

```python
def run_summary(*,
                include_executive_summary: bool = True,
                summary_model: Optional[Model] = None,
                summary_prompt_input_kw: Optional[str] = None,
                summary_max_context_chars: int = 24_000,
                quality_gates_report: Optional[Mapping[str, Any]] = None,
                **summary_model_run_kwargs: Any) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L1977)

Return aggregate run statistics and optional executive summary text.

When ``include_executive_summary`` is true and ``summary_model`` is not
provided, :attr:`AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH` is resolved
using the client from :meth:`AgentEvaluationRun.configure_insights` when set.

**Arguments**:

- `include_executive_summary` - Generate an LLM-backed executive summary.
- `summary_model` - Optional model for executive summary; defaults to configured insight model.
- `summary_prompt_input_kw` - Explicit keyword for model run input.
- `summary_max_context_chars` - Truncate embedded evaluation context to this size.
- ``0 - Optional :meth:``1 result (or ``by_agent``
  only); copied into ``quality_gates`` on the returned dict (without
  ``debug_dataframe``) and passed into :meth:``8 when enabled.
- ``9 - Additional kwargs passed to ``summary_model.run()``.
  

**Returns**:

  Dict with aggregate stats and optional ``executive_summary`` text.

#### summarize\_by\_agent

```python
def summarize_by_agent() -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2143)

Per-agent counts, failures, numeric metric means, and ``__metric_pass`` pass rates.

See :func:`summarize_by_agent`.

#### pivot\_agents\_wide

```python
def pivot_agents_wide(value_columns: Optional[Sequence[str]] = None,
                      *,
                      include_query: bool = True,
                      include_reference: bool = True) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2152)

Wide pivot with MultiIndex columns; see :func:`pivot_agents_wide`.

#### case\_comparison\_html

```python
def case_comparison_html(case_index: int,
                         *,
                         max_output_chars: Optional[int] = 8000) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2169)

HTML table comparing agents for one case; see :func:`case_comparison_html`.

#### case\_rows

```python
def case_rows(case_index: int) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2175)

Long-format :class:`pandas.DataFrame` for a single ``case_index``; see :func:`case_rows`.

#### metric\_prefixes

```python
def metric_prefixes() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2181)

Sorted union of metric tool prefixes present across rows.

#### metric\_inner\_key\_is\_numeric

```python
def metric_inner_key_is_numeric(inner_key: str = "score",
                                *,
                                tool_prefix: Optional[str] = None) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2209)

Return True if every non-null ``inner_key`` value coerces to a number via :func:`pandas.to_numeric`.

``inner_key`` defaults to ``&quot;score&quot;``. Use this to choose between :meth:`plot_mean_metric_by_agent`
(numeric) and :meth:`plot_enum_metric_by_agent` (string / enum-like categories).

**Raises**:

- `ValidationError` - If there is no data for this metric key after resolving ``tool_prefix``.

#### plot\_mean\_metric\_by\_agent

```python
def plot_mean_metric_by_agent(
        inner_key: str = "score",
        *,
        tool_prefix: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2236)

Draw a bar chart of mean ``inner_key`` per ``agent_name`` (numeric metrics only).

``inner_key`` is a key inside ``AgentEvaluationRow.metrics[tool_prefix]``; it defaults to
``&quot;score&quot;``. If ``tool_prefix`` is omitted and exactly one metric prefix exists on the run,
it is used; otherwise pass ``tool_prefix`` explicitly.

Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
``nbformat&gt;=4.2.0`` (``pip install nbformat`` or ``pip install -e &quot;.[notebook]&quot;`` from this repo).

**Returns**:

  A :class:``2.

#### plot\_enum\_metric\_by\_agent

```python
def plot_enum_metric_by_agent(inner_key: str = "score",
                              *,
                              tool_prefix: Optional[str] = None,
                              title: Optional[str] = None,
                              figsize: Optional[tuple[float, float]] = None,
                              normalize: bool = True) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2297)

Draw a grouped bar chart of categorical ``inner_key`` counts or shares per ``agent_name``.

``inner_key`` defaults to ``&quot;score&quot;``. Values are treated as discrete categories (strings or
:class:`enum.Enum` members).
When ``normalize`` is True (default), values are row-normalized (proportion per agent).

Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
``nbformat&gt;=4.2.0`` (``pip install nbformat`` or ``pip install -e &quot;.[notebook]&quot;`` from this repo).

**Returns**:

  A :class:``9.

#### plot\_metric\_by\_agent

```python
def plot_metric_by_agent(inner_key: str = "score",
                         *,
                         tool_prefix: Optional[str] = None,
                         title: Optional[str] = None,
                         figsize: Optional[tuple[float, float]] = None,
                         normalize_enum: bool = True) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2361)

Plot ``inner_key`` by agent, dispatching on numeric vs categorical values.

``inner_key`` defaults to ``&quot;score&quot;``. Calls :meth:`metric_inner_key_is_numeric`; numeric metrics use
:meth:`plot_mean_metric_by_agent`, otherwise :meth:`plot_enum_metric_by_agent`.
``normalize_enum`` is passed only to the enum path.

Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
``nbformat&gt;=4.2.0`` (``pip install nbformat`` or ``pip install -e &quot;.[notebook]&quot;`` from this repo).

**Returns**:

  A :class:``9.

#### chatbot

```python
def chatbot(
    model: Optional[Model] = None,
    *,
    system_prompt: Optional[str] = None,
    max_context_chars: int = 48_000,
    prompt_input_kw: Optional[str] = None,
    quality_gates_report: Optional[Mapping[str, Any]] = None
) -> AgentEvaluationResultsChatbot
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2397)

Build an LLM-backed helper that answers questions about this evaluation run.

The underlying :class:`~aixplain.v2.model.Model` is invoked with one text
payload per question. The run keyword (``text``, ``data``, etc.) is taken
from ``prompt_input_kw`` when provided; otherwise it is inferred from
:attr:`~aixplain.v2.model.Model.params` (required fields first), then
``&quot;text&quot;`` if the model declares no parameters.

**Arguments**:

- ``0 - Optional loaded :class:`~aixplain.v2.model.Model`. If omitted,
  the default insight model is resolved via
  :meth:``2 when set.
- ``3 - Override the default analyst instructions.
- ``4 - Truncate embedded evaluation context to this size.
- ``5 - Explicit keyword for :meth:``6
  (e.g. ``&quot;data&quot;`` for some utilities). ``None`` selects automatically.
- ``1 - Optional :meth:``2 result (or ``by_agent``
  only); appended as JSON after the evaluation excerpt on each turn.
  ``debug_dataframe`` is stripped automatically.
  

**Returns**:

  :class:``7 with :meth:``8.

### AgentEvaluationResultsChatbot Objects

```python
@dataclass
class AgentEvaluationResultsChatbot()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2596)

LLM-backed Q&amp;A over a single :class:`AgentEvaluationRun`.

Call :meth:`ask` with natural-language questions; prior turns are kept in
``conversation_history`` until :meth:`reset_conversation`.

#### reset\_conversation

```python
def reset_conversation() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2611)

Clear prior user/assistant turns (evaluation context is re-injected each call).

#### ask\_with\_result

```python
def ask_with_result(question: str, **model_run_kwargs: Any) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2672)

Run the model on ``question`` and return the raw :class:`~aixplain.v2.model.ModelResult`.

#### ask

```python
def ask(question: str, **model_run_kwargs: Any) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L2681)

Ask a question about the run; returns assistant text only.

#### normalize\_eval\_results\_dataframe

```python
def normalize_eval_results_dataframe(df: pd.DataFrame) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3070)

Return a copy of evaluator results with stable dtypes after CSV round-trip.

:meth:`AgentEvaluationRun.to_dataframe` (or CSV from ``to_csv``) followed by
:func:`pandas.read_csv` often yields object dtypes for booleans and occasionally
mis-typed integers. Use this on frames loaded from disk before calling helpers
such as :func:`~aixplain.v2.eval_results_display.pivot_agents_wide` or
:func:`~aixplain.v2.eval_results_display.summarize_by_agent`.

Only columns that exist are touched; unknown columns are left unchanged.

**Arguments**:

- `df` - Long-format evaluation results.
  

**Returns**:

  A new DataFrame; the input is not modified.

#### compare\_agents\_side\_by\_side

```python
def compare_agents_side_by_side(
        results: Union[pd.DataFrame, AgentEvaluationRun],
        *,
        value_columns: Optional[Sequence[str]] = None,
        include_query: bool = True,
        include_reference: bool = False) -> pd.DataFrame
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3160)

Pivot long evaluator results so each case is one row and agents are columns.

Typical long output (one row per case per agent, from
:class:`AgentEvaluationRun` or ``results.csv`` from ``to_dataframe().to_csv``)
is normalized with :func:`normalize_eval_results_dataframe`, then pivoted.
By default only ``output`` and metric **score** fields are included (columns
ending with ``__score`` / ``__scores``, or other numeric metric payload columns
such as ``m1__bleu``). Pass ``value_columns`` to override.

Result columns look like ``output__&lt;agent_name&gt;`` and
``aws-correctness__score__&lt;agent_name&gt;``. Optional ``query`` / ``reference``
are one column each per case (not split by agent).

**Arguments**:

- ``4 - Long-format :class:``5 or :class:`AgentEvaluationRun`.
- ``7 - Fields to spread by ``agent_name``; default is score-like
  columns only plus ``output``.
- ``2 - If True and ``query`` is present, add a single ``query``
  column per ``case_index``.
- ``9 - Same for ``reference``.
  

**Returns**:

  Wide DataFrame with ``case_index`` as the first column. Empty input
  yields an empty DataFrame.
  

**Raises**:

- ``4 - If required columns are missing or ``value_columns``
  references absent columns.

### Eval Objects

```python
class Eval()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3227)

Runs eval cases across agents, runs metric tools, returns :class:`AgentEvaluationRun`.

For each pair of (case, agent) the executor calls ``agent.run`` with the
case&#x27;s ``query``. Each :class:`Metric` is invoked with ``run`` payload
``data`` containing at least ``output`` (agent output) and ``reference``
(from the case, may be ``None``). Metric results are nested under
``AgentEvaluationRow.metrics[prefix]`` using the tool&#x27;s ``name``, ``id``, or
``metric_&lt;n&gt;`` as prefix (see :meth:``4 for the
legacy ``&lt;prefix&gt;__&lt;key&gt;`` flat layout).

Set ``cache_experiments=False`` to skip writing :class:``9
snapshots to the local cache after each :meth:``0. Use
``experiment_cache_dir`` to override the default cache directory.

#### \_\_init\_\_

```python
def __init__(*,
             cache_experiments: bool = True,
             experiment_cache_dir: Optional[Union[str, Path]] = None,
             autosave_eval_runs: Optional[bool] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3243)

Configure optional local persistence for :class:`~aixplain.v2.eval_experiment.Experiment`.

**Arguments**:

- `cache_experiments` - When True (default), experiments created via
  :meth:`create_experiment` are saved to disk after :meth:`~aixplain.v2.eval_experiment.Experiment.run`.
- `experiment_cache_dir` - Root directory for experiment JSON files; defaults to a
  platform-appropriate user cache path (see :func:`~aixplain.v2.eval_experiment.default_experiment_cache_dir`).
- `autosave_eval_runs` - Deprecated alias for ``cache_experiments`` when not ``None``.

#### create\_experiment

```python
def create_experiment(agents: Union[Agent, Sequence[Agent]],
                      dataset: Dataset,
                      metrics: Optional[Sequence[Metric]] = None,
                      *,
                      metadata: Optional[Dict[str, Any]] = None) -> Experiment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3272)

Build an :class:`~aixplain.v2.eval_experiment.Experiment` bound to this executor.

Snapshots ``agents`` and ``metrics`` via ``to_dict()`` for provenance and cache
reload. Call :meth:`~aixplain.v2.eval_experiment.Experiment.run` to execute and
append an :class:`~aixplain.v2.eval_experiment.ExperimentRun`.

**Arguments**:

- `agents` - Agent or sequence evaluated against ``dataset``.
- ``2 - Named evaluation dataset (:class:``3).
- ``4 - Optional metric tools.
- ``5 - Arbitrary JSON-serializable metadata stored on the experiment.
  

**Returns**:

  A new experiment with a unique id and creation timestamp.

#### list\_cached\_experiments

```python
def list_cached_experiments() -> List[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3318)

List experiments on disk under this executor&#x27;s cache directory.

#### load\_cached\_experiment

```python
def load_cached_experiment(experiment_id: str) -> Experiment
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3322)

Load a cached experiment and bind this executor for subsequent :meth:`~aixplain.v2.eval_experiment.Experiment.run` calls.

#### load\_from\_csv

```python
@classmethod
def load_from_csv(cls,
                  path: Union[str, Path, Any],
                  *,
                  normalize: bool = True,
                  **read_csv_kwargs: Any) -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3327)

Load a CSV written by :meth:`AgentEvaluationRun.to_dataframe` into a structured run.

Unknown columns (for example a legacy ``agent_id`` column) are ignored.
Flat ``&lt;metric_prefix&gt;__&lt;field&gt;`` columns are split into
``AgentEvaluationRow.metrics``.

**Arguments**:

- `path` - Path to the CSV file, or a file-like object accepted by
  :func:`pandas.read_csv`.
- `normalize` - If True, run :func:``0 so dtypes
  match in-memory evaluation results.
- ``1 - Forwarded to :func:`pandas.read_csv`.
  

**Returns**:

  :class:``3 with one row per CSV record.
  

**Raises**:

- ``4 - If the CSV is non-empty but missing ``case_index`` or
  ``agent_name``.

#### evaluate

```python
def evaluate(agents: Union[Agent, Sequence[Agent]],
             dataset: Dataset,
             metrics: Optional[Sequence[Metric]] = None,
             **agent_run_kwargs: Any) -> AgentEvaluationRun
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_evaluator.py#L3368)

Execute all cases against all agents and build a structured result.

**Arguments**:

- `agents` - A single :class:`~aixplain.v2.agent.Agent` or a sequence of agents.
- `dataset` - Named evaluation dataset whose :attr:`Dataset.cases` are executed.
- `metrics` - Optional sequence of :class:`Metric` instances. When a
  tool sets :attr:`Metric.threshold`, each successful metric row
  includes ``metric_pass`` (boolean) from the score and threshold.
- `**agent_run_kwargs` - Forwarded to each ``agent.run`` call.
  

**Returns**:

  :class:`~aixplain.v2.agent.Agent`2 with one :class:`~aixplain.v2.agent.Agent`3 per
  (case, agent). Agent or metric failures are recorded per row instead of
  aborting the batch. Empty ``dataset.cases`` yields an empty run.

