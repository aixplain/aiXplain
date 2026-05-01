"""Experiment definitions and local filesystem cache for agent evaluations."""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from .agent import Agent
from .exceptions import ValidationError
from .eval_results_display import _is_metric_data_column

from .agent_evaluator import (
    AgentEvaluationRun,
    EvalCase,
    MetricTool,
    _agent_evaluation_row_from_csv_record,
    _normalize_agents,
    normalize_eval_results_dataframe,
)

_CACHE_FORMAT_VERSION = 1

# Default x-axis column for :meth:`Experiment.plot_runs_regression` (human-readable frame).
EXPERIMENT_COMPARISON_COL_RUN_INDEX = "Run index"
EXPERIMENT_COMPARISON_COL_RUN_CREATED_AT = "Run created at (UTC)"

_MACHINE_RUN_IDENTITY_KEYS: Dict[str, str] = {
    "run_index": EXPERIMENT_COMPARISON_COL_RUN_INDEX,
    "run_id": "Run ID",
    "run_created_at": EXPERIMENT_COMPARISON_COL_RUN_CREATED_AT,
}

_MACHINE_SUMMARY_SCALAR_KEYS: Dict[str, str] = {
    "total_cost": "Total credits (sum)",
    "total_time_seconds": "Total run time (s)",
    "total_samples": "Unique cases (count)",
    "rows_evaluated": "Evaluation rows (count)",
    "n_agent_failures": "Agent failures (count)",
    "agent_failure_rate": "Agent failure rate",
    "total_tool_calls": "Tool calls (total)",
    "mean_used_credits_per_row": "Avg credits per evaluation row",
    "mean_run_time_seconds_per_row": "Avg run time per row (s)",
}

_AGENT_SUMMARY_FIELD_LABELS: Dict[str, str] = {
    "rows": "Evaluation rows",
    "n_failures": "Failures (count)",
    "failure_rate": "Failure rate",
    "total_cost": "Credits used (sum)",
    "total_time_seconds": "Run time (s, sum)",
    "total_tool_calls": "Tool calls (sum)",
}

_METRIC_PASS_STAT_LABELS: Dict[str, str] = {
    "pass_rate": "Pass rate",
    "passed": "Passed (count)",
    "evaluated": "Evaluated (count)",
}


def default_experiment_cache_dir() -> Path:
    """Return the default directory for experiment cache files."""
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return root / "aixplain" / "experiments"
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "aixplain" / "experiments"
    return Path.home() / ".cache" / "aixplain" / "experiments"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_dt(value: str) -> datetime:
    raw = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if raw.tzinfo is None:
        return raw.replace(tzinfo=timezone.utc)
    return raw


def _eval_case_to_dict(c: EvalCase) -> Dict[str, Any]:
    return {"query": c.query, "reference": c.reference, "metadata": dict(c.metadata) if c.metadata else None}


def _eval_case_from_dict(d: Dict[str, Any]) -> EvalCase:
    return EvalCase(
        query=d["query"],
        reference=d.get("reference"),
        metadata=dict(d["metadata"]) if d.get("metadata") else None,
    )


def _agent_snapshot(agent: Agent) -> Dict[str, Any]:
    to_dict = getattr(agent, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    raise ValidationError("Each agent must provide a to_dict() method for experiment snapshots.")


def _metric_snapshot(tool: MetricTool) -> Dict[str, Any]:
    to_dict = getattr(tool, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    raise ValidationError("Each metric tool must provide a to_dict() method for experiment snapshots.")


def _serialize_evaluation_records(run: AgentEvaluationRun) -> List[Dict[str, Any]]:
    df = run.to_dataframe()
    if df.empty:
        return []
    blob = df.to_json(orient="records", date_format="iso")
    return json.loads(blob) if blob else []


def _deserialize_evaluation_records(records: List[Dict[str, Any]]) -> AgentEvaluationRun:
    if not records:
        return AgentEvaluationRun(rows=[])
    df = pd.DataFrame(records)
    df = normalize_eval_results_dataframe(df)
    rows = [_agent_evaluation_row_from_csv_record(rec) for rec in df.to_dict("records")]
    return AgentEvaluationRun(rows=rows)


def _flatten_run_summary_for_experiment_trends(summary: Dict[str, Any], results: AgentEvaluationRun) -> Dict[str, Any]:
    """Scalar and shallow-nested fields from :meth:`AgentEvaluationRun.run_summary` plus derived means."""
    out: Dict[str, Any] = {}
    for key in (
        "total_cost",
        "total_time_seconds",
        "total_samples",
        "rows_evaluated",
        "n_agent_failures",
        "agent_failure_rate",
        "total_tool_calls",
    ):
        if key in summary:
            out[key] = summary[key]
    rows_ev = int(summary.get("rows_evaluated") or 0)
    if rows_ev > 0:
        out["mean_used_credits_per_row"] = float(summary.get("total_cost", 0.0) or 0.0) / float(rows_ev)
        out["mean_run_time_seconds_per_row"] = float(summary.get("total_time_seconds", 0.0) or 0.0) / float(rows_ev)
    else:
        out["mean_used_credits_per_row"] = 0.0
        out["mean_run_time_seconds_per_row"] = 0.0

    mpr = summary.get("metric_pass_rates") or {}
    if isinstance(mpr, dict):
        for prefix, block in mpr.items():
            if isinstance(block, dict) and "pass_rate" in block:
                out[f"metric_pass_rate__{prefix}"] = float(block.get("pass_rate", 0.0))

    per_agent = summary.get("per_agent") or {}
    if isinstance(per_agent, dict):
        for agent_name, block in per_agent.items():
            if not isinstance(block, dict):
                continue
            safe = str(agent_name).replace("__", "_")
            pre = f"per_agent__{safe}"
            for k, v in block.items():
                if isinstance(v, (int, float, str, bool)) or v is None:
                    out[f"{pre}__{k}"] = v
                elif isinstance(v, dict):
                    for subk, subv in v.items():
                        if isinstance(subv, (int, float, str, bool)) or subv is None:
                            out[f"{pre}__{k}__{subk}"] = subv

    rdf = results.to_dataframe()
    if not rdf.empty:
        for col in rdf.columns:
            if not _is_metric_data_column(str(col)):
                continue
            if pd.api.types.is_numeric_dtype(rdf[col]):
                out[f"mean_metric__{col}"] = float(pd.to_numeric(rdf[col], errors="coerce").mean())

    return out


def _humanize_metric_pass_rate_key(machine_key: str) -> str:
    prefix = machine_key[len("metric_pass_rate__") :]
    return f"Pass rate ({prefix})"


def _humanize_mean_metric_key(machine_key: str) -> str:
    suffix = machine_key[len("mean_metric__") :]
    return "Average metric: " + suffix.replace("__", " / ")


def _humanize_per_agent_machine_key(machine_key: str) -> str:
    """Turn ``per_agent__<agent>__...`` machine keys into readable column titles."""
    if not machine_key.startswith("per_agent__"):
        return machine_key
    parts = machine_key.split("__")
    if len(parts) < 3:
        return machine_key.replace("__", " / ")
    agent = parts[1]
    tail = parts[2:]
    if len(tail) >= 3 and tail[0] == "metric_pass":
        metric = tail[1]
        stat = tail[2]
        stat_label = _METRIC_PASS_STAT_LABELS.get(stat, stat.replace("_", " ").title())
        rest = tail[3:]
        if rest:
            stat_label = f"{stat_label} ({' / '.join(rest)})"
        return f"{agent}: {stat_label} ({metric})"
    if len(tail) == 1:
        field = tail[0]
        label = _AGENT_SUMMARY_FIELD_LABELS.get(field, field.replace("_", " ").title())
        return f"{agent}: {label}"
    return f"{agent}: {' / '.join(t.replace('_', ' ') for t in tail)}"


def _humanize_experiment_comparison_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map internal comparison keys to human-oriented column names."""
    out: Dict[str, Any] = {}
    for key, val in row.items():
        if key in _MACHINE_RUN_IDENTITY_KEYS:
            out[_MACHINE_RUN_IDENTITY_KEYS[key]] = val
        elif key in _MACHINE_SUMMARY_SCALAR_KEYS:
            out[_MACHINE_SUMMARY_SCALAR_KEYS[key]] = val
        elif key.startswith("metric_pass_rate__"):
            out[_humanize_metric_pass_rate_key(key)] = val
        elif key.startswith("mean_metric__"):
            out[_humanize_mean_metric_key(key)] = val
        elif key.startswith("per_agent__"):
            out[_humanize_per_agent_machine_key(key)] = val
        else:
            out[key.replace("_", " ").title()] = val
    return out


def _strip_trend_traces_from_legend(fig: Any) -> None:
    """Force trend-line traces off the legend (Plotly sometimes keeps them when traces were grouped)."""
    for tr in fig.data:
        meta = getattr(tr, "meta", None)
        if not isinstance(meta, dict):
            continue
        if meta.get("aixplain_role") != "trend":
            continue
        tr.update(showlegend=False)


def _experiment_run_trend_row(run: ExperimentRun, run_index: int, *, human_column_names: bool) -> Dict[str, Any]:
    """One flat dict for :meth:`Experiment.runs_comparison_dataframe`."""
    summary = run.results.run_summary(include_executive_summary=False)
    flat = _flatten_run_summary_for_experiment_trends(summary, run.results)
    merged = {
        "run_index": int(run_index),
        "run_id": run.id,
        "run_created_at": run.created_at,
        **flat,
    }
    if human_column_names:
        return _humanize_experiment_comparison_row(merged)
    return merged


@dataclass
class Experiment:
    """Definition of an evaluation (dataset, agent snapshots, metric snapshots) plus appended runs.

    Use :meth:`runs_comparison_dataframe` to tabulate each :class:`ExperimentRun`, and
    :meth:`plot_runs_regression` for a line chart (with optional polynomial trend) across runs.
    """

    id: str
    created_at: datetime
    metadata: Dict[str, Any]
    dataset: List[EvalCase]
    agents_snapshot: List[Dict[str, Any]]
    metrics_snapshot: List[Dict[str, Any]]
    runs: List[ExperimentRun] = field(default_factory=list)
    _agents: Optional[Sequence[Agent]] = field(default=None, repr=False, compare=False)
    _metrics: Optional[Sequence[MetricTool]] = field(default=None, repr=False, compare=False)
    _executor: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate required fields after construction."""
        if not self.id:
            raise ValidationError("Experiment.id must be non-empty.")
        if not isinstance(self.metadata, dict):
            raise ValidationError("Experiment.metadata must be a dict.")

    def bind_executor(self, executor: Any) -> None:
        """Attach an :class:`~aixplain.v2.agent_evaluator.AgentEvaluationExecutor` (e.g. after loading from cache)."""
        self._executor = executor

    def run(
        self,
        *,
        agents: Optional[Union[Agent, Sequence[Agent]]] = None,
        metrics: Optional[Sequence[MetricTool]] = None,
        run_metadata: Optional[Dict[str, Any]] = None,
        **agent_run_kwargs: Any,
    ) -> ExperimentRun:
        """Execute the experiment and append a new :class:`ExperimentRun` (does not replace prior runs)."""
        executor = self._executor
        if executor is None:
            raise ValidationError(
                "No executor is bound to this experiment. Pass executor= when loading from cache, or call bind_executor().",
            )
        agents_effective: Optional[Sequence[Agent]] = None
        if agents is not None:
            agents_effective = _normalize_agents(agents)
        elif self._agents is not None:
            agents_effective = list(self._agents)
        if not agents_effective:
            raise ValidationError(
                "No agents available to run. Pass agents=... for experiments loaded from cache, "
                "or create the experiment via AgentEvaluationExecutor.create_experiment.",
            )
        metrics_effective: Optional[Sequence[MetricTool]]
        if metrics is not None:
            metrics_effective = list(metrics)
        else:
            metrics_effective = list(self._metrics) if self._metrics is not None else None

        eval_run = executor.evaluate(agents_effective, self.dataset, metrics_effective, **agent_run_kwargs)
        run = ExperimentRun(
            id=str(uuid.uuid4()),
            created_at=_utcnow(),
            metadata=dict(run_metadata or {}),
            parent=self,
            results=eval_run,
        )
        self.runs.append(run)
        persist = getattr(executor, "cache_experiments", True)
        if persist:
            store = getattr(executor, "_experiment_cache_store", lambda: None)()
            if store is not None:
                store.save(self)
        return run

    def runs_comparison_dataframe(self, *, human_column_names: bool = True) -> pd.DataFrame:
        """Tabular view of each :class:`ExperimentRun` for trend / regression plots.

        Rows are ordered by ``run.created_at``. By default columns use readable titles
        (for example ``"Run index"``, ``"Total credits (sum)"``, ``"Pass rate (m1)"``,
        ``"Average metric: m1 / score"``, ``"agent_a: Credits used (sum)"``). Set
        ``human_column_names=False`` for the legacy machine-oriented names
        (``run_index``, ``total_cost``, ``metric_pass_rate__m1``, …).

        Args:
            human_column_names: When True (default), column names are chosen for notebooks
                and charts; when False, internal stable keys are preserved.

        Returns:
            Empty DataFrame when :attr:`runs` is empty.
        """
        if not self.runs:
            return pd.DataFrame()
        ordered = sorted(self.runs, key=lambda r: r.created_at)
        records = [_experiment_run_trend_row(r, i, human_column_names=human_column_names) for i, r in enumerate(ordered)]
        return pd.DataFrame(records)

    def plot_runs_regression(
        self,
        *,
        y: Union[str, Sequence[str]],
        x: Optional[str] = None,
        human_column_names: bool = True,
        show_trendline: bool = True,
        trendline_degree: int = 1,
        show_trendline_in_legend: bool = False,
        title: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> Any:
        """Line chart of one or more series across experiment runs, with optional polynomial fit.

        Fits the trend against run order (0, 1, …) while the chart **x-axis** uses the
        column given by ``x``. When ``human_column_names`` is True (default), ``x`` defaults
        to :data:`EXPERIMENT_COMPARISON_COL_RUN_INDEX` (``\"Run index\"``); otherwise it
        defaults to ``\"run_index\"``.

        Args:
            y: Column name(s) from :meth:`runs_comparison_dataframe` — for example
                ``\"Total credits (sum)\"``, ``\"Avg credits per evaluation row\"``,
                ``\"Pass rate (my_metric)\"``, or ``\"Average metric: m1 / score\"`` when
                ``human_column_names`` is True.
            x: Column to use as x-axis; if omitted, uses ``Run index`` or ``run_index``
                depending on ``human_column_names``.
            human_column_names: Passed to :meth:`runs_comparison_dataframe` (default True).
            show_trendline: When True (default), overlay a least-squares polynomial per ``y``.
            trendline_degree: Polynomial degree (at least ``1``); capped by run count.
            show_trendline_in_legend: When False (default), dashed trend lines are omitted from
                the legend so only the data series names appear (e.g. ``Total credits (sum)``).
            title: Plot title; default describes the experiment and ``y``.
            figsize: Optional ``(width, height)`` in inches for layout sizing.

        Returns:
            A :class:`plotly.graph_objects.Figure`.

        Raises:
            ValidationError: If there are no runs or requested columns are missing.

        Note:
            Requires plotly (``pip install plotly``).
        """
        try:
            import plotly.graph_objects as go  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "Experiment.plot_runs_regression requires plotly. Install with: pip install plotly",
            ) from exc

        df = self.runs_comparison_dataframe(human_column_names=human_column_names)
        if df.empty:
            raise ValidationError("Experiment has no runs to plot; call run() at least once.")
        x_eff = (
            x
            if x is not None
            else (
                EXPERIMENT_COMPARISON_COL_RUN_INDEX if human_column_names else "run_index"
            )
        )
        if x_eff not in df.columns:
            raise ValidationError(
                f"Unknown x column {x_eff!r}. Available: {sorted(df.columns)!r}.",
            )
        y_cols: List[str] = [y] if isinstance(y, str) else [str(c) for c in y]
        for col in y_cols:
            if col not in df.columns:
                raise ValidationError(
                    f"Unknown y column {col!r}. Call runs_comparison_dataframe() and inspect df.columns.",
                )

        w, h = figsize if figsize is not None else (8.0, 4.0)
        layout_size = {"width": int(w * 96), "height": int(h * 96)}

        xi = np.arange(len(df), dtype=float)
        deg = max(1, int(trendline_degree))
        deg = min(deg, max(1, len(df) - 1))

        fig = go.Figure()
        x_plot = df[x_eff]
        for col in y_cols:
            y_num = pd.to_numeric(df[col], errors="coerce")
            data_kw: Dict[str, Any] = {
                "x": x_plot,
                "y": y_num,
                "mode": "lines+markers",
                "name": str(col),
                "connectgaps": False,
                "meta": {"aixplain_role": "data", "series": str(col)},
            }
            if show_trendline and show_trendline_in_legend:
                data_kw["legendgroup"] = str(col)
            fig.add_trace(go.Scatter(**data_kw))
            if show_trendline and len(df) >= 2:
                yv = y_num.to_numpy(dtype=float)
                valid = ~np.isnan(yv)
                n_valid = int(valid.sum())
                if n_valid >= 2:
                    d_fit = min(deg, n_valid - 1)
                    coeff = np.polyfit(xi[valid], yv[valid], d_fit)
                    y_hat = np.polyval(coeff, xi)
                    trend_kw: Dict[str, Any] = {
                        "x": x_plot,
                        "y": y_hat,
                        "mode": "lines",
                        "line": {"dash": "dash", "width": 2},
                        "meta": {"aixplain_role": "trend", "series": str(col)},
                    }
                    if show_trendline_in_legend:
                        trend_kw["name"] = f"{col} (trend)"
                        trend_kw["legendgroup"] = str(col)
                        trend_kw["showlegend"] = True
                    else:
                        trend_kw["showlegend"] = False
                        trend_kw["hovertemplate"] = (
                            f"<b>{col}</b><br>Least-squares fit<br>%{{x}}<br>%{{y}}<extra></extra>"
                        )
                    fig.add_trace(go.Scatter(**trend_kw))

        if show_trendline and not show_trendline_in_legend:
            _strip_trend_traces_from_legend(fig)

        plot_title = title if title is not None else f"Experiment {self.id[:8]}… — " + ", ".join(y_cols)
        fig.update_layout(
            title=plot_title,
            xaxis_title=str(x_eff),
            yaxis_title="value",
            legend_title_text="series",
            **layout_size,
        )
        return fig

    def to_cache_payload(self) -> Dict[str, Any]:
        """Serialize experiment and all runs for the local cache."""
        return {
            "format_version": _CACHE_FORMAT_VERSION,
            "experiment": {
                "id": self.id,
                "created_at": _iso(self.created_at),
                "metadata": dict(self.metadata),
                "dataset": [_eval_case_to_dict(c) for c in self.dataset],
                "agents_snapshot": list(self.agents_snapshot),
                "metrics_snapshot": list(self.metrics_snapshot),
                "runs": [
                    {
                        "id": r.id,
                        "created_at": _iso(r.created_at),
                        "metadata": dict(r.metadata),
                        "results_records": _serialize_evaluation_records(r.results),
                    }
                    for r in self.runs
                ],
            },
        }

    @classmethod
    def from_cache_payload(cls, data: Dict[str, Any], *, executor: Any = None) -> Experiment:
        """Restore an experiment from :meth:`to_cache_payload` JSON structure."""
        version = data.get("format_version")
        if version != _CACHE_FORMAT_VERSION:
            raise ValidationError(f"Unsupported experiment cache format_version: {version!r}")
        raw = data["experiment"]
        exp = cls(
            id=str(raw["id"]),
            created_at=_parse_dt(str(raw["created_at"])),
            metadata=dict(raw.get("metadata") or {}),
            dataset=[_eval_case_from_dict(x) for x in raw["dataset"]],
            agents_snapshot=list(raw.get("agents_snapshot") or []),
            metrics_snapshot=list(raw.get("metrics_snapshot") or []),
            runs=[],
            _agents=None,
            _metrics=None,
            _executor=executor,
        )
        for run_raw in raw.get("runs") or []:
            results = _deserialize_evaluation_records(list(run_raw.get("results_records") or []))
            run = ExperimentRun(
                id=str(run_raw["id"]),
                created_at=_parse_dt(str(run_raw["created_at"])),
                metadata=dict(run_raw.get("metadata") or {}),
                parent=exp,
                results=results,
            )
            exp.runs.append(run)
        return exp


@dataclass
class ExperimentRun:
    """One execution of an :class:`Experiment` with concrete :class:`AgentEvaluationRun` results."""

    id: str
    created_at: datetime
    metadata: Dict[str, Any]
    parent: Experiment
    results: AgentEvaluationRun

    def __post_init__(self) -> None:
        """Validate required fields after construction."""
        if not self.id:
            raise ValidationError("ExperimentRun.id must be non-empty.")
        if not isinstance(self.metadata, dict):
            raise ValidationError("ExperimentRun.metadata must be a dict.")


class ExperimentLocalCache:
    """Filesystem-backed store for :class:`Experiment` (including all :class:`ExperimentRun` records)."""

    def __init__(self, base_dir: Union[str, Path]) -> None:
        """Create a cache rooted at ``base_dir`` (created if missing)."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, experiment_id: str) -> Path:
        """Return the JSON path for a given experiment id."""
        safe = str(experiment_id).replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe}.json"

    def save(self, experiment: Experiment) -> Path:
        """Write ``experiment`` to disk atomically."""
        path = self.path_for(experiment.id)
        payload = experiment.to_cache_payload()
        tmp = path.with_suffix(path.suffix + ".tmp")
        text = json.dumps(payload, indent=2, default=str)
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
        return path

    def list_experiments(self) -> List[Dict[str, Any]]:
        """Summarize cached experiments (id, creation time, metadata, run count)."""
        summaries: List[Dict[str, Any]] = []
        for path in sorted(self.base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                exp = data.get("experiment") or {}
                summaries.append(
                    {
                        "id": exp.get("id"),
                        "created_at": exp.get("created_at"),
                        "metadata": dict(exp.get("metadata") or {}),
                        "run_count": len(exp.get("runs") or []),
                        "path": str(path),
                    },
                )
            except (json.JSONDecodeError, OSError, KeyError, TypeError):
                continue
        return summaries

    def load_experiment(self, experiment_id: str, *, executor: Any = None) -> Experiment:
        """Load a full experiment and runs from the cache."""
        path = self.path_for(experiment_id)
        if not path.is_file():
            raise ValidationError(f"No cached experiment found for id {experiment_id!r} at {path}.")
        data = json.loads(path.read_text(encoding="utf-8"))
        exp = Experiment.from_cache_payload(data, executor=executor)
        if exp.id != experiment_id:
            raise ValidationError("Cached file experiment id does not match requested id.")
        return exp
