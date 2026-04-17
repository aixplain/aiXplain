"""Agent evaluation utilities for aiXplain v2 SDK.

Provides a minimal executor that runs evaluation cases through one or more
:class:`~aixplain.v2.agent.Agent` instances, runs optional :class:`MetricTool`
instances, and aggregates rows into a :class:`pandas.DataFrame`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import json
import re

import pandas as pd
from dataclasses_json import config as dj_config, dataclass_json

from .agent import Agent, AgentResponseData, AgentRunResult
from .eval_results_display import _is_metric_data_column
from .exceptions import AixplainV2Error, ValidationError, create_operation_failed_error
from .resource import Result
from .tool import Tool


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
    """

    RESPONSE_CLASS = MetricToolResponse
    prompt_template: Optional[str] = field(default=None, metadata=dj_config(field_name="promptTemplate"))
    llm_path: Optional[str] = field(default=None, metadata=dj_config(field_name="llmPath"))
    agent_response_data_fields: AgentResponseDataFields = field(
        default_factory=AgentResponseDataFields,
        metadata=dj_config(field_name="agentResponseDataFields"),
    )
    additional_input_prompt: Optional[str] = field(default=None, metadata=dj_config(field_name="additionalInputPrompt"))

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


def _merge_metric_columns(row: Dict[str, Any], prefix: str, metric_result: MetricToolResponse) -> None:
    """Flatten metric tool output into row columns with ``prefix__*`` keys."""
    row[f"{prefix}__metric_status"] = metric_result.status
    row[f"{prefix}__metric_completed"] = metric_result.completed
    data = metric_result.validated_data
    if isinstance(data, dict):
        for key, val in data.items():
            row[f"{prefix}__{key}"] = val
    elif data is not None:
        row[f"{prefix}__value"] = data


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


def _record_metric_failure(row: Dict[str, Any], prefix: str, exc: Exception) -> None:
    """Record a metric tool failure without aborting the evaluation row."""
    row[f"{prefix}__metric_status"] = "FAILED"
    row[f"{prefix}__metric_completed"] = False
    row[f"{prefix}__metric_error"] = _eval_exception_message(exc)
    row[f"{prefix}__metric_error_type"] = type(exc).__name__


def _record_metrics_skipped_for_agent_failure(row: Dict[str, Any], prefix: str) -> None:
    """Record that metrics were not run because the agent run failed."""
    row[f"{prefix}__metric_skipped"] = True
    row[f"{prefix}__metric_skip_reason"] = "agent_run_failed"


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

    :meth:`AgentEvaluationExecutor.evaluate` returns typed columns, but
    ``DataFrame.to_csv`` followed by :func:`pandas.read_csv` often yields object
    dtypes for booleans and occasionally mis-typed integers. Use this on frames
    loaded from disk (for example ``results.csv`` from ``df.to_csv``) before
    calling helpers such as :func:`~aixplain.v2.eval_results_display.pivot_agents_wide`
    or :func:`~aixplain.v2.eval_results_display.summarize_by_agent`.

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
    for col in out.columns:
        if col in ("case_index", "agent_run_failed", "completed", "run_time", "used_credits"):
            continue
        if col.startswith("case_meta__"):
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
    df: pd.DataFrame,
    *,
    value_columns: Optional[Sequence[str]] = None,
    include_query: bool = True,
    include_reference: bool = False,
) -> pd.DataFrame:
    """Pivot long evaluator results so each case is one row and agents are columns.

    Typical long output (one row per case per agent, as from
    :meth:`AgentEvaluationExecutor.evaluate` or ``results.csv`` from
    ``df.to_csv``) is normalized with :func:`normalize_eval_results_dataframe`,
    then pivoted. By default only ``output`` and metric **score** fields are
    included (columns ending with ``__score`` / ``__scores``, or other numeric
    metric payload columns such as ``m1__bleu``). Pass ``value_columns`` to
    override.

    Result columns look like ``output__<agent_name>`` and
    ``aws-correctness__score__<agent_name>``. Optional ``query`` / ``reference``
    are one column each per case (not split by agent).

    Args:
        df: Long-format evaluation results.
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
    """Runs eval cases across agents, runs metric tools, returns a DataFrame.

    For each pair of (case, agent) the executor calls ``agent.run`` with the
    case's ``query``. Each :class:`MetricTool` is invoked with ``run`` payload
    ``data`` containing at least ``output`` (agent output) and ``reference``
    (from the case, may be ``None``). Metric results are flattened into columns
    ``<metric_prefix>__<key>`` using the tool's ``name``, ``id``, or
    ``metric_<n>`` as prefix.
    """

    @classmethod
    def create_dataset_from_list(cls, query_list: List[str]) -> List[EvalCase]:
        """Create a list of evaluation cases from a list of query strings."""
        return [EvalCase(query=query) for query in query_list]

    def evaluate(
        self,
        agents: Union[Agent, Sequence[Agent]],
        cases: Sequence[EvalCase],
        metrics: Optional[Sequence[MetricTool]] = None,
        **agent_run_kwargs: Any,
    ) -> pd.DataFrame:
        """Execute all cases against all agents and build a result DataFrame.

        Args:
            agents: A single :class:`~aixplain.v2.agent.Agent` or a sequence of agents.
            cases: Evaluation cases to run.
            metrics: Optional sequence of :class:`MetricTool` instances.
            **agent_run_kwargs: Forwarded to each ``agent.run`` call.

        Returns:
            A DataFrame with one row per (case, agent); metric columns use the
            ``<prefix>__<key>`` pattern. Agent or metric failures are recorded per
            row (``agent_run_failed``, ``<prefix>__metric_error``, etc.) instead
            of aborting the batch. Empty ``cases`` yields an empty DataFrame with
            the standard column set.
        """
        rows: List[Dict[str, Any]] = []
        metrics_list: List[MetricTool] = list(metrics) if metrics is not None else []
        agents_list: List[Agent] = _normalize_agents(agents)

        for case_index, case in enumerate(cases):
            for agent in agents_list:
                row: Dict[str, Any] = {
                    "case_index": case_index,
                    "query": case.query,
                    "reference": case.reference,
                    "agent_name": getattr(agent, "name", None),
                }

                agent_run_failed = False
                try:
                    result = agent.run(case.query, **agent_run_kwargs)
                except Exception as exc:
                    agent_run_failed = True
                    row["output"] = None
                    row["agent_response"] = None
                    row["status"] = "FAILED"
                    row["completed"] = False
                    row["error_message"] = _eval_exception_message(exc)
                    row["run_time"] = 0.0
                    row["used_credits"] = 0.0
                    row["agent_run_failed"] = True
                    row["agent_error_type"] = type(exc).__name__
                    row["agent_error_details"] = _eval_agent_error_details(exc)
                else:
                    output = _extract_agent_output(result)
                    row["output"] = output
                    row["agent_response"] = result.data
                    row["status"] = result.status
                    row["completed"] = result.completed
                    row["error_message"] = result.error_message
                    row["run_time"] = result.run_time
                    row["used_credits"] = result.used_credits
                    row["agent_run_failed"] = False
                    row["agent_error_type"] = None
                    row["agent_error_details"] = None

                if case.metadata:
                    for meta_key, meta_val in case.metadata.items():
                        row[f"case_meta__{meta_key}"] = meta_val

                for metric_index, metric_tool in enumerate(metrics_list):
                    prefix = _metric_tool_prefix(metric_tool, metric_index)
                    if agent_run_failed:
                        _record_metrics_skipped_for_agent_failure(row, prefix)
                    else:
                        try:
                            metric_result = metric_tool.measure(result.data)
                            _merge_metric_columns(row, prefix, metric_result)
                        except Exception as exc:
                            _record_metric_failure(row, prefix, exc)

                rows.append(row)

        if not rows:
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
                    "agent_run_failed",
                    "agent_error_type",
                    "agent_error_details",
                ]
            )

        return pd.DataFrame(rows)
