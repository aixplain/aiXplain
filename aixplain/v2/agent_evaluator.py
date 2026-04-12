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
