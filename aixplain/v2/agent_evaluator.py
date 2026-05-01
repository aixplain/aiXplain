"""Agent evaluation utilities for aiXplain v2 SDK.

Provides a minimal executor that runs evaluation cases through one or more
:class:`~aixplain.v2.agent.Agent` instances, runs optional :class:`MetricTool`
instances, and returns a structured :class:`AgentEvaluationRun`. Use
:meth:`AgentEvaluationRun.to_dataframe` for tabular export and
:meth:`AgentEvaluationExecutor.load_from_csv` to reload from disk.
"""

from __future__ import annotations

import ast
import enum
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Iterator, List, Mapping, Optional, Sequence, Union

if TYPE_CHECKING:
    from .eval_experiment import Experiment, ExperimentLocalCache

import pandas as pd
from dataclasses_json import config as dj_config, dataclass_json

from .agent import Agent, AgentResponseData, AgentRunResult
from .eval_results_display import _is_metric_data_column
from .model import Model, ModelResult
from .exceptions import AixplainV2Error, ValidationError, create_operation_failed_error
from .resource import Result
from .tool import Tool


def _plotly_layout_size(figsize: Optional[tuple[float, float]]) -> Dict[str, int]:
    """Map a matplotlib-style ``figsize`` in inches to pixel-ish Plotly width/height."""
    w, h = figsize if figsize is not None else (8.0, 4.0)
    return {"width": int(w * 96), "height": int(h * 96)}


def _plot_title_case(text: str) -> str:
    """Title-case plot labels (underscores become spaces; each word is capitalized)."""
    normalized = str(text).strip().replace("_", " ")
    words = [w for w in normalized.split() if w]
    out: List[str] = []
    for w in words:
        out.append(w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper())
    return " ".join(out)


@dataclass_json
@dataclass(repr=False)
class MetricToolResponse(Result):
    """Result for a metric tool run after validation and cleanup.

    Extends Result with optional metric-specific fields populated by
    post-processing (response validation and cleanup).
    """

    validated_data: Optional[Any] = field(default=None, metadata=dj_config(field_name="validatedData"))


@dataclass_json
@dataclass
class AgentResponseDataFields:
    """Fields that are required from AgentResponseData."""

    query: bool = field(default=False, metadata=dj_config(field_name="query"))
    trace: bool = field(default=False, metadata=dj_config(field_name="trace"))
    output: bool = field(default=False, metadata=dj_config(field_name="output"))

    def give_codes(self) -> Dict[str, str]:
        code_response: Dict[str, str] = {}
        if self.query:
            code_response["query"] = "{{QUERY}}"
        if self.trace:
            code_response["trace"] = "{{TRACE}}"
        if self.output:
            code_response["output"] = "{{OUTPUT}}"
        return code_response

    def give_metric_input(self, agent_response: AgentResponseData) -> str:
        metric_input = ""
        if self.query:
            metric_input += f"Query: {agent_response.input}\n"
        if self.trace:
            metric_input += f"Trace: {agent_response.steps}\n"
        if self.output:
            metric_input += f"Output: {agent_response.output}\n"
        return metric_input


@dataclass_json
@dataclass(repr=False)
class MetricTool(Tool):
    """Tool wrapper for creating a tool from a metric integration.

    Adds optional pre-processing before creation (placeholder) and
    post-processing (response validation and cleanup) when running.

    Optional :attr:`threshold` marks each evaluated row with ``metric_pass`` when
    set: for string/enum scores use a list of passing values; for numeric scores
    use a single float (pass when ``score > threshold``).
    """

    RESPONSE_CLASS = MetricToolResponse
    prompt_template: Optional[str] = field(default=None, metadata=dj_config(field_name="promptTemplate"))
    llm_path: Optional[str] = field(default=None, metadata=dj_config(field_name="llmPath"))
    agent_response_data_fields: AgentResponseDataFields = field(
        default_factory=AgentResponseDataFields,
        metadata=dj_config(field_name="agentResponseDataFields"),
    )
    additional_input_prompt: Optional[str] = field(default=None, metadata=dj_config(field_name="additionalInputPrompt"))
    score_type: Optional[str] = field(default=None, metadata=dj_config(field_name="scoreType"))
    threshold: Optional[Union[List[str], float]] = field(default=None, metadata=dj_config(field_name="threshold"))

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.threshold is not None:
            _validate_metric_tool_threshold(self.threshold)

    @classmethod
    def initialize(
        cls,
        name: str,
        prompt_template: str,
        llm_path: str,
        metric_description: str = "",
        allowed_actions: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> "MetricTool":
        """Initialize a MetricTool instance with common LLM metric tool configuration.

        Args:
            name: Name of the metric tool.
            prompt_template: The prompt template string for the LLM.
            llm_path: The path or ID of the LLM to use.
            metric_description: Optional description of the metric tool.
            **kwargs: Additional keyword arguments for Tool initialization.

        Returns:
            MetricTool: The initialized MetricTool instance.
        """
        config = {
            "prompt": prompt_template,
            "llmId": llm_path,
        }
        metric = cls(
            name=name,
            description=metric_description,
            integration="aixplain/custom-llm-prompt/aixplain",
            config=config,
            # allowed_actions=allowed_actions,
            # **kwargs,
        )
        metric.save()
        return metric

    @staticmethod
    def _normalize_metric_run_data(data: Any) -> dict:
        """Coerce run ``data`` to a dict.

        The custom-llm-prompt integration expects ``data`` to be an object (e.g. with
        ``output`` / ``reference``). Bare strings from ``run("...")`` are wrapped as
        ``{"output": ...}`` to match :class:`AgentEvaluationExecutor` payloads.
        """
        if data is None:
            return {}
        if isinstance(data, dict):
            return dict(data)
        return {"output": data}

    @staticmethod
    def trim_and_load_json(input_string: str) -> dict:
        start = input_string.find("{")
        end = input_string.rfind("}") + 1

        if end == 0 and start != -1:
            input_string = input_string + "}"
            end = len(input_string)

        jsonStr = input_string[start:end] if start != -1 and end != 0 else ""
        # Remove trailing comma if one is present
        jsonStr = re.sub(r",\s*([\]}])", r"\1", jsonStr)

        try:
            return json.loads(jsonStr)
        except json.JSONDecodeError:
            error_str = "Evaluation LLM outputted an invalid JSON. Please use a better evaluation model."
            raise ValueError(error_str)
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

    def measure(self, agent_response: AgentResponseData) -> MetricToolResponse:
        metric_input = self.agent_response_data_fields.give_metric_input(agent_response)
        if self.additional_input_prompt:
            metric_input = self.additional_input_prompt + "\n\n" + metric_input
        metric_payload = {"data": metric_input}
        return self.run(data=metric_payload)

    def _preprocess_before_create(self, payload: dict) -> dict:
        """Preprocess create payload. Placeholder: returns payload unchanged."""
        return payload

    def _validate_run_response(self, response: dict) -> None:
        """Validate the raw run response. Raises on invalid or failed status."""
        if not isinstance(response, dict):
            raise ValidationError("Run response must be a dictionary")
        status = response.get("status", "IN_PROGRESS")
        if status == "FAILED":
            raise create_operation_failed_error(response)

    def _cleanup_run_response(self, response: str) -> dict:
        """Clean up and normalize the run response dict."""
        response_dict = self.trim_and_load_json(response)
        return response_dict

    def handle_run_response(self, response: MetricToolResponse, **kwargs: Any) -> MetricToolResponse:
        """Validate and cleanup response, then return a MetricToolResponse."""
        self._validate_run_response(response)
        result = MetricToolResponse.from_dict(response)
        result.data = self._cleanup_run_response(result.data)
        result._raw_data = response
        result.validated_data = result.data
        return result


MetricTool.AgentResponseDataFields = AgentResponseDataFields


def _validate_metric_tool_threshold(threshold: Any) -> None:
    """Ensure :attr:`MetricTool.threshold` is a float or a list/tuple of passing enum strings."""
    if isinstance(threshold, bool):
        raise ValidationError("MetricTool.threshold must not be a boolean; use a float or a list of strings.")
    if isinstance(threshold, (int, float)):
        return
    if isinstance(threshold, (list, tuple)):
        return
    raise ValidationError(
        "MetricTool.threshold must be None, a float for numeric metrics, "
        f"or a list of passing enum strings; got {type(threshold).__name__}."
    )


def _metric_threshold_passes(threshold: Union[Sequence[str], float, int], score: Any) -> bool:
    """Return True if ``score`` passes ``threshold`` (enum membership or numeric greater-than)."""
    if isinstance(threshold, (list, tuple)):
        passing = {str(x).strip() for x in threshold}
        if score is None:
            return False
        return str(score).strip() in passing
    if isinstance(threshold, bool):
        return False
    if isinstance(threshold, (int, float)):
        try:
            bound = float(threshold)
        except (TypeError, ValueError):
            return False
        if score is None:
            return False
        try:
            return float(score) > bound
        except (TypeError, ValueError):
            return False
    return False


def _apply_metric_pass_for_threshold(
    metric_bucket: Dict[str, Any],
    metric_tool: Optional[MetricTool],
) -> None:
    """Set ``metric_pass`` on ``metric_bucket`` when ``metric_tool.threshold`` is configured."""
    if metric_tool is None:
        return
    threshold = getattr(metric_tool, "threshold", None)
    if threshold is None:
        return
    if isinstance(threshold, bool):
        return
    if not isinstance(threshold, (int, float, list, tuple)):
        return
    score = metric_bucket.get("score")
    metric_bucket["metric_pass"] = _metric_threshold_passes(threshold, score)


_QUALITY_GATE_NUMERIC_OPERATORS = frozenset({"lt", "le", "gt", "ge", "eq"})

_QUALITY_GATE_RUN_AGGREGATE_KEYS = frozenset(
    {
        "agent_failure_rate",
        "total_time_seconds",
        "total_cost",
        "n_agent_failures",
        "total_tool_calls",
        "rows_evaluated",
    },
)

# Map overall :meth:`run_summary` gate field → per-agent stats key (see ``_stats_from_agent_rows``).
_QUALITY_GATE_RUN_TO_PER_AGENT_STAT: Dict[str, str] = {
    "agent_failure_rate": "failure_rate",
    "total_time_seconds": "total_time_seconds",
    "total_cost": "total_cost",
    "n_agent_failures": "n_failures",
    "total_tool_calls": "total_tool_calls",
    "rows_evaluated": "rows",
}

# Accepted gate field names that map to :meth:`run_summary` keys.
_QUALITY_GATE_RUN_FIELD_ALIASES: Dict[str, str] = {
    "credits_used": "total_cost",
    "run_time": "total_time_seconds",
}

# Reserved names in ``metric_score_criteria`` for per-row :class:`AgentEvaluationRow` scalars.
_ROW_SAMPLE_METRIC_CRITERIA_FIELDS: Dict[str, str] = {
    "run_time": "run_time",
    "latency": "run_time",
    "used_credits": "used_credits",
    "credits_used": "used_credits",
    "cost": "used_credits",
}


def _numeric_quality_compare(actual: float, bound: float, operator: str) -> bool:
    """Compare ``actual`` to ``bound`` using ``operator`` (``lt``/``le``/``gt``/``ge``/``eq``)."""
    op = operator.strip().lower()
    if op == "lt":
        return actual < bound
    if op == "le":
        return actual <= bound
    if op == "gt":
        return actual > bound
    if op == "ge":
        return actual >= bound
    if op == "eq":
        return actual == bound
    raise ValidationError(
        f"Unsupported comparison operator {operator!r}; expected one of "
        f"{sorted(_QUALITY_GATE_NUMERIC_OPERATORS)}.",
    )


def _parse_aggregate_gate_spec(spec: Any, *, context: str) -> tuple[float, str]:
    """Parse ``{\"bound\": float, \"operator\": \"lt\"}`` style gate specs."""
    if not isinstance(spec, Mapping):
        raise ValidationError(f"{context} gate must be a mapping with 'bound' and 'operator'.")
    bound_raw = spec.get("bound")
    try:
        bound = float(bound_raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{context} gate requires numeric 'bound'.") from exc
    op = str(spec.get("operator", "lt")).strip().lower()
    if op not in _QUALITY_GATE_NUMERIC_OPERATORS:
        raise ValidationError(
            f"{context}: unsupported operator {spec.get('operator')!r}; "
            f"expected one of {sorted(_QUALITY_GATE_NUMERIC_OPERATORS)}.",
        )
    return bound, op


def _parse_metric_score_criterion(spec: Any) -> tuple[Any, str, str]:
    """Normalize custom metric score criteria.

    Returns:
        Tuple of ``(threshold_or_passing_values, operator, score_key)``. For enum-style
        metrics, ``operator`` is ``\"in\"`` and the first element is a list of passing values.
    """
    score_key_default = "score"
    if isinstance(spec, bool):
        raise ValidationError("Metric score criterion must not be a boolean.")
    if isinstance(spec, (list, tuple)):
        return (list(spec), "in", score_key_default)
    if isinstance(spec, (int, float)) and not isinstance(spec, bool):
        return (float(spec), "gt", score_key_default)
    if isinstance(spec, dict):
        score_key = str(spec.get("score_key", score_key_default))
        threshold = spec.get("threshold")
        if isinstance(threshold, (list, tuple)):
            return (list(threshold), "in", score_key)
        if threshold is None:
            raise ValidationError("Metric score criterion dict requires a 'threshold' value.")
        if isinstance(threshold, bool):
            raise ValidationError("Metric score threshold must not be a boolean.")
        if isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
            op_raw = spec.get("operator", "gt")
            op = str(op_raw).strip().lower()
            if op not in _QUALITY_GATE_NUMERIC_OPERATORS:
                raise ValidationError(
                    f"Unsupported metric score operator {op_raw!r}; "
                    f"expected one of {sorted(_QUALITY_GATE_NUMERIC_OPERATORS)}.",
                )
            return (float(threshold), op, score_key)
        raise ValidationError(
            "Metric score 'threshold' must be a number or a list/tuple of passing enum values.",
        )
    raise ValidationError(
        f"Unsupported metric score criterion type {type(spec).__name__}; "
        "use a number, list of passing strings, or a dict with 'threshold' and optional 'operator'.",
    )


def _row_sample_field_passes(
    row: "AgentEvaluationRow",
    field: str,
    threshold_part: Any,
    operator: str,
) -> bool:
    """Apply numeric criterion to ``row.run_time`` or ``row.used_credits``."""
    raw = getattr(row, field, None)
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return False
    try:
        bound = float(threshold_part)
    except (TypeError, ValueError):
        return False
    return _numeric_quality_compare(val, bound, operator)


def _agent_row_group_key(row: "AgentEvaluationRow") -> str:
    """Stable bucket for grouping evaluation rows by agent."""
    return "__unnamed__" if row.agent_name is None else str(row.agent_name)


def _stats_from_agent_rows(sub: Sequence["AgentEvaluationRow"]) -> Dict[str, Any]:
    """Per-agent slice stats aligned with :meth:`AgentEvaluationRun.run_summary` ``per_agent``."""
    if not sub:
        return {
            "rows": 0,
            "n_failures": 0,
            "failure_rate": 0.0,
            "total_cost": 0.0,
            "total_time_seconds": 0.0,
            "total_tool_calls": 0,
        }
    n = len(sub)
    nf = sum(1 for r in sub if r.agent_run_failed)
    return {
        "rows": n,
        "n_failures": nf,
        "failure_rate": (float(nf) / float(n)) if n else 0.0,
        "total_cost": float(sum(float(r.used_credits or 0.0) for r in sub)),
        "total_time_seconds": float(sum(float(r.run_time or 0.0) for r in sub)),
        "total_tool_calls": int(sum(int(r.total_tool_calls or 0) for r in sub)),
    }


def _metric_gate_entry_for_rows(
    rows: Sequence["AgentEvaluationRow"],
    pfx: str,
    raw_spec: Any,
) -> Dict[str, Any]:
    """Evaluate one ``metric_score_criteria`` entry over ``rows`` (same rules as :meth:`evaluate_quality_gates`)."""
    sample_attr = _ROW_SAMPLE_METRIC_CRITERIA_FIELDS.get(pfx)
    thr_part, op, score_key = _parse_metric_score_criterion(raw_spec)
    evaluated = 0
    passed_n = 0
    if sample_attr is not None:
        if op == "in":
            raise ValidationError(
                f"metric_score_criteria[{pfx!r}]: enum/list criteria are not supported "
                f"for per-row field {sample_attr!r}; use a numeric threshold and operator.",
            )
        for r in rows:
            evaluated += 1
            if _row_sample_field_passes(r, sample_attr, thr_part, op):
                passed_n += 1
    else:
        for r in rows:
            bucket = r.metrics.get(pfx)
            if not isinstance(bucket, dict):
                continue
            if bucket.get("metric_skipped"):
                continue
            if bucket.get(score_key) is None:
                continue
            evaluated += 1
            if _metric_row_passes_custom_criterion(bucket, thr_part, op, score_key):
                passed_n += 1
    gate_pass = evaluated > 0 and passed_n == evaluated
    entry: Dict[str, Any] = {
        "passed": gate_pass,
        "evaluated_rows": evaluated,
        "passed_rows": passed_n,
        "pass_rate": (float(passed_n) / float(evaluated)) if evaluated else 0.0,
        "operator": op,
        "threshold": thr_part,
    }
    if sample_attr is not None:
        entry["row_field"] = sample_attr
    else:
        entry["score_key"] = score_key
    return entry


_DEBUG_METRIC_BUCKET_KEYS: Sequence[str] = (
    "score",
    "metric_pass",
    "metric_status",
    "metric_completed",
    "metric_error",
    "metric_error_type",
    "metric_skip_reason",
    "metric_skipped",
)


def _row_quality_gate_criteria_detail(row: "AgentEvaluationRow", pfx: str, raw_spec: Any) -> Dict[str, Any]:
    """Evaluate ``metric_score_criteria`` for one row; return ``gate_pass`` and ``gate_reason``."""
    sample_attr = _ROW_SAMPLE_METRIC_CRITERIA_FIELDS.get(pfx)
    thr_part, op, score_key = _parse_metric_score_criterion(raw_spec)
    if sample_attr is not None:
        if op == "in":
            raise ValidationError(
                f"metric_score_criteria[{pfx!r}]: enum/list criteria are not supported "
                f"for per-row field {sample_attr!r}; use a numeric threshold and operator.",
            )
        raw_val = getattr(row, sample_attr, None)
        try:
            val_f = float(raw_val)
        except (TypeError, ValueError):
            return {
                "gate_pass": False,
                "gate_reason": f"{sample_attr} missing or non-numeric ({raw_val!r})",
            }
        ok = _row_sample_field_passes(row, sample_attr, thr_part, op)
        if ok:
            return {"gate_pass": True, "gate_reason": "ok"}
        return {
            "gate_pass": False,
            "gate_reason": f"{sample_attr}={val_f} failed {op} {thr_part}",
        }

    bucket = row.metrics.get(pfx)
    if not isinstance(bucket, dict):
        return {
            "gate_pass": False,
            "gate_reason": f"no metric bucket for prefix {pfx!r}",
        }
    if bucket.get("metric_skipped"):
        sr = bucket.get("metric_skip_reason") or "metric_skipped"
        return {"gate_pass": False, "gate_reason": f"skipped: {sr}"}
    score = bucket.get(score_key)
    if score is None:
        return {"gate_pass": False, "gate_reason": f"missing {score_key!r}"}
    ok = _metric_row_passes_custom_criterion(bucket, thr_part, op, score_key)
    if ok:
        return {"gate_pass": True, "gate_reason": "ok"}
    if op == "in":
        return {
            "gate_pass": False,
            "gate_reason": f"{score_key}={score!r} not in passing values {thr_part!r}",
        }
    try:
        sf = float(score)
        tb = float(thr_part)
    except (TypeError, ValueError):
        return {
            "gate_pass": False,
            "gate_reason": f"{score_key}={score!r} failed criterion ({op} {thr_part!r})",
        }
    return {
        "gate_pass": False,
        "gate_reason": f"{score_key}={sf} failed {op} {tb}",
    }


def _quality_gates_debug_dataframe(
    rows: Sequence["AgentEvaluationRow"],
    m_crit: Mapping[str, Any],
) -> pd.DataFrame:
    """One row per evaluation sample with inputs, outputs, metric fields, and optional criteria columns."""
    crit = dict(m_crit)
    crit_metric_prefixes = {str(k) for k in crit if not _ROW_SAMPLE_METRIC_CRITERIA_FIELDS.get(str(k))}
    prefixes_seen: set[str] = set()
    for r in rows:
        prefixes_seen.update(r.metrics.keys())
    all_metric_prefixes = sorted(prefixes_seen | crit_metric_prefixes)

    base_cols = (
        "case_index",
        "query",
        "input",
        "agent_name",
        "reference",
        "output",
        "agent_response",
        "status",
        "completed",
        "agent_run_failed",
        "error_message",
        "agent_error_type",
        "run_time",
        "used_credits",
    )

    if not rows:
        return pd.DataFrame(columns=list(base_cols))

    records: List[Dict[str, Any]] = []
    for r in rows:
        rec: Dict[str, Any] = {
            "case_index": r.case_index,
            "query": r.query,
            "input": r.query,
            "agent_name": r.agent_name,
            "reference": r.reference,
            "output": r.output,
            "agent_response": r.agent_response,
            "status": r.status,
            "completed": r.completed,
            "agent_run_failed": r.agent_run_failed,
            "error_message": r.error_message,
            "agent_error_type": r.agent_error_type,
            "run_time": r.run_time,
            "used_credits": r.used_credits,
        }
        for pfx in all_metric_prefixes:
            bucket = r.metrics.get(pfx)
            if not isinstance(bucket, dict):
                bucket = {}
            for mk in _DEBUG_METRIC_BUCKET_KEYS:
                rec[f"{pfx}__{mk}"] = bucket.get(mk)
            if pfx in crit:
                detail = _row_quality_gate_criteria_detail(r, pfx, crit[pfx])
                rec[f"{pfx}__criteria_pass"] = detail["gate_pass"]
                rec[f"{pfx}__criteria_reason"] = detail["gate_reason"]

        for pfx_raw, raw_spec in crit.items():
            pfx = str(pfx_raw)
            if not _ROW_SAMPLE_METRIC_CRITERIA_FIELDS.get(pfx):
                continue
            if pfx in all_metric_prefixes:
                continue
            detail = _row_quality_gate_criteria_detail(r, pfx, raw_spec)
            rec[f"{pfx}__criteria_pass"] = detail["gate_pass"]
            rec[f"{pfx}__criteria_reason"] = detail["gate_reason"]

        records.append(rec)

    return pd.DataFrame(records)


def _aggregate_gates_for_stats(
    stats: Mapping[str, Any],
    r_gates: Mapping[str, Any],
    *,
    context_prefix: str,
) -> tuple[Dict[str, Any], bool]:
    """Apply ``run_aggregate_gates`` to a per-agent stats mapping; return results and all-pass."""
    run_allowed = _QUALITY_GATE_RUN_AGGREGATE_KEYS | set(_QUALITY_GATE_RUN_FIELD_ALIASES.keys())
    run_results: Dict[str, Any] = {}
    all_pass = True
    for key, spec in r_gates.items():
        k = str(key)
        if k not in run_allowed:
            raise ValidationError(
                f"Unknown run aggregate gate key {k!r}. "
                f"Allowed: {sorted(run_allowed)}.",
            )
        canonical = _QUALITY_GATE_RUN_FIELD_ALIASES.get(k, k)
        stat_field = _QUALITY_GATE_RUN_TO_PER_AGENT_STAT.get(canonical)
        if stat_field is None:
            raise ValidationError(
                f"run_aggregate_gates[{k!r}]: internal mapping missing for {canonical!r}.",
            )
        bound, op = _parse_aggregate_gate_spec(spec, context=f"{context_prefix}[{k!r}]")
        actual_raw = stats.get(stat_field)
        try:
            actual_f = float(actual_raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"{context_prefix}: field {stat_field!r} is not numeric (got {actual_raw!r}).",
            ) from exc
        ok = _numeric_quality_compare(actual_f, bound, op)
        if not ok:
            all_pass = False
        run_results[k] = {
            "passed": ok,
            "actual": actual_f,
            "bound": bound,
            "operator": op,
            "canonical_field": canonical,
            "per_agent_stat_field": stat_field,
        }
    return run_results, all_pass


def _metric_row_passes_custom_criterion(
    bucket: Dict[str, Any],
    threshold_part: Any,
    operator: str,
    score_key: str,
) -> bool:
    """Return whether ``bucket[score_key]`` passes under the parsed criterion."""
    if bucket.get("metric_skipped"):
        return False
    score = bucket.get(score_key)
    if score is None:
        return False
    if operator == "in":
        passing = {str(x).strip() for x in threshold_part}
        return str(score).strip() in passing
    try:
        bound = float(threshold_part)
        val = float(score)
    except (TypeError, ValueError):
        return False
    return _numeric_quality_compare(val, bound, operator)


def _coerce_metric_pass_value(value: Any) -> Optional[bool]:
    """Parse ``metric_pass`` after CSV or API into ``True``/``False``; unknown becomes ``None``."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "1", "yes", "pass"):
            return True
        if s in ("false", "0", "no", "fail"):
            return False
        return None
    return None


def metric_pass_rates_from_rows(rows: Sequence[AgentEvaluationRow]) -> Dict[str, Any]:
    """Aggregate pass counts and rates for each metric prefix that has ``metric_pass``.

    Only rows with a coercible boolean ``metric_pass`` under a prefix are counted.
    Structure::

        {
            "<prefix>": {
                "passed": int,
                "evaluated": int,
                "pass_rate": float,
                "by_agent": {
                    "<agent_name>": {"passed": int, "evaluated": int, "pass_rate": float},
                    ...
                },
            },
            ...
        }

    Args:
        rows: Evaluation rows (typically :attr:`AgentEvaluationRun.rows`).

    Returns:
        Empty dict when no ``metric_pass`` fields are present.
    """
    pairs_by_prefix: Dict[str, List[tuple[str, bool]]] = {}
    for r in rows:
        agent_key = str(r.agent_name) if r.agent_name is not None else ""
        for prefix, fields in r.metrics.items():
            if not isinstance(fields, dict) or "metric_pass" not in fields:
                continue
            coerced = _coerce_metric_pass_value(fields.get("metric_pass"))
            if coerced is None:
                continue
            pairs_by_prefix.setdefault(str(prefix), []).append((agent_key, coerced))

    out: Dict[str, Any] = {}
    for prefix, pairs in pairs_by_prefix.items():
        evaluated = len(pairs)
        passed_n = sum(1 for _, p in pairs if p)
        by_agent_raw: Dict[str, List[bool]] = {}
        for agent_key, p in pairs:
            by_agent_raw.setdefault(agent_key, []).append(p)
        by_agent: Dict[str, Dict[str, Any]] = {}
        for agent_key, plist in by_agent_raw.items():
            ev = len(plist)
            pn = sum(1 for x in plist if x)
            by_agent[agent_key] = {
                "passed": pn,
                "evaluated": ev,
                "pass_rate": (float(pn) / float(ev)) if ev else 0.0,
            }
        out[prefix] = {
            "passed": passed_n,
            "evaluated": evaluated,
            "pass_rate": (float(passed_n) / float(evaluated)) if evaluated else 0.0,
            "by_agent": by_agent,
        }
    return out


def _format_metric_pass_rates_for_llm(mpr: Dict[str, Any], *, markdown: bool) -> str:
    """Human-readable block for :meth:`AgentEvaluationRun.to_llm_context` / templates."""
    if not mpr:
        return ""
    lines: List[str] = []
    for prefix in sorted(mpr):
        stats = mpr[prefix]
        if not isinstance(stats, dict):
            continue
        passed = stats.get("passed", 0)
        ev = stats.get("evaluated", 0)
        rate = float(stats.get("pass_rate", 0.0))
        by_agent = stats.get("by_agent") or {}
        if markdown:
            lines.append(
                f"- **{prefix}**: {rate:.2%} pass ({passed}/{ev}); by agent: "
                + (
                    ", ".join(
                        f"{a}: {float(b.get('pass_rate', 0.0)):.2%} ({b.get('passed', 0)}/{b.get('evaluated', 0)})"
                        for a, b in sorted(by_agent.items())
                        if isinstance(b, dict)
                    )
                    or "(n/a)"
                )
            )
        else:
            lines.append(
                f"{prefix}: pass_rate={rate:.4f} passed={passed} evaluated={ev}; "
                + (
                    "; ".join(
                        f"{a}: pass_rate={float(b.get('pass_rate', 0.0)):.4f} "
                        f"passed={b.get('passed', 0)}/{b.get('evaluated', 0)}"
                        for a, b in sorted(by_agent.items())
                        if isinstance(b, dict)
                    )
                    or "by_agent=n/a"
                )
            )
    return "\n".join(lines)


@dataclass
class EvalCase:
    """One evaluation example (input plus optional reference and metadata).

    Attributes:
        query: Passed to ``agent.run(query, **agent_run_kwargs)``.
        reference: Optional ground truth or expected value for metrics.
        metadata: Optional extra fields merged into the result row as ``case_meta__<key>``.
    """

    query: Any
    reference: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentEvaluationRow:
    """One evaluated (case, agent) pair including nested metric tool fields.

    ``metrics`` maps each metric tool prefix (see :func:`_metric_tool_prefix`) to
    a dict of flattened keys (for example ``metric_status``, ``score``,
    ``metric_pass`` when the tool defines a :attr:`~MetricTool.threshold`) matching
    the former ``<prefix>__<key>`` column names without the ``<prefix>__`` prefix.

    ``per_asset_stats`` maps a stable asset label (``type`` and ``name`` from each
    step's ``unit``, joined as ``type:name``, or breakdown keys from
    ``execution_stats`` when steps are absent) to ``run_time``, ``used_credits``,
    and ``n_steps`` aggregates.
    """

    case_index: int
    query: Any
    reference: Optional[Any]
    agent_name: Optional[str]
    output: Optional[Any]
    agent_response: Optional[Any]
    status: Any
    completed: bool
    error_message: Optional[str]
    run_time: float
    used_credits: float
    agent_run_failed: bool
    agent_error_type: Optional[str]
    agent_error_details: Optional[Dict[str, Any]]
    case_metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    request_id: Optional[str] = None
    assets_used: List[str] = field(default_factory=list)
    total_tool_calls: int = 0
    per_asset_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def metric_value(self, tool_prefix: str, key: str) -> Any:
        """Return ``metrics[tool_prefix][key]`` when present, else ``None``."""
        return self.metrics.get(tool_prefix, {}).get(key)


@dataclass
class AgentEvaluationRun:
    """Structured output of :meth:`AgentEvaluationExecutor.evaluate`.

    Convenience methods (filtering, LLM-ready text, summaries, HTML, optional plots,
    and :meth:`chatbot`) build on :meth:`to_dataframe` and
    :mod:`aixplain.v2.eval_results_display`.

    Default LLM-backed insight features (:meth:`executive_summary`, :meth:`chatbot`
    without ``model=``) resolve the model at :attr:`DEFAULT_INSIGHT_MODEL_PATH`
    using the client bound by :meth:`configure_insights`. After creating
    ``aix = Aixplain(...)``, call ``AgentEvaluationRun.configure_insights(aix)``
    so :meth:`aix.Model.get` with the path-style model id uses the same API key and
    URLs as your agents. :attr:`DEFAULT_INSIGHT_MODEL` stays ``None`` until the
    first successful resolution; call :meth:`ensure_insight_model_loaded` to
    populate it without generating a summary.
    """

    DEFAULT_INSIGHT_MODEL_PATH: ClassVar[str] = "openai/gpt-5.4-mini/openai"
    DEFAULT_INSIGHT_MODEL: ClassVar[Optional[Model]] = None
    insight_context: ClassVar[Optional[Any]] = None

    rows: List[AgentEvaluationRow] = field(default_factory=list)

    @classmethod
    def configure_insights(cls, client: Any) -> None:
        """Bind default insight model resolution to an :class:`~aixplain.v2.core.Aixplain` client.

        Clears any cached default model so the next resolution uses ``client.Model``.

        Args:
            client: An initialized ``Aixplain`` instance (same one used for
                ``client.Agent.get``, ``client.Model``, etc.).
        """
        cls.insight_context = client
        cls.DEFAULT_INSIGHT_MODEL = None

    @classmethod
    def ensure_insight_model_loaded(cls) -> Optional[Model]:
        """Resolve and cache :attr:`DEFAULT_INSIGHT_MODEL` from :attr:`DEFAULT_INSIGHT_MODEL_PATH`.

        Call after :meth:`configure_insights`. Idempotent when a model is already cached.

        Returns:
            The cached :class:`~aixplain.v2.model.Model`, or ``None`` if get/search fails.
        """
        return cls._resolve_default_insight_model()

    @classmethod
    def _resolve_default_insight_model(cls) -> Optional[Model]:
        """Resolve and cache the default model for executive summary and chatbot.

        Uses ``client.Model.get`` with :attr:`DEFAULT_INSIGHT_MODEL_PATH` (path-style
        id, e.g. ``openai/gpt-5.4-mini/openai``). If that fails, falls back to
        ``search(path=...)`` then ``get(id)``.
        """
        if cls.DEFAULT_INSIGHT_MODEL is not None:
            return cls.DEFAULT_INSIGHT_MODEL
        model_cls: Any = Model
        if cls.insight_context is not None:
            bound = getattr(cls.insight_context, "Model", None)
            if bound is not None and getattr(bound, "context", None) is not None:
                model_cls = bound
        path = str(cls.DEFAULT_INSIGHT_MODEL_PATH)
        try:
            cls.DEFAULT_INSIGHT_MODEL = model_cls.get(path)
            return cls.DEFAULT_INSIGHT_MODEL
        except Exception:
            pass
        try:
            page = model_cls.search(path=path, page_size=50)
        except Exception:
            return None
        results = list(getattr(page, "results", []) or [])
        if not results:
            return None
        exact = [m for m in results if str(getattr(m, "path", "")) == path]
        chosen = exact[0] if exact else results[0]
        model_id = getattr(chosen, "id", None)
        if model_id:
            try:
                cls.DEFAULT_INSIGHT_MODEL = model_cls.get(str(model_id))
                return cls.DEFAULT_INSIGHT_MODEL
            except Exception:
                pass
        if isinstance(chosen, Model):
            cls.DEFAULT_INSIGHT_MODEL = chosen
        return cls.DEFAULT_INSIGHT_MODEL

    def __iter__(self) -> Iterator[AgentEvaluationRow]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __bool__(self) -> bool:
        return bool(self.rows)

    def to_dataframe(self) -> pd.DataFrame:
        """Materialize rows into a long-format :class:`pandas.DataFrame` (CSV / pivot helpers)."""
        if not self.rows:
            return pd.DataFrame(
                columns=[
                    "case_index",
                    "agent_id",
                    "agent_name",
                    "query",
                    "reference",
                    "output",
                    "status",
                    "completed",
                    "error_message",
                    "run_time",
                    "used_credits",
                    "agent_run_failed",
                    "agent_error_type",
                    "agent_error_details",
                    "request_id",
                    "assets_used",
                    "total_tool_calls",
                    "per_asset_stats",
                ]
            )
        records: List[Dict[str, Any]] = []
        for r in self.rows:
            d: Dict[str, Any] = {
                "case_index": r.case_index,
                "query": r.query,
                "reference": r.reference,
                "agent_name": r.agent_name,
                "output": r.output,
                "agent_response": r.agent_response,
                "status": r.status,
                "completed": r.completed,
                "error_message": r.error_message,
                "run_time": r.run_time,
                "used_credits": r.used_credits,
                "agent_run_failed": r.agent_run_failed,
                "agent_error_type": r.agent_error_type,
                "agent_error_details": r.agent_error_details,
                "request_id": r.request_id,
                "assets_used": json.dumps(r.assets_used),
                "total_tool_calls": r.total_tool_calls,
                "per_asset_stats": json.dumps(r.per_asset_stats, default=str),
            }
            for meta_key, meta_val in r.case_metadata.items():
                d[f"case_meta__{meta_key}"] = meta_val
            for prefix, fields in r.metrics.items():
                for field_key, val in fields.items():
                    d[f"{prefix}__{field_key}"] = val
            records.append(d)
        return pd.DataFrame(records)

    def compare_agents_side_by_side(
        self,
        *,
        value_columns: Optional[Sequence[str]] = None,
        include_query: bool = True,
        include_reference: bool = False,
    ) -> pd.DataFrame:
        """Pivot to one row per case with agents in columns; see :func:`compare_agents_side_by_side`."""
        return compare_agents_side_by_side(
            self,
            value_columns=value_columns,
            include_query=include_query,
            include_reference=include_reference,
        )

    def filter(
        self,
        *,
        case_indices: Optional[Sequence[int]] = None,
        agent_names: Optional[Sequence[str]] = None,
        agent_run_failed: Optional[bool] = None,
    ) -> AgentEvaluationRun:
        """Return a new run containing only rows matching all supplied filters."""
        want_cases = set(case_indices) if case_indices is not None else None
        want_agents = set(agent_names) if agent_names is not None else None
        out: List[AgentEvaluationRow] = []
        for r in self.rows:
            if want_cases is not None and r.case_index not in want_cases:
                continue
            if want_agents is not None and r.agent_name not in want_agents:
                continue
            if agent_run_failed is not None and r.agent_run_failed != agent_run_failed:
                continue
            out.append(r)
        return AgentEvaluationRun(rows=out)

    def filter_where(self, predicate: Callable[[AgentEvaluationRow], bool]) -> AgentEvaluationRun:
        """Return a new run with rows for which ``predicate(row)`` is true."""
        return AgentEvaluationRun(rows=[r for r in self.rows if predicate(r)])

    def subset_for_case(self, case_index: int) -> AgentEvaluationRun:
        """Return a new run with only rows for ``case_index``."""
        return AgentEvaluationRun(rows=[r for r in self.rows if r.case_index == case_index])

    def metric_pass_rates(self) -> Dict[str, Any]:
        """Aggregate pass counts and rates for metrics that recorded ``metric_pass``.

        Returns:
            Mapping from metric tool prefix to ``passed``, ``evaluated``, ``pass_rate``,
            and nested ``by_agent`` (same keys per agent). Empty when no thresholds
            were applied. See :func:`metric_pass_rates_from_rows`.
        """
        return metric_pass_rates_from_rows(self.rows)

    def evaluate_quality_gates(
        self,
        *,
        metric_score_criteria: Optional[Mapping[str, Any]] = None,
        run_aggregate_gates: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assess pass/fail against custom metric score rules and run-level aggregates.

        **Metric scores** (per :class:`MetricTool` prefix in :attr:`rows` ``metrics``):

        - A bare number uses the same rule as :attr:`MetricTool.threshold` for numeric scores
          (pass when ``score > threshold``).
        - A list/tuple of strings passes when the score string is in that set (enum-style).
        - A dict supports ``threshold``, optional ``operator`` (``lt`` / ``le`` / ``gt`` / ``ge`` /
          ``eq``), and optional ``score_key`` (defaults to ``\"score\"``).

        Rows with ``metric_skipped`` or missing ``score_key`` are omitted from that metric's
        evaluation count. If every row is omitted, that metric gate **fails** (nothing to verify).

        **Per-sample latency and cost** use the same criterion shapes as numeric metrics but
        reserved criterion names (not metric prefixes): ``run_time`` / ``latency`` compare
        :attr:`AgentEvaluationRow.run_time`; ``used_credits`` / ``credits_used`` / ``cost``
        compare :attr:`AgentEvaluationRow.used_credits`. Every row is evaluated; list/enum
        criteria are not allowed for these fields.

        **Run aggregate gates** use the same **field names** as overall :meth:`run_summary`
        (``agent_failure_rate``, ``total_time_seconds``, ``total_cost``, ``n_agent_failures``,
        ``total_tool_calls``, ``rows_evaluated``, plus aliases ``credits_used``, ``run_time``).
        They are evaluated **per agent** against that agent's slice (sums / counts / failure
        rate for that agent's rows only).

        Each gate is ``{\"bound\": float, \"operator\": \"lt\"}`` (default operator ``lt``).

        Args:
            metric_score_criteria: Map metric prefix or reserved per-row field name → criterion.
            run_aggregate_gates: Map run-summary-style field → ``{\"bound\", \"operator\"}``.

        Returns:
            Dict with ``by_agent`` (each agent's ``overall_pass``, ``metric_gates``,
            ``aggregate_gates``), ``all_agents_pass`` (conjunction across agents), ``agents``,
            ``criteria`` echoing inputs, and ``debug_dataframe`` — a long-format
            :class:`pandas.DataFrame` with ``query`` / ``input``, ``agent_name``, ``output``,
            ``agent_response``, core row fields, ``<metric_prefix>__<metric_field>`` columns
            (``score``, ``metric_pass``, ``metric_status``, ``metric_error``, skip fields, etc.),
            plus ``<key>__criteria_pass`` / ``<key>__criteria_reason`` when the corresponding
            ``metric_score_criteria`` entry applies to that row. Rows with missing ``agent_name``
            are grouped under ``\"__unnamed__\"`` in ``by_agent``; the debug frame lists raw
            ``agent_name`` values.
        """
        m_crit = dict(metric_score_criteria or {})
        r_gates = dict(run_aggregate_gates or {})

        groups: Dict[str, List[AgentEvaluationRow]] = {}
        for r in self.rows:
            groups.setdefault(_agent_row_group_key(r), []).append(r)
        agent_keys = sorted(groups.keys())

        by_agent: Dict[str, Any] = {}
        all_agents_pass = True
        no_gates = not m_crit and not r_gates

        for agent_key in agent_keys:
            sub = groups[agent_key]
            metric_gates: Dict[str, Any] = {}
            metrics_all_pass = True
            if m_crit:
                for prefix, raw_spec in m_crit.items():
                    pfx = str(prefix)
                    entry = _metric_gate_entry_for_rows(sub, pfx, raw_spec)
                    metric_gates[pfx] = entry
                    if not entry["passed"]:
                        metrics_all_pass = False
            else:
                metrics_all_pass = True

            stats = _stats_from_agent_rows(sub)
            agg_results: Dict[str, Any] = {}
            agg_all_pass = True
            if r_gates:
                agg_results, agg_all_pass = _aggregate_gates_for_stats(
                    stats,
                    r_gates,
                    context_prefix=f"by_agent[{agent_key!r}]",
                )

            slice_pass = (metrics_all_pass and agg_all_pass) if not no_gates else True
            if not slice_pass:
                all_agents_pass = False

            by_agent[agent_key] = {
                "overall_pass": slice_pass,
                "metric_gates": metric_gates,
                "aggregate_gates": agg_results,
                "stats": stats,
            }

        if no_gates:
            all_agents_pass = True
        elif not agent_keys:
            all_agents_pass = False

        return {
            "by_agent": by_agent,
            "agents": agent_keys,
            "all_agents_pass": all_agents_pass,
            "debug_dataframe": _quality_gates_debug_dataframe(self.rows, m_crit),
            "criteria": {
                "metric_score_criteria": dict(m_crit),
                "run_aggregate_gates": dict(r_gates),
            },
        }

    def to_llm_context(
        self,
        *,
        layout: str = "markdown",
        max_output_chars: Optional[int] = 8000,
        case_indices: Optional[Sequence[int]] = None,
    ) -> str:
        """Build a single string suitable for pasting into an LLM prompt (review / compare).

        Includes per-row fields needed for analysis: ``reference``, ``run_time``,
        ``used_credits``, ``request_id``, ``assets_used``, ``total_tool_calls``,
        ``per_asset_stats``, ``status``, completion and failure flags, errors,
        ``case_metadata``, ``metrics``, ``output``, and ``agent_response`` (both
        long text fields respect ``max_output_chars`` when set). When any row has
        ``metric_pass`` under a metric prefix, a leading section summarizes overall
        and per-agent pass rates (same data as :meth:`metric_pass_rates`).

        Args:
            layout: ``markdown`` (headings and bullets) or ``text`` (plain lines).
            max_output_chars: Truncate ``output`` and ``agent_response``; ``None`` for no limit.
            case_indices: If set, only include rows whose ``case_index`` is listed.
        """
        if layout not in ("markdown", "text"):
            raise ValidationError("layout must be 'markdown' or 'text'")
        want = set(case_indices) if case_indices is not None else None
        rows = [r for r in self.rows if want is None or r.case_index in want]
        lines: List[str] = []
        md = layout == "markdown"
        mpr = metric_pass_rates_from_rows(rows)
        if mpr:
            if md:
                lines.append("## Metric threshold pass rates")
                lines.append(_format_metric_pass_rates_for_llm(mpr, markdown=True))
            else:
                lines.append("=== metric threshold pass rates ===")
                lines.append(_format_metric_pass_rates_for_llm(mpr, markdown=False))
            lines.append("")
        by_case: Dict[int, List[AgentEvaluationRow]] = {}
        for r in rows:
            by_case.setdefault(r.case_index, []).append(r)

        def _trunc(s: str) -> str:
            if max_output_chars is None or len(s) <= max_output_chars:
                return s
            return s[:max_output_chars] + "..."

        for ci in sorted(by_case):
            group = by_case[ci]
            if md:
                lines.append(f"## case_index={ci}")
            else:
                lines.append(f"=== case_index={ci} ===")
            q = group[0].query if group else ""
            if md:
                lines.append(f"- **query:** {q!s}")
            else:
                lines.append(f"query: {q!s}")
            for r in group:
                out_s = _trunc(str(r.output if r.output is not None else ""))
                resp_s = _trunc(str(r.agent_response if r.agent_response is not None else ""))
                ref_s = "" if r.reference is None else str(r.reference)
                if md:
                    lines.append(f"### agent: {r.agent_name!s}")
                    lines.append(
                        f"- status: {r.status!s}, completed: {r.completed}, "
                        f"agent_run_failed: {r.agent_run_failed}, "
                        f"run_time: {r.run_time}, used_credits: {r.used_credits}"
                    )
                    lines.append(
                        f"- request_id: {r.request_id!s}, total_tool_calls: {r.total_tool_calls}, "
                        f"assets_used: {json.dumps(r.assets_used, default=str)}"
                    )
                    lines.append(f"- per_asset_stats: {json.dumps(r.per_asset_stats, default=str)}")
                    if ref_s:
                        lines.append(f"- reference: {ref_s!s}")
                    if r.case_metadata:
                        lines.append(f"- case_metadata: {json.dumps(r.case_metadata, default=str)}")
                    if r.error_message:
                        lines.append(f"- error_message: {r.error_message!s}")
                    if r.agent_error_type or r.agent_error_details is not None:
                        lines.append(
                            f"- agent_error_type: {r.agent_error_type!s}, "
                            f"agent_error_details: {json.dumps(r.agent_error_details, default=str) if r.agent_error_details is not None else 'null'}"
                        )
                    if r.metrics:
                        lines.append(f"- metrics: {json.dumps(r.metrics, default=str)}")
                    lines.append(f"- output:\n```\n{out_s}\n```")
                    if resp_s:
                        lines.append(f"- agent_response:\n```\n{resp_s}\n```")
                else:
                    lines.append(f"agent: {r.agent_name!s}")
                    lines.append(
                        f"status={r.status} completed={r.completed} agent_run_failed={r.agent_run_failed} "
                        f"run_time={r.run_time} used_credits={r.used_credits}"
                    )
                    lines.append(
                        f"request_id={r.request_id!s} total_tool_calls={r.total_tool_calls} "
                        f"assets_used={json.dumps(r.assets_used, default=str)}"
                    )
                    lines.append(f"per_asset_stats={json.dumps(r.per_asset_stats, default=str)}")
                    if ref_s:
                        lines.append(f"reference={ref_s!s}")
                    if r.case_metadata:
                        lines.append(f"case_metadata={json.dumps(r.case_metadata, default=str)}")
                    if r.error_message:
                        lines.append(f"error_message={r.error_message!s}")
                    if r.agent_error_type or r.agent_error_details is not None:
                        lines.append(
                            f"agent_error_type={r.agent_error_type} "
                            f"agent_error_details={json.dumps(r.agent_error_details, default=str) if r.agent_error_details is not None else 'null'}"
                        )
                    if r.metrics:
                        lines.append(f"metrics={json.dumps(r.metrics, default=str)}")
                    lines.append(f"output:\n{out_s}")
                    if resp_s:
                        lines.append(f"agent_response:\n{resp_s}")
            lines.append("")
        return "\n".join(lines).strip()

    def to_json_records(self) -> List[Dict[str, Any]]:
        """One JSON-serializable dict per row (metrics flattened as ``prefix__key``).

        Run-level pass-rate aggregates live under :meth:`run_summary`'s
        ``metric_pass_rates`` (not duplicated on each record).
        """
        out: List[Dict[str, Any]] = []
        for r in self.rows:
            d: Dict[str, Any] = {
                "case_index": r.case_index,
                "query": r.query,
                "reference": r.reference,
                "agent_name": r.agent_name,
                "output": r.output,
                "status": r.status,
                "completed": r.completed,
                "error_message": r.error_message,
                "run_time": r.run_time,
                "used_credits": r.used_credits,
                "agent_run_failed": r.agent_run_failed,
                "agent_error_type": r.agent_error_type,
                "agent_error_details": r.agent_error_details,
                "case_metadata": dict(r.case_metadata),
                "request_id": r.request_id,
                "assets_used": list(r.assets_used),
                "total_tool_calls": r.total_tool_calls,
                "per_asset_stats": dict(r.per_asset_stats),
            }
            for prefix, fields in r.metrics.items():
                for fk, fv in fields.items():
                    d[f"{prefix}__{fk}"] = fv
            out.append(d)
        return out

    def _executive_summary_template(
        self,
        *,
        quality_gates_report: Optional[Mapping[str, Any]] = None,
        quality_gates_max_chars: int = 8000,
    ) -> str:
        """Deterministic summary template used when no LLM summary is requested."""
        summary = self.run_summary(include_executive_summary=False)
        if summary["rows_evaluated"] == 0:
            return (
                "No evaluation rows are available. Run the evaluator with at least one case and one agent "
                "to produce quality, cost, and reliability insights."
            )

        lines: List[str] = [
            "Evaluation overview:",
            f"- Evaluated {summary['total_samples']} samples across {summary['n_agents']} agents ({summary['rows_evaluated']} total rows).",
            f"- Total cost: {summary['total_cost']:.6f} credits. Total accumulated run time: {summary['total_time_seconds']:.3f}s.",
            f"- Agent-run failures: {summary['n_agent_failures']} of {summary['rows_evaluated']} rows ({summary['agent_failure_rate']:.2%}).",
            f"- Total tool calls observed in traces: {summary['total_tool_calls']}.",
        ]
        if summary["agents_evaluated"]:
            lines.append(f"- Agents evaluated: {', '.join(str(a) for a in summary['agents_evaluated'])}.")
        if summary["assets_used"]:
            lines.append(f"- Assets used: {', '.join(str(a) for a in summary['assets_used'])}.")

        metric_highlights = summary.get("metric_highlights") or {}
        if metric_highlights:
            lines.append("")
            lines.append("Performance highlights:")
            for metric_name, metric_data in metric_highlights.items():
                best = metric_data.get("best_agent")
                worst = metric_data.get("worst_agent")
                best_value = metric_data.get("best_value")
                worst_value = metric_data.get("worst_value")
                lines.append(
                    f"- {metric_name}: best={best} ({best_value:.4f}), worst={worst} ({worst_value:.4f}), "
                    f"spread={metric_data.get('spread', 0.0):.4f}."
                )

        mpr = summary.get("metric_pass_rates") or {}
        if mpr:
            lines.append("")
            lines.append("Threshold pass rates (metric_pass):")
            lines.append(_format_metric_pass_rates_for_llm(mpr, markdown=False))

        qg_txt = _format_quality_gates_report_text(quality_gates_report, max_chars=quality_gates_max_chars)
        if qg_txt:
            lines.append("")
            lines.append("Quality gates (evaluate_quality_gates by_agent):")
            lines.append(qg_txt)

        actions: List[str] = []
        if summary["agent_failure_rate"] > 0:
            actions.append(
                "Prioritize reliability fixes for failing rows (inspect agent_error_type/error_message and rerun those cases).",
            )

        per_agent = summary.get("per_agent") or {}
        cost_by_agent = {
            str(agent): float(values.get("total_cost", 0.0))
            for agent, values in per_agent.items()
        }
        if len(cost_by_agent) >= 2:
            max_agent = max(cost_by_agent, key=cost_by_agent.get)
            min_agent = min(cost_by_agent, key=cost_by_agent.get)
            min_cost = cost_by_agent[min_agent]
            max_cost = cost_by_agent[max_agent]
            if max_cost > 0 and (min_cost == 0 or max_cost >= (min_cost * 1.2)):
                actions.append(
                    f"Optimize spend for {max_agent}; its total cost ({max_cost:.6f}) is materially higher than {min_agent} ({min_cost:.6f}).",
                )

        for metric_name, metric_data in metric_highlights.items():
            best = metric_data.get("best_agent")
            spread = float(metric_data.get("spread", 0.0))
            if spread > 0:
                actions.append(
                    f"For {metric_name}, use {best} as the baseline and investigate why lower-performing agents trail by {spread:.4f}.",
                )

        for prefix, stats in mpr.items():
            if not isinstance(stats, dict):
                continue
            by_agent = stats.get("by_agent") or {}
            if len(by_agent) < 2:
                continue
            rates = {
                a: float(b.get("pass_rate", 0.0)) for a, b in by_agent.items() if isinstance(b, dict)
            }
            if len(rates) < 2:
                continue
            best_a = max(rates, key=rates.get)
            worst_a = min(rates, key=rates.get)
            gap = float(rates[best_a]) - float(rates[worst_a])
            if gap > 0.05:
                actions.append(
                    f"For threshold metric {prefix!r}, {best_a} leads on pass rate "
                    f"({rates[best_a]:.2%}) vs {worst_a} ({rates[worst_a]:.2%}); "
                    f"investigate the {gap:.2%} gap.",
                )

        lines.append("")
        lines.append("Actionable insights:")
        if actions:
            for action in actions:
                lines.append(f"- {action}")
        else:
            lines.append("- Reliability, cost, and metric spread look stable; proceed with larger or harder evaluation datasets for stronger signal.")

        return "\n".join(lines)

    def executive_summary(
        self,
        model: Optional[Model] = None,
        *,
        prompt_input_kw: Optional[str] = None,
        max_context_chars: int = 24_000,
        quality_gates_report: Optional[Mapping[str, Any]] = None,
        **model_run_kwargs: Any,
    ) -> str:
        """Generate an executive summary, optionally using an LLM for dynamic insights.

        Args:
            model: Optional :class:`~aixplain.v2.model.Model` used to generate
                richer narrative insights from run statistics and compact context.
                If omitted, :attr:`AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH` is
                resolved via :meth:`AgentEvaluationRun.configure_insights` (bound
                ``client.Model``); otherwise a deterministic template summary is returned.
            prompt_input_kw: Optional explicit keyword for ``model.run`` (for
                example ``"text"`` or ``"data"``). When omitted it is inferred
                from model parameters.
            max_context_chars: Maximum size of embedded evaluation context passed
                to the model.
            quality_gates_report: Optional mapping from :meth:`evaluate_quality_gates`
                (or its ``by_agent`` slice only); embedded as JSON for LLM/template context.
                ``debug_dataframe`` is stripped automatically.
            **model_run_kwargs: Extra kwargs forwarded to ``model.run`` when
                ``model`` is provided.
        """
        qg_cap = max(4000, max_context_chars // 4)
        if model is None:
            model = _default_insight_model()
        if model is None:
            return self._executive_summary_template(
                quality_gates_report=quality_gates_report,
                quality_gates_max_chars=qg_cap,
            )

        stats = self.run_summary(include_executive_summary=False)
        ctx = self.to_llm_context(layout="markdown", max_output_chars=2500)
        if len(ctx) > max_context_chars:
            ctx = ctx[:max_context_chars] + "\n\n[... evaluation context truncated ...]"

        qg_txt = _format_quality_gates_report_text(quality_gates_report, max_chars=qg_cap)

        prompt_parts: List[str] = [
            "You are a senior evaluation analyst. Write an executive summary of this agent evaluation run.",
            "Be specific, data-grounded, and actionable. Do not invent values.",
            "",
            "Requirements:",
            "- Briefly cover run scope, quality, reliability, cost, and latency.",
            "- Highlight strongest/weakest agents and key metric spreads.",
            "- When metric_pass_rates is present, cite overall and per-agent pass rates.",
            "- When quality_gates_report JSON is present (below, before row-level context), cite per-agent overall_pass, metric_gates, and aggregate_gates.",
            "- Include concrete next actions prioritized by impact.",
            "- Keep it concise but detailed enough for an engineering/product decision.",
            "",
            "=== run_summary_stats_json ===",
            json.dumps(stats, default=str),
            "",
        ]
        if qg_txt:
            prompt_parts.extend(["=== quality_gates_report ===", qg_txt, ""])
        prompt_parts.extend(
            [
                "=== compact_run_context ===",
                ctx,
                "",
                "Return plain text only.",
            ],
        )
        prompt = "\n".join(prompt_parts)
        kw = prompt_input_kw if prompt_input_kw is not None else _infer_prompt_input_field_name(model)
        result = model.run(**{kw: prompt}, **model_run_kwargs)
        text = _reply_text_from_model_result(result).strip()
        if text:
            return text
        return self._executive_summary_template(
            quality_gates_report=quality_gates_report,
            quality_gates_max_chars=qg_cap,
        )

    def run_summary(
        self,
        *,
        include_executive_summary: bool = True,
        summary_model: Optional[Model] = None,
        summary_prompt_input_kw: Optional[str] = None,
        summary_max_context_chars: int = 24_000,
        quality_gates_report: Optional[Mapping[str, Any]] = None,
        **summary_model_run_kwargs: Any,
    ) -> Dict[str, Any]:
        """Return aggregate run statistics and optional executive summary text.

        When ``include_executive_summary`` is true and ``summary_model`` is not
        provided, :attr:`AgentEvaluationRun.DEFAULT_INSIGHT_MODEL_PATH` is resolved
        using the client from :meth:`AgentEvaluationRun.configure_insights` when set.

        Args:
            quality_gates_report: Optional :meth:`evaluate_quality_gates` result (or ``by_agent``
                only); copied into ``quality_gates`` on the returned dict (without
                ``debug_dataframe``) and passed into :meth:`executive_summary` when enabled.
        """
        slim_qg = _slim_quality_gates_report_for_llm(quality_gates_report)
        rows = list(self.rows)
        if not rows:
            out = {
                "total_cost": 0.0,
                "total_time_seconds": 0.0,
                "total_samples": 0,
                "n_agents": 0,
                "agents_evaluated": [],
                "rows_evaluated": 0,
                "n_agent_failures": 0,
                "agent_failure_rate": 0.0,
                "total_tool_calls": 0,
                "assets_used": [],
                "per_asset_totals": {},
                "per_agent": {},
                "metric_highlights": {},
                "metric_pass_rates": {},
            }
            if slim_qg:
                out["quality_gates"] = slim_qg
            if include_executive_summary:
                out["executive_summary"] = self.executive_summary(
                    model=summary_model,
                    prompt_input_kw=summary_prompt_input_kw,
                    max_context_chars=summary_max_context_chars,
                    quality_gates_report=quality_gates_report,
                    **summary_model_run_kwargs,
                )
            return out

        agent_names = sorted({str(r.agent_name) for r in rows if r.agent_name is not None})
        case_indices = {r.case_index for r in rows}
        rows_evaluated = len(rows)
        n_fail = sum(1 for r in rows if r.agent_run_failed)
        total_cost = float(sum(float(r.used_credits or 0.0) for r in rows))
        total_time = float(sum(float(r.run_time or 0.0) for r in rows))
        total_tool_calls = int(sum(int(r.total_tool_calls or 0) for r in rows))

        assets: set[str] = set()
        per_asset_totals: Dict[str, Dict[str, float]] = {}
        for r in rows:
            for a in r.assets_used:
                if a is not None:
                    assets.add(str(a))
            for asset_key, vals in r.per_asset_stats.items():
                key = str(asset_key)
                bucket = per_asset_totals.setdefault(
                    key,
                    {"total_time_seconds": 0.0, "total_credits": 0.0, "n_steps": 0},
                )
                if isinstance(vals, dict):
                    bucket["total_time_seconds"] += _coerce_eval_float(vals.get("run_time"))
                    bucket["total_credits"] += _coerce_eval_float(vals.get("used_credits"))
                    steps = vals.get("n_steps", 0)
                    try:
                        bucket["n_steps"] += int(steps)
                    except (TypeError, ValueError):
                        pass

        mpr_global = metric_pass_rates_from_rows(rows)
        per_agent: Dict[str, Dict[str, Any]] = {}
        for agent in agent_names:
            sub = [r for r in rows if str(r.agent_name) == agent]
            pa: Dict[str, Any] = {
                "rows": len(sub),
                "n_failures": sum(1 for r in sub if r.agent_run_failed),
                "failure_rate": (sum(1 for r in sub if r.agent_run_failed) / len(sub)) if sub else 0.0,
                "total_cost": float(sum(float(r.used_credits or 0.0) for r in sub)),
                "total_time_seconds": float(sum(float(r.run_time or 0.0) for r in sub)),
                "total_tool_calls": int(sum(int(r.total_tool_calls or 0) for r in sub)),
            }
            for prefix, pdata in mpr_global.items():
                if not isinstance(pdata, dict):
                    continue
                by_agent = pdata.get("by_agent") or {}
                agent_stats = by_agent.get(agent)
                if isinstance(agent_stats, dict):
                    pa[f"metric_pass__{prefix}"] = {
                        "passed": int(agent_stats.get("passed", 0)),
                        "evaluated": int(agent_stats.get("evaluated", 0)),
                        "pass_rate": float(agent_stats.get("pass_rate", 0.0)),
                    }
            per_agent[agent] = pa

        metric_highlights: Dict[str, Dict[str, Any]] = {}
        df = self.to_dataframe()
        if not df.empty and "agent_name" in df.columns:
            metric_cols = [c for c in df.columns if _is_metric_data_column(c)]
            for col in metric_cols:
                numeric = pd.to_numeric(df[col], errors="coerce")
                valid = df.assign(_v=numeric).dropna(subset=["_v"])
                if valid.empty:
                    continue
                by_agent = valid.groupby("agent_name", dropna=False)["_v"].mean()
                if by_agent.empty:
                    continue
                best_agent = str(by_agent.idxmax())
                worst_agent = str(by_agent.idxmin())
                best_value = float(by_agent.max())
                worst_value = float(by_agent.min())
                metric_highlights[str(col)] = {
                    "best_agent": best_agent,
                    "best_value": best_value,
                    "worst_agent": worst_agent,
                    "worst_value": worst_value,
                    "spread": best_value - worst_value,
                }

        out = {
            "total_cost": total_cost,
            "total_time_seconds": total_time,
            "total_samples": len(case_indices),
            "n_agents": len(agent_names),
            "agents_evaluated": agent_names,
            "rows_evaluated": rows_evaluated,
            "n_agent_failures": n_fail,
            "agent_failure_rate": (n_fail / rows_evaluated) if rows_evaluated else 0.0,
            "total_tool_calls": total_tool_calls,
            "assets_used": sorted(assets),
            "per_asset_totals": per_asset_totals,
            "per_agent": per_agent,
            "metric_highlights": metric_highlights,
            "metric_pass_rates": mpr_global,
        }
        if slim_qg:
            out["quality_gates"] = slim_qg
        if include_executive_summary:
            out["executive_summary"] = self.executive_summary(
                model=summary_model,
                prompt_input_kw=summary_prompt_input_kw,
                max_context_chars=summary_max_context_chars,
                quality_gates_report=quality_gates_report,
                **summary_model_run_kwargs,
            )
        return out

    def summarize_by_agent(self) -> pd.DataFrame:
        """Per-agent counts, failures, numeric metric means, and ``__metric_pass`` pass rates.

        See :func:`summarize_by_agent`.
        """
        from .eval_results_display import summarize_by_agent

        return summarize_by_agent(self.to_dataframe())

    def pivot_agents_wide(
        self,
        value_columns: Optional[Sequence[str]] = None,
        *,
        include_query: bool = True,
        include_reference: bool = True,
    ) -> pd.DataFrame:
        """Wide pivot with MultiIndex columns; see :func:`pivot_agents_wide`."""
        from .eval_results_display import pivot_agents_wide

        return pivot_agents_wide(
            self.to_dataframe(),
            value_columns=value_columns,
            include_query=include_query,
            include_reference=include_reference,
        )

    def case_comparison_html(self, case_index: int, *, max_output_chars: Optional[int] = 8000) -> str:
        """HTML table comparing agents for one case; see :func:`case_comparison_html`."""
        from .eval_results_display import case_comparison_html

        return case_comparison_html(self.to_dataframe(), case_index, max_output_chars=max_output_chars)

    def case_rows(self, case_index: int) -> pd.DataFrame:
        """Long-format :class:`pandas.DataFrame` for a single ``case_index``; see :func:`case_rows`."""
        from .eval_results_display import case_rows

        return case_rows(self.to_dataframe(), case_index)

    def metric_tool_prefixes(self) -> List[str]:
        """Sorted union of metric tool prefixes present across rows."""
        keys: set[str] = set()
        for r in self.rows:
            keys.update(r.metrics.keys())
        return sorted(keys)

    def _resolve_single_metric_tool_prefix(self, tool_prefix: Optional[str]) -> str:
        """Resolve ``tool_prefix`` when omitted (single prefix on the run) or return explicit prefix."""
        if tool_prefix is not None:
            return tool_prefix
        prefixes = self.metric_tool_prefixes()
        if not prefixes:
            raise ValidationError("No metric data present; nothing to plot.")
        if len(prefixes) > 1:
            raise ValidationError(
                f"Multiple metric tool prefixes {prefixes!r}; pass tool_prefix= explicitly.",
            )
        return prefixes[0]

    @staticmethod
    def _metric_inner_scalar_label(raw: Any) -> str:
        """String label for a categorical metric value (handles :class:`enum.Enum`)."""
        if isinstance(raw, enum.Enum):
            val = raw.value
            return val if isinstance(val, str) else str(val)
        return str(raw)

    def metric_inner_key_is_numeric(
        self,
        inner_key: str = "score",
        *,
        tool_prefix: Optional[str] = None,
    ) -> bool:
        """Return True if every non-null ``inner_key`` value coerces to a number via :func:`pandas.to_numeric`.

        ``inner_key`` defaults to ``\"score\"``. Use this to choose between :meth:`plot_mean_metric_by_agent`
        (numeric) and :meth:`plot_enum_metric_by_agent` (string / enum-like categories).

        Raises:
            ValidationError: If there is no data for this metric key after resolving ``tool_prefix``.
        """
        tool_prefix = self._resolve_single_metric_tool_prefix(tool_prefix)
        values: List[Any] = []
        for r in self.rows:
            raw = r.metrics.get(tool_prefix, {}).get(inner_key)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            values.append(raw)
        if not values:
            raise ValidationError(f"No values for metrics[{tool_prefix!r}][{inner_key!r}].")

        num = pd.to_numeric(pd.Series(values, dtype=object), errors="coerce")
        return bool(num.notna().all())

    def plot_mean_metric_by_agent(
        self,
        inner_key: str = "score",
        *,
        tool_prefix: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
    ) -> Any:
        """Draw a bar chart of mean ``inner_key`` per ``agent_name`` (numeric metrics only).

        ``inner_key`` is a key inside ``AgentEvaluationRow.metrics[tool_prefix]``; it defaults to
        ``\"score\"``. If ``tool_prefix`` is omitted and exactly one metric prefix exists on the run,
        it is used; otherwise pass ``tool_prefix`` explicitly.

        Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
        ``nbformat>=4.2.0`` (``pip install nbformat`` or ``pip install -e ".[notebook]"`` from this repo).

        Returns:
            A :class:`plotly.graph_objects.Figure`.
        """
        try:
            import plotly.graph_objects as go  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "AgentEvaluationRun.plot_mean_metric_by_agent requires plotly. "
                "Install with: pip install plotly",
            ) from exc

        tool_prefix = self._resolve_single_metric_tool_prefix(tool_prefix)

        records: List[Dict[str, Any]] = []
        for r in self.rows:
            raw = r.metrics.get(tool_prefix, {}).get(inner_key)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            records.append({"agent_name": r.agent_name, "value": raw})
        if not records:
            raise ValidationError(f"No numeric values for metrics[{tool_prefix!r}][{inner_key!r}].")

        ser = pd.DataFrame(records)
        ser["value"] = pd.to_numeric(ser["value"], errors="coerce")
        ser = ser.dropna(subset=["value"])
        if ser.empty:
            raise ValidationError(f"No numeric values for metrics[{tool_prefix!r}][{inner_key!r}].")
        grouped = ser.groupby("agent_name", dropna=False)["value"].mean()

        agents = [str(i) for i in grouped.index]
        fig = go.Figure(data=[go.Bar(x=agents, y=grouped.values.tolist())])
        plot_title = (
            _plot_title_case(title)
            if title is not None
            else f"{_plot_title_case(f'mean {inner_key} by agent')} ({tool_prefix})"
        )
        fig.update_layout(
            title=plot_title,
            xaxis_title=_plot_title_case("agent_name"),
            yaxis_title=_plot_title_case(inner_key),
            xaxis_tickangle=-45,
            **_plotly_layout_size(figsize),
        )
        return fig

    def plot_enum_metric_by_agent(
        self,
        inner_key: str = "score",
        *,
        tool_prefix: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        normalize: bool = True,
    ) -> Any:
        """Draw a grouped bar chart of categorical ``inner_key`` counts or shares per ``agent_name``.

        ``inner_key`` defaults to ``\"score\"``. Values are treated as discrete categories (strings or
        :class:`enum.Enum` members).
        When ``normalize`` is True (default), values are row-normalized (proportion per agent).

        Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
        ``nbformat>=4.2.0`` (``pip install nbformat`` or ``pip install -e ".[notebook]"`` from this repo).

        Returns:
            A :class:`plotly.graph_objects.Figure`.
        """
        try:
            import plotly.graph_objects as go  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "AgentEvaluationRun.plot_enum_metric_by_agent requires plotly. "
                "Install with: pip install plotly",
            ) from exc

        tool_prefix = self._resolve_single_metric_tool_prefix(tool_prefix)
        records: List[Dict[str, Any]] = []
        for r in self.rows:
            raw = r.metrics.get(tool_prefix, {}).get(inner_key)
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            records.append({"agent_name": r.agent_name, "category": self._metric_inner_scalar_label(raw)})
        if not records:
            raise ValidationError(f"No categorical values for metrics[{tool_prefix!r}][{inner_key!r}].")

        df = pd.DataFrame(records)
        ct = pd.crosstab(df["agent_name"], df["category"])
        if normalize:
            ct = ct.div(ct.sum(axis=1), axis=0)

        ylab = "share" if normalize else "count"
        agents = [str(i) for i in ct.index]
        fig = go.Figure()
        for col in ct.columns:
            fig.add_trace(go.Bar(name=str(col), x=agents, y=ct[col].tolist()))
        plot_title = (
            _plot_title_case(title)
            if title is not None
            else f"{_plot_title_case(f'{inner_key} distribution by agent')} ({tool_prefix})"
        )
        fig.update_layout(
            barmode="group",
            title=plot_title,
            xaxis_title=_plot_title_case("agent_name"),
            yaxis_title=_plot_title_case(ylab),
            xaxis_tickangle=-45,
            legend_title_text=_plot_title_case(inner_key),
            **_plotly_layout_size(figsize),
        )
        return fig

    def plot_metric_by_agent(
        self,
        inner_key: str = "score",
        *,
        tool_prefix: Optional[str] = None,
        title: Optional[str] = None,
        figsize: Optional[tuple[float, float]] = None,
        normalize_enum: bool = True,
    ) -> Any:
        """Plot ``inner_key`` by agent, dispatching on numeric vs categorical values.

        ``inner_key`` defaults to ``\"score\"``. Calls :meth:`metric_inner_key_is_numeric`; numeric metrics use
        :meth:`plot_mean_metric_by_agent`, otherwise :meth:`plot_enum_metric_by_agent`.
        ``normalize_enum`` is passed only to the enum path.

        Requires plotly (``pip install plotly``). Jupyter / Cursor notebook inline display also needs
        ``nbformat>=4.2.0`` (``pip install nbformat`` or ``pip install -e ".[notebook]"`` from this repo).

        Returns:
            A :class:`plotly.graph_objects.Figure`.
        """
        if self.metric_inner_key_is_numeric(inner_key, tool_prefix=tool_prefix):
            return self.plot_mean_metric_by_agent(
                inner_key,
                tool_prefix=tool_prefix,
                title=title,
                figsize=figsize,
            )
        return self.plot_enum_metric_by_agent(
            inner_key,
            tool_prefix=tool_prefix,
            title=title,
            figsize=figsize,
            normalize=normalize_enum,
        )

    def chatbot(
        self,
        model: Optional[Model] = None,
        *,
        system_prompt: Optional[str] = None,
        max_context_chars: int = 48_000,
        prompt_input_kw: Optional[str] = None,
        quality_gates_report: Optional[Mapping[str, Any]] = None,
    ) -> AgentEvaluationResultsChatbot:
        """Build an LLM-backed helper that answers questions about this evaluation run.

        The underlying :class:`~aixplain.v2.model.Model` is invoked with one text
        payload per question. The run keyword (``text``, ``data``, etc.) is taken
        from ``prompt_input_kw`` when provided; otherwise it is inferred from
        :attr:`~aixplain.v2.model.Model.params` (required fields first), then
        ``\"text\"`` if the model declares no parameters.

        Args:
            model: Optional loaded :class:`~aixplain.v2.model.Model`. If omitted,
                the default insight model is resolved via
                :meth:`AgentEvaluationRun.configure_insights` when set.
            system_prompt: Override the default analyst instructions.
            max_context_chars: Truncate embedded evaluation context to this size.
            prompt_input_kw: Explicit keyword for :meth:`~aixplain.v2.model.Model.run`
                (e.g. ``\"data\"`` for some utilities). ``None`` selects automatically.
            quality_gates_report: Optional :meth:`evaluate_quality_gates` result (or ``by_agent``
                only); appended as JSON after the evaluation excerpt on each turn.
                ``debug_dataframe`` is stripped automatically.

        Returns:
            :class:`AgentEvaluationResultsChatbot` with :meth:`~AgentEvaluationResultsChatbot.ask`.
        """
        resolved_model = model if model is not None else _default_insight_model()
        if resolved_model is None:
            raise ValidationError(
                "No model provided and default insight model could not be loaded. "
                "Call AgentEvaluationRun.configure_insights(aix) after Aixplain(...), or pass model=... explicitly.",
            )
        resolved_kw = (
            prompt_input_kw if prompt_input_kw is not None else _infer_prompt_input_field_name(resolved_model)
        )
        return AgentEvaluationResultsChatbot(
            run=self,
            model=resolved_model,
            system_prompt=system_prompt or _DEFAULT_EVAL_CHATBOT_SYSTEM_PROMPT,
            max_context_chars=max_context_chars,
            prompt_input_kw=resolved_kw,
            quality_gates_report=quality_gates_report,
        )


_DEFAULT_EVAL_CHATBOT_SYSTEM_PROMPT = (
    "You are an analyst answering questions strictly about the agent evaluation "
    "results provided below. Use only facts present in the evaluation excerpt; "
    "if something is unknown or missing, say so. Be concise and accurate."
)

def _default_insight_model() -> Optional[Model]:
    """Return :meth:`AgentEvaluationRun._resolve_default_insight_model` (shim for callers)."""
    return AgentEvaluationRun._resolve_default_insight_model()


def _infer_prompt_input_field_name(model: Model) -> str:
    """Infer the ``Model.run`` keyword for the main text prompt (e.g. ``text`` vs ``data``).

    Uses declared :attr:`~aixplain.v2.model.Model.params` when present; otherwise
    defaults to ``\"text\"`` (common for LLMs such as OpenAI-backed models on the
    platform). Pass ``prompt_input_kw=...`` to :meth:`AgentEvaluationRun.chatbot`
    to override (for example ``\"data\"`` for some utility models).
    """
    params = getattr(model, "params", None) or []
    if not params:
        return "text"

    preferred = ("text", "data", "input", "prompt", "query")
    required = [p for p in params if getattr(p, "required", False)]
    for name in preferred:
        if any(getattr(p, "name", None) == name for p in required):
            return name
    if len(required) == 1:
        return str(required[0].name)
    for name in preferred:
        if any(getattr(p, "name", None) == name for p in params):
            return name
    for p in params:
        dt = (getattr(p, "data_type", None) or "").lower()
        if dt == "text":
            return str(p.name)
    return str(params[0].name)


def _slim_quality_gates_report_for_llm(report: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize :meth:`~AgentEvaluationRun.evaluate_quality_gates` output for summaries / chatbot."""
    if report is None:
        return {}
    if not isinstance(report, Mapping):
        raise ValidationError("quality_gates_report must be a mapping (e.g. evaluate_quality_gates result) or None.")
    rep = dict(report)
    rep.pop("debug_dataframe", None)
    if "by_agent" in rep:
        out: Dict[str, Any] = {}
        for key in ("all_agents_pass", "agents", "criteria", "by_agent"):
            if key in rep:
                out[key] = rep[key]
        return out
    return {"by_agent": dict(report)}


def _format_quality_gates_report_text(report: Optional[Mapping[str, Any]], *, max_chars: Optional[int]) -> str:
    """JSON text for embedding in prompts; optional truncation."""
    slim = _slim_quality_gates_report_for_llm(report)
    if not slim:
        return ""
    text = json.dumps(slim, default=str, indent=2)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n... [quality_gates_report truncated] ..."
    return text


def _reply_text_from_model_result(result: ModelResult) -> str:
    """Extract assistant-visible text from a :class:`~aixplain.v2.model.ModelResult`."""
    data = getattr(result, "data", None)

    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            ch0 = choices[0]
            if isinstance(ch0, dict):
                msg = ch0.get("message") or {}
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if content is not None and str(content).strip():
                        return str(content).strip()
        for key in ("output", "text", "content", "message", "response"):
            if key in data and data[key] is not None:
                s = str(data[key]).strip()
                if s:
                    return s

    if isinstance(data, str):
        s = data.strip()
        if s:
            return s
    elif data is not None and not isinstance(data, dict):
        s = str(data).strip()
        if s:
            return s

    alt = getattr(result, "result", None)
    if alt is not None:
        s = str(alt).strip()
        if s:
            return s

    details = getattr(result, "details", None) or []
    if isinstance(details, list):
        for item in details:
            msg: Any = None
            if isinstance(item, dict):
                msg = item.get("message")
            else:
                msg = getattr(item, "message", None)
            if msg is None:
                continue
            if isinstance(msg, dict):
                content = msg.get("content")
            else:
                content = getattr(msg, "content", None)
            if content is not None and str(content).strip():
                return str(content).strip()

    if isinstance(data, dict):
        return json.dumps(data, default=str)
    return ""


@dataclass
class AgentEvaluationResultsChatbot:
    """LLM-backed Q&A over a single :class:`AgentEvaluationRun`.

    Call :meth:`ask` with natural-language questions; prior turns are kept in
    ``conversation_history`` until :meth:`reset_conversation`.
    """

    run: AgentEvaluationRun
    model: Model
    system_prompt: str = field(default=_DEFAULT_EVAL_CHATBOT_SYSTEM_PROMPT)
    max_context_chars: int = 48_000
    prompt_input_kw: str = "text"
    quality_gates_report: Optional[Mapping[str, Any]] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list, repr=False)

    def reset_conversation(self) -> None:
        """Clear prior user/assistant turns (evaluation context is re-injected each call)."""
        self.conversation_history.clear()

    def _evaluation_context_block(self) -> str:
        if not self.run.rows:
            return "(no evaluation rows)"
        ctx = self.run.to_llm_context(layout="markdown", max_output_chars=None)
        if len(ctx) > self.max_context_chars:
            return ctx[: self.max_context_chars] + "\n\n[... evaluation context truncated ...]"
        return ctx

    def _compose_prompt(self, question: str) -> str:
        qg_cap = max(4000, self.max_context_chars // 4)
        qg_txt = _format_quality_gates_report_text(self.quality_gates_report, max_chars=qg_cap)
        parts: List[str] = [
            self.system_prompt,
            "",
        ]
        if qg_txt:
            parts.extend(
                [
                    "=== quality_gates_report ===",
                    qg_txt,
                    "",
                ],
            )
        parts.extend(
            [
                "=== evaluation_results ===",
                self._evaluation_context_block(),
                "",
            ],
        )
        if self.conversation_history:
            parts.append("=== prior_conversation ===")
            for turn in self.conversation_history:
                parts.append(f"{turn['role']}: {turn['content']}")
            parts.append("")
        parts.append(f"user: {question}")
        parts.append("assistant:")
        return "\n".join(parts)

    def _invoke_model(self, prompt: str, **kwargs: Any) -> ModelResult:
        kw = (self.prompt_input_kw or "data").strip()
        if not kw:
            raise ValidationError("prompt_input_kw must be a non-empty string")
        return self.model.run(**{kw: prompt}, **kwargs)

    def ask_with_result(self, question: str, **model_run_kwargs: Any) -> ModelResult:
        """Run the model on ``question`` and return the raw :class:`~aixplain.v2.model.ModelResult`."""
        prompt = self._compose_prompt(question)
        result = self._invoke_model(prompt, **model_run_kwargs)
        answer = _reply_text_from_model_result(result)
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})
        return result

    def ask(self, question: str, **model_run_kwargs: Any) -> str:
        """Ask a question about the run; returns assistant text only."""
        return _reply_text_from_model_result(self.ask_with_result(question, **model_run_kwargs))


_CSV_ROW_CORE_KEYS = frozenset(
    {
        "case_index",
        "query",
        "reference",
        "agent_name",
        "output",
        "agent_response",
        "status",
        "completed",
        "error_message",
        "run_time",
        "used_credits",
        "agent_run_failed",
        "agent_error_type",
        "agent_error_details",
        "request_id",
        "assets_used",
        "total_tool_calls",
        "per_asset_stats",
    }
)


def _none_if_pd_na(value: Any) -> Any:
    """Map pandas/CSV missing sentinels to ``None`` for structured fields."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _parse_assets_used_csv(value: Any) -> List[str]:
    """Parse ``assets_used`` after :func:`pandas.read_csv` (JSON string or list)."""
    v = _none_if_pd_na(value)
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    return []


def _parse_per_asset_stats_csv(value: Any) -> Dict[str, Dict[str, Any]]:
    """Parse ``per_asset_stats`` after CSV round-trip (JSON object string or dict)."""
    v = _none_if_pd_na(value)
    if v is None:
        return {}
    if isinstance(v, dict):
        out: Dict[str, Dict[str, Any]] = {}
        for k, val in v.items():
            if isinstance(val, dict):
                out[str(k)] = dict(val)
            else:
                out[str(k)] = {}
        return out
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return {}
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            out = {}
            for k, val in parsed.items():
                if isinstance(val, dict):
                    out[str(k)] = dict(val)
                else:
                    out[str(k)] = {}
            return out
    return {}


def _parse_agent_error_details_csv(value: Any) -> Optional[Dict[str, Any]]:
    """Best-effort parse of ``agent_error_details`` after CSV round-trip."""
    v = _none_if_pd_na(value)
    if v is None:
        return None
    if isinstance(v, dict):
        return dict(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            parsed = ast.literal_eval(s)
            return dict(parsed) if isinstance(parsed, dict) else None
        except (ValueError, SyntaxError):
            try:
                out = json.loads(s)
                return dict(out) if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _agent_evaluation_row_from_csv_record(record: Dict[str, Any]) -> AgentEvaluationRow:
    """Build a row from one long-format CSV record (flat ``prefix__key`` metrics)."""
    case_metadata: Dict[str, Any] = {}
    metrics: Dict[str, Dict[str, Any]] = {}
    core: Dict[str, Any] = {}
    for raw_k, raw_v in record.items():
        k = str(raw_k)
        v = _none_if_pd_na(raw_v)
        if k in _CSV_ROW_CORE_KEYS:
            core[k] = v
            continue
        if k.startswith("case_meta__"):
            case_metadata[k[len("case_meta__"):]] = v
            continue
        if "__" in k:
            prefix, suffix = k.split("__", 1)
            _metric_bucket(metrics, prefix)[suffix] = v
    ci = core.get("case_index")
    if ci is None or pd.isna(ci):
        case_index_int = 0
    else:
        case_index_int = int(ci)
    ttc = core.get("total_tool_calls")
    if ttc is None or pd.isna(ttc):
        total_tool_calls_int = 0
    else:
        total_tool_calls_int = int(ttc)
    raw_request_id = core.get("request_id")
    if raw_request_id is None or pd.isna(raw_request_id):
        request_id_parsed: Optional[str] = None
    else:
        request_id_parsed = str(raw_request_id).strip() or None
    return AgentEvaluationRow(
        case_index=case_index_int,
        query=core.get("query"),
        reference=core.get("reference"),
        agent_name=core.get("agent_name"),
        output=core.get("output"),
        agent_response=core.get("agent_response"),
        status=core.get("status"),
        completed=bool(core["completed"]) if core.get("completed") is not None else False,
        error_message=core.get("error_message"),
        run_time=float(core["run_time"] or 0.0),
        used_credits=float(core["used_credits"] or 0.0),
        agent_run_failed=bool(core["agent_run_failed"]) if core.get("agent_run_failed") is not None else False,
        agent_error_type=core.get("agent_error_type"),
        agent_error_details=_parse_agent_error_details_csv(core.get("agent_error_details")),
        case_metadata=case_metadata,
        metrics=metrics,
        request_id=request_id_parsed,
        assets_used=_parse_assets_used_csv(core.get("assets_used")),
        total_tool_calls=total_tool_calls_int,
        per_asset_stats=_parse_per_asset_stats_csv(core.get("per_asset_stats")),
    )


def _coerce_eval_float(value: Any) -> float:
    """Parse a numeric field from API payloads; missing or invalid becomes ``0.0``."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _execution_stats_from_response_data(data: Any) -> Dict[str, Any]:
    """Return ``execution_stats`` dict from :class:`AgentResponseData` or a plain dict."""
    if isinstance(data, AgentResponseData):
        raw = data.execution_stats
    elif isinstance(data, dict):
        raw = data.get("execution_stats") or data.get("executionStats")
    else:
        return {}
    if raw is None:
        return {}
    return dict(raw) if isinstance(raw, dict) else {}


def _steps_from_response_data(data: Any) -> List[Any]:
    """Return the ``steps`` list from response data."""
    if isinstance(data, AgentResponseData):
        return list(data.steps or [])
    if isinstance(data, dict):
        steps = data.get("steps")
        return list(steps) if isinstance(steps, list) else []
    return []


def _request_id_from_run_result(result: AgentRunResult) -> Optional[str]:
    rid = getattr(result, "request_id", None)
    if rid is None:
        rid = getattr(result, "requestId", None)
    if rid is None:
        return None
    s = str(rid).strip()
    return s or None


def _normalize_assets_used_list(raw: Any) -> List[str]:
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if x is not None]


def _asset_key_from_step_unit(unit: Any) -> str:
    if not isinstance(unit, dict):
        return "unknown:unknown"
    ut_raw = unit.get("type") or "unknown"
    ut = str(ut_raw).lower() if ut_raw is not None else "unknown"
    name = unit.get("name") or unit.get("id") or "unknown"
    return f"{ut}:{name}"


def _extract_execution_insights(result: AgentRunResult) -> Dict[str, Any]:
    """Derive request id, assets list, tool-call count, and per-asset time/credits from a run.

    Per-asset totals prefer step-level ``unit`` aggregation (models and tools). If
    there are no steps, falls back to ``runtime_breakdown`` / ``credit_breakdown``
    from ``execution_stats`` when present.
    """
    request_id = _request_id_from_run_result(result)
    assets_used: List[str] = []
    total_tool_calls = 0
    per_asset_from_steps: Dict[str, Dict[str, Any]] = {}

    data = getattr(result, "data", None)
    stats = _execution_stats_from_response_data(data)
    if stats:
        request_id = stats.get("request_id") or stats.get("requestId") or request_id
        assets_used = _normalize_assets_used_list(
            stats.get("assets_used") or stats.get("assetsUsed") or [],
        )

    for step in _steps_from_response_data(data):
        if not isinstance(step, dict):
            continue
        unit = step.get("unit")
        if isinstance(unit, dict):
            utype = unit.get("type")
            if isinstance(utype, str) and utype.lower() == "tool":
                total_tool_calls += 1
        key = _asset_key_from_step_unit(unit)
        bucket = per_asset_from_steps.setdefault(
            key,
            {"run_time": 0.0, "used_credits": 0.0, "n_steps": 0},
        )
        bucket["run_time"] = float(bucket["run_time"]) + _coerce_eval_float(step.get("run_time"))
        bucket["used_credits"] = float(bucket["used_credits"]) + _coerce_eval_float(step.get("used_credits"))
        bucket["n_steps"] = int(bucket["n_steps"]) + 1

    per_asset_final: Dict[str, Dict[str, Any]] = {}
    if per_asset_from_steps:
        per_asset_final = per_asset_from_steps
    elif stats:
        rt_bd = stats.get("runtime_breakdown") or stats.get("runtimeBreakdown") or {}
        cr_bd = stats.get("credit_breakdown") or stats.get("creditBreakdown") or {}
        keys: set[Any] = set()
        if isinstance(rt_bd, dict):
            keys.update(rt_bd.keys())
        if isinstance(cr_bd, dict):
            keys.update(cr_bd.keys())
        for k in keys:
            ks = str(k)
            per_asset_final[ks] = {
                "run_time": _coerce_eval_float(rt_bd.get(k)) if isinstance(rt_bd, dict) else 0.0,
                "used_credits": _coerce_eval_float(cr_bd.get(k)) if isinstance(cr_bd, dict) else 0.0,
                "n_steps": 0,
            }

    return {
        "request_id": request_id,
        "assets_used": assets_used,
        "total_tool_calls": total_tool_calls,
        "per_asset_stats": per_asset_final,
    }


def _extract_agent_output(result: AgentRunResult) -> Any:
    """Best-effort extraction of the primary agent output from a run result."""
    data = result.data
    if data is None:
        return result.result
    if isinstance(data, AgentResponseData):
        return data.output
    return data


def _metric_tool_prefix(tool: MetricTool, index: int) -> str:
    """Stable column prefix for a metric tool."""
    if tool.name:
        return str(tool.name)
    if tool.id:
        return str(tool.id)
    return f"metric_{index}"


def _metric_bucket(metrics: Dict[str, Dict[str, Any]], prefix: str) -> Dict[str, Any]:
    """Return the nested dict for a metric tool prefix, creating it if needed."""
    return metrics.setdefault(prefix, {})


def _merge_metric_columns(
    metrics: Dict[str, Dict[str, Any]],
    prefix: str,
    metric_result: MetricToolResponse,
    metric_tool: Optional[MetricTool] = None,
) -> None:
    """Write metric tool output into ``metrics[prefix]`` (legacy flat keys: ``prefix__*``)."""
    b = _metric_bucket(metrics, prefix)
    b["metric_status"] = metric_result.status
    b["metric_completed"] = metric_result.completed
    data = metric_result.validated_data
    if isinstance(data, dict):
        for key, val in data.items():
            b[key] = val
    elif data is not None:
        b["value"] = data
    _apply_metric_pass_for_threshold(b, metric_tool)


def _eval_exception_message(exc: Exception) -> str:
    """Human-readable message for a row ``error_message`` column."""
    if isinstance(exc, AixplainV2Error):
        return str(exc.message)
    return str(exc)


def _eval_agent_error_details(exc: Exception) -> Optional[Dict[str, Any]]:
    """Structured details for API/SDK errors; ``None`` if not available."""
    if isinstance(exc, AixplainV2Error) and exc.details:
        return dict(exc.details)
    return None


def _record_metric_failure(metrics: Dict[str, Dict[str, Any]], prefix: str, exc: Exception) -> None:
    """Record a metric tool failure without aborting the evaluation row."""
    b = _metric_bucket(metrics, prefix)
    b["metric_status"] = "FAILED"
    b["metric_completed"] = False
    b["metric_error"] = _eval_exception_message(exc)
    b["metric_error_type"] = type(exc).__name__


def _record_metrics_skipped_for_agent_failure(metrics: Dict[str, Dict[str, Any]], prefix: str) -> None:
    """Record that metrics were not run because the agent run failed."""
    b = _metric_bucket(metrics, prefix)
    b["metric_status"] = "SKIPPED"
    b["metric_completed"] = False
    b["metric_skipped"] = True
    b["metric_skip_reason"] = "agent_run_failed"


def _normalize_agents(agents: Union[Agent, Sequence[Agent]]) -> List[Agent]:
    if isinstance(agents, Agent):
        return [agents]
    if isinstance(agents, (list, tuple)):
        agent_list = list(agents)
        if not agent_list:
            raise ValueError("At least one agent is required")
        return agent_list
    return [agents]


def _coerce_object_bool(series: pd.Series) -> pd.Series:
    """Parse common string boolean forms produced by CSV export."""
    return series.map(lambda x: str(x).lower() in ("true", "1", "yes"))


def normalize_eval_results_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of evaluator results with stable dtypes after CSV round-trip.

    :meth:`AgentEvaluationRun.to_dataframe` (or CSV from ``to_csv``) followed by
    :func:`pandas.read_csv` often yields object dtypes for booleans and occasionally
    mis-typed integers. Use this on frames loaded from disk before calling helpers
    such as :func:`~aixplain.v2.eval_results_display.pivot_agents_wide` or
    :func:`~aixplain.v2.eval_results_display.summarize_by_agent`.

    Only columns that exist are touched; unknown columns are left unchanged.

    Args:
        df: Long-format evaluation results.

    Returns:
        A new DataFrame; the input is not modified.
    """
    out = df.copy()
    if "case_index" in out.columns:
        out["case_index"] = pd.to_numeric(out["case_index"], errors="coerce").astype("Int64")
    for col in ("agent_run_failed", "completed"):
        if col not in out.columns:
            continue
        s = out[col]
        if pd.api.types.is_bool_dtype(s):
            continue
        if pd.api.types.is_numeric_dtype(s):
            out[col] = s.astype(bool)
        else:
            out[col] = _coerce_object_bool(s.astype("object"))
    for col in ("run_time", "used_credits"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "total_tool_calls" in out.columns:
        out["total_tool_calls"] = pd.to_numeric(out["total_tool_calls"], errors="coerce").fillna(0).astype(int)
    if "assets_used" in out.columns:
        out["assets_used"] = out["assets_used"].map(_parse_assets_used_csv)
    if "per_asset_stats" in out.columns:
        out["per_asset_stats"] = out["per_asset_stats"].map(_parse_per_asset_stats_csv)
    for col in out.columns:
        if col in (
            "case_index",
            "agent_run_failed",
            "completed",
            "run_time",
            "used_credits",
            "total_tool_calls",
            "assets_used",
            "per_asset_stats",
        ):
            continue
        if col.startswith("case_meta__"):
            continue
        if str(col).endswith("__metric_pass"):
            s = out[col]
            if pd.api.types.is_bool_dtype(s):
                continue
            if pd.api.types.is_numeric_dtype(s):
                out[col] = s.astype(bool)
            else:
                out[col] = _coerce_object_bool(s.astype("object"))
            continue
        if not _is_metric_data_column(col):
            continue
        s = out[col]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            numeric = pd.to_numeric(s, errors="coerce")
            if numeric.notna().all():
                out[col] = numeric
    return out


def _default_side_by_side_value_columns(df: pd.DataFrame) -> List[str]:
    """Pick ``output`` plus metric columns that look like scores (not reasoning text)."""
    out: List[str] = []
    if "output" in df.columns:
        out.append("output")
    for col in df.columns:
        if col == "output":
            continue
        if not _is_metric_data_column(col):
            continue
        lower = str(col).lower()
        if lower.endswith("__score") or lower.endswith("__scores"):
            out.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            out.append(col)
    return out


def compare_agents_side_by_side(
    results: Union[pd.DataFrame, AgentEvaluationRun],
    *,
    value_columns: Optional[Sequence[str]] = None,
    include_query: bool = True,
    include_reference: bool = False,
) -> pd.DataFrame:
    """Pivot long evaluator results so each case is one row and agents are columns.

    Typical long output (one row per case per agent, from
    :class:`AgentEvaluationRun` or ``results.csv`` from ``to_dataframe().to_csv``)
    is normalized with :func:`normalize_eval_results_dataframe`, then pivoted.
    By default only ``output`` and metric **score** fields are included (columns
    ending with ``__score`` / ``__scores``, or other numeric metric payload columns
    such as ``m1__bleu``). Pass ``value_columns`` to override.

    Result columns look like ``output__<agent_name>`` and
    ``aws-correctness__score__<agent_name>``. Optional ``query`` / ``reference``
    are one column each per case (not split by agent).

    Args:
        results: Long-format :class:`pandas.DataFrame` or :class:`AgentEvaluationRun`.
        value_columns: Fields to spread by ``agent_name``; default is score-like
            columns only plus ``output``.
        include_query: If True and ``query`` is present, add a single ``query``
            column per ``case_index``.
        include_reference: Same for ``reference``.

    Returns:
        Wide DataFrame with ``case_index`` as the first column. Empty input
        yields an empty DataFrame.

    Raises:
        ValidationError: If required columns are missing or ``value_columns``
            references absent columns.
    """
    df = results.to_dataframe() if isinstance(results, AgentEvaluationRun) else results
    for required in ("case_index", "agent_name"):
        if required not in df.columns:
            raise ValidationError(f"DataFrame must include column {required!r}")
    work = normalize_eval_results_dataframe(df)
    if work.empty:
        return pd.DataFrame()
    cols = list(value_columns) if value_columns is not None else _default_side_by_side_value_columns(work)
    if not cols:
        raise ValidationError(
            "No value columns to compare; add output/metric scores or pass value_columns.",
        )
    for col in cols:
        if col not in work.columns:
            raise ValidationError(f"Missing value column {col!r}")
    meta_frames: List[pd.DataFrame] = []
    if include_query and "query" in work.columns:
        q = work.drop_duplicates(subset=["case_index"]).set_index("case_index")["query"]
        meta_frames.append(q.to_frame())
    if include_reference and "reference" in work.columns:
        r = work.drop_duplicates(subset=["case_index"]).set_index("case_index")["reference"]
        meta_frames.append(r.to_frame())
    pivoted: List[pd.DataFrame] = []
    for col in cols:
        pt = work.pivot_table(index="case_index", columns="agent_name", values=col, aggfunc="first")
        pt = pt.rename(columns=lambda a: f"{col}__{a}")
        pivoted.append(pt)
    wide = pd.concat(meta_frames + pivoted, axis=1)
    return wide.reset_index()


class AgentEvaluationExecutor:
    """Runs eval cases across agents, runs metric tools, returns :class:`AgentEvaluationRun`.

    For each pair of (case, agent) the executor calls ``agent.run`` with the
    case's ``query``. Each :class:`MetricTool` is invoked with ``run`` payload
    ``data`` containing at least ``output`` (agent output) and ``reference``
    (from the case, may be ``None``). Metric results are nested under
    ``AgentEvaluationRow.metrics[prefix]`` using the tool's ``name``, ``id``, or
    ``metric_<n>`` as prefix (see :meth:`AgentEvaluationRun.to_dataframe` for the
    legacy ``<prefix>__<key>`` flat layout).

    Set ``cache_experiments=False`` to skip writing :class:`~aixplain.v2.eval_experiment.Experiment`
    snapshots to the local cache after each :meth:`Experiment.run`. Use
    ``experiment_cache_dir`` to override the default cache directory.
    """

    def __init__(
        self,
        *,
        cache_experiments: bool = True,
        experiment_cache_dir: Optional[Union[str, Path]] = None,
        autosave_eval_runs: Optional[bool] = None,
    ) -> None:
        """Configure optional local persistence for :class:`~aixplain.v2.eval_experiment.Experiment`.

        Args:
            cache_experiments: When True (default), experiments created via
                :meth:`create_experiment` are saved to disk after :meth:`~aixplain.v2.eval_experiment.Experiment.run`.
            experiment_cache_dir: Root directory for experiment JSON files; defaults to a
                platform-appropriate user cache path (see :func:`~aixplain.v2.eval_experiment.default_experiment_cache_dir`).
            autosave_eval_runs: Deprecated alias for ``cache_experiments`` when not ``None``.
        """
        if autosave_eval_runs is not None:
            cache_experiments = bool(autosave_eval_runs)
        self.cache_experiments = cache_experiments
        self.experiment_cache_dir: Optional[Path] = (
            Path(experiment_cache_dir) if experiment_cache_dir is not None else None
        )

    def _experiment_cache_store(self) -> ExperimentLocalCache:
        from .eval_experiment import ExperimentLocalCache, default_experiment_cache_dir

        base = self.experiment_cache_dir if self.experiment_cache_dir is not None else default_experiment_cache_dir()
        return ExperimentLocalCache(base)

    def create_experiment(
        self,
        agents: Union[Agent, Sequence[Agent]],
        cases: Sequence[EvalCase],
        metrics: Optional[Sequence[MetricTool]] = None,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Experiment:
        """Build an :class:`~aixplain.v2.eval_experiment.Experiment` bound to this executor.

        Snapshots ``agents`` and ``metrics`` via ``to_dict()`` for provenance and cache
        reload. Call :meth:`~aixplain.v2.eval_experiment.Experiment.run` to execute and
        append an :class:`~aixplain.v2.eval_experiment.ExperimentRun`.

        Args:
            agents: Agent or sequence evaluated against ``cases``.
            cases: Evaluation cases (dataset).
            metrics: Optional metric tools.
            metadata: Arbitrary JSON-serializable metadata stored on the experiment.

        Returns:
            A new experiment with a unique id and creation timestamp.
        """
        from .eval_experiment import Experiment as ExperimentCls
        from .eval_experiment import _agent_snapshot, _metric_snapshot
        import uuid
        from datetime import datetime, timezone

        agents_list = _normalize_agents(agents)
        metrics_list = list(metrics) if metrics is not None else []
        exp = ExperimentCls(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            metadata=dict(metadata or {}),
            dataset=list(cases),
            agents_snapshot=[_agent_snapshot(a) for a in agents_list],
            metrics_snapshot=[_metric_snapshot(m) for m in metrics_list],
            runs=[],
            _agents=tuple(agents_list),
            _metrics=tuple(metrics_list) if metrics_list else None,
            _executor=self,
        )
        if self.cache_experiments:
            self._experiment_cache_store().save(exp)
        return exp

    def list_cached_experiments(self) -> List[Dict[str, Any]]:
        """List experiments on disk under this executor's cache directory."""
        return self._experiment_cache_store().list_experiments()

    def load_cached_experiment(self, experiment_id: str) -> Experiment:
        """Load a cached experiment and bind this executor for subsequent :meth:`~aixplain.v2.eval_experiment.Experiment.run` calls."""
        return self._experiment_cache_store().load_experiment(experiment_id, executor=self)

    @classmethod
    def create_dataset_from_list(cls, query_list: List[str]) -> List[EvalCase]:
        """Create a list of evaluation cases from a list of query strings."""
        return [EvalCase(query=query) for query in query_list]

    @classmethod
    def create_dataset_from_csv(
        cls,
        path: Union[str, Path, Any],
        *,
        query_column: str = "query",
        reference_column: Optional[str] = "reference",
        metadata_columns: Optional[Sequence[str]] = None,
        **read_csv_kwargs: Any,
    ) -> List[EvalCase]:
        """Build :class:`EvalCase` rows from a CSV with at least a query column.

        Args:
            path: CSV path or file-like accepted by :func:`pandas.read_csv`.
            query_column: Column name used as ``EvalCase.query``.
            reference_column: Column for ``EvalCase.reference``, or ``None`` to skip.
            metadata_columns: Optional column names merged into each case's ``metadata``.
            **read_csv_kwargs: Forwarded to :func:`pandas.read_csv`.

        Returns:
            List of cases; header-only CSV yields an empty list.

        Raises:
            ValidationError: If the query column is missing or a row has an empty query.
        """
        if isinstance(path, (str, Path)):
            df = pd.read_csv(Path(path), **read_csv_kwargs)
        else:
            df = pd.read_csv(path, **read_csv_kwargs)
        if df.empty:
            return []
        if query_column not in df.columns:
            raise ValidationError(f"CSV must include query column {query_column!r}")
        meta_cols = list(metadata_columns) if metadata_columns else []
        out: List[EvalCase] = []
        for _, row in df.iterrows():
            raw_q = row[query_column]
            if pd.isna(raw_q):
                raise ValidationError("Empty query row in dataset CSV.")
            q = raw_q.strip() if isinstance(raw_q, str) else raw_q
            if isinstance(q, str) and not q:
                raise ValidationError("Empty query row in dataset CSV.")
            ref: Optional[Any] = None
            if reference_column is not None and reference_column in df.columns:
                v = row[reference_column]
                ref = None if pd.isna(v) else v
            meta: Dict[str, Any] = {}
            for col in meta_cols:
                if col in df.columns:
                    v = row[col]
                    meta[col] = None if pd.isna(v) else v
            out.append(EvalCase(query=q, reference=ref, metadata=meta if meta else None))
        return out

    @classmethod
    def load_from_csv(
        cls,
        path: Union[str, Path, Any],
        *,
        normalize: bool = True,
        **read_csv_kwargs: Any,
    ) -> AgentEvaluationRun:
        """Load a CSV written by :meth:`AgentEvaluationRun.to_dataframe` into a structured run.

        Unknown columns (for example a legacy ``agent_id`` column) are ignored.
        Flat ``<metric_prefix>__<field>`` columns are split into
        ``AgentEvaluationRow.metrics``.

        Args:
            path: Path to the CSV file, or a file-like object accepted by
                :func:`pandas.read_csv`.
            normalize: If True, run :func:`normalize_eval_results_dataframe` so dtypes
                match in-memory evaluation results.
            **read_csv_kwargs: Forwarded to :func:`pandas.read_csv`.

        Returns:
            :class:`AgentEvaluationRun` with one row per CSV record.

        Raises:
            ValidationError: If the CSV is non-empty but missing ``case_index`` or
                ``agent_name``.
        """
        if isinstance(path, (str, Path)):
            df = pd.read_csv(Path(path), **read_csv_kwargs)
        else:
            df = pd.read_csv(path, **read_csv_kwargs)
        if normalize:
            df = normalize_eval_results_dataframe(df)
        if df.empty:
            return AgentEvaluationRun(rows=[])
        for required in ("case_index", "agent_name"):
            if required not in df.columns:
                raise ValidationError(f"CSV must include column {required!r}")
        rows = [_agent_evaluation_row_from_csv_record(rec) for rec in df.to_dict("records")]
        return AgentEvaluationRun(rows=rows)

    def evaluate(
        self,
        agents: Union[Agent, Sequence[Agent]],
        cases: Sequence[EvalCase],
        metrics: Optional[Sequence[MetricTool]] = None,
        **agent_run_kwargs: Any,
    ) -> AgentEvaluationRun:
        """Execute all cases against all agents and build a structured result.

        Args:
            agents: A single :class:`~aixplain.v2.agent.Agent` or a sequence of agents.
            cases: Evaluation cases to run.
            metrics: Optional sequence of :class:`MetricTool` instances. When a
                tool sets :attr:`MetricTool.threshold`, each successful metric row
                includes ``metric_pass`` (boolean) from the score and threshold.
            **agent_run_kwargs: Forwarded to each ``agent.run`` call.

        Returns:
            :class:`AgentEvaluationRun` with one :class:`AgentEvaluationRow` per
            (case, agent). Agent or metric failures are recorded per row instead of
            aborting the batch. Empty ``cases`` yields an empty run.
        """
        out_rows: List[AgentEvaluationRow] = []
        metrics_list: List[MetricTool] = list(metrics) if metrics is not None else []
        agents_list: List[Agent] = _normalize_agents(agents)

        for case_index, case in enumerate(cases):
            for agent in agents_list:
                case_metadata = dict(case.metadata) if case.metadata else {}
                metrics_by_prefix: Dict[str, Dict[str, Any]] = {}
                result: Optional[AgentRunResult] = None
                try:
                    result = agent.run(case.query, **agent_run_kwargs)
                except Exception as exc:
                    out_rows.append(
                        AgentEvaluationRow(
                            case_index=case_index,
                            query=case.query,
                            reference=case.reference,
                            agent_name=getattr(agent, "name", None),
                            output=None,
                            agent_response=None,
                            status="FAILED",
                            completed=False,
                            error_message=_eval_exception_message(exc),
                            run_time=0.0,
                            used_credits=0.0,
                            agent_run_failed=True,
                            agent_error_type=type(exc).__name__,
                            agent_error_details=_eval_agent_error_details(exc),
                            case_metadata=case_metadata,
                            metrics=metrics_by_prefix,
                            request_id=None,
                            assets_used=[],
                            total_tool_calls=0,
                            per_asset_stats={},
                        )
                    )
                    for metric_index, metric_tool in enumerate(metrics_list):
                        prefix = _metric_tool_prefix(metric_tool, metric_index)
                        _record_metrics_skipped_for_agent_failure(metrics_by_prefix, prefix)
                    continue

                assert result is not None
                output = _extract_agent_output(result)
                ex_insights = _extract_execution_insights(result)
                out_rows.append(
                    AgentEvaluationRow(
                        case_index=case_index,
                        query=case.query,
                        reference=case.reference,
                        agent_name=getattr(agent, "name", None),
                        output=output,
                        agent_response=result.data,
                        status=result.status,
                        completed=result.completed,
                        error_message=result.error_message,
                        run_time=result.run_time,
                        used_credits=result.used_credits,
                        agent_run_failed=False,
                        agent_error_type=None,
                        agent_error_details=None,
                        case_metadata=case_metadata,
                        metrics=metrics_by_prefix,
                        request_id=ex_insights["request_id"],
                        assets_used=ex_insights["assets_used"],
                        total_tool_calls=ex_insights["total_tool_calls"],
                        per_asset_stats=ex_insights["per_asset_stats"],
                    )
                )
                current = out_rows[-1]
                for metric_index, metric_tool in enumerate(metrics_list):
                    prefix = _metric_tool_prefix(metric_tool, metric_index)
                    try:
                        metric_result = metric_tool.measure(result.data)
                        _merge_metric_columns(current.metrics, prefix, metric_result, metric_tool)
                    except Exception as exc:
                        _record_metric_failure(current.metrics, prefix, exc)

        return AgentEvaluationRun(rows=out_rows)
