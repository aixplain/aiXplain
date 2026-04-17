"""Display helpers for :class:`~aixplain.v2.agent_evaluator.AgentEvaluationExecutor` results.

Load CSV exports of evaluation DataFrames, pivot long rows into side-by-side wide
tables, summarize metrics by agent, and build simple HTML for notebook widgets.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

import pandas as pd

from .exceptions import ValidationError

_SKIP_METRIC_SUFFIXES = (
    "__metric_status",
    "__metric_completed",
    "__metric_error",
    "__metric_error_type",
    "__metric_skipped",
    "__metric_skip_reason",
)


def _is_metric_data_column(name: str) -> bool:
    """True for ``<metric>__<payload_key>`` columns, excluding metric machinery fields."""
    n = str(name)
    if "__" not in n:
        return False
    if n.startswith("case_meta__"):
        return False
    return not any(n.endswith(suffix) for suffix in _SKIP_METRIC_SUFFIXES)


def guess_compare_value_columns(df: pd.DataFrame) -> List[str]:
    """Columns to compare by default: ``output`` plus flattened metric payload columns."""
    out: List[str] = []
    if "output" in df.columns:
        out.append("output")
    for col in df.columns:
        if col == "output":
            continue
        if _is_metric_data_column(col):
            out.append(col)
    return out


def load_eval_csv(path: Union[str, Path], **read_csv_kwargs: Any) -> pd.DataFrame:
    """Load a CSV written from evaluator results (e.g. ``df.to_csv(...)``).

    Args:
        path: Path to the CSV file.
        **read_csv_kwargs: Forwarded to :func:`pandas.read_csv`.

    Returns:
        DataFrame in the same long shape as :meth:`AgentEvaluationExecutor.evaluate`.
    """
    return pd.read_csv(Path(path), **read_csv_kwargs)


def pivot_agents_wide(
    df: pd.DataFrame,
    value_columns: Optional[Sequence[str]] = None,
    *,
    include_query: bool = True,
    include_reference: bool = True,
) -> pd.DataFrame:
    """Pivot long evaluator output so each case is one row and agents appear as columns.

    Column index is a MultiIndex. Pivoted fields use ``(value_field, agent_name)``.
    ``query`` and ``reference`` use ``(field_name, "")`` so they share two levels
    and concatenate cleanly with pivoted columns.

    Args:
        df: Long-format evaluation results.
        value_columns: Columns to pivot; defaults to :func:`guess_compare_value_columns`.
        include_query: If True and ``query`` is present, join one query per ``case_index``.
        include_reference: Same for ``reference``.

    Returns:
        Wide DataFrame indexed by ``case_index``.

    Raises:
        ValidationError: If required columns are missing or pivot inputs are invalid.
    """
    for required in ("case_index", "agent_name"):
        if required not in df.columns:
            raise ValidationError(f"DataFrame must include column {required!r}")
    cols = list(value_columns) if value_columns is not None else guess_compare_value_columns(df)
    if not cols:
        raise ValidationError("No value columns to pivot; pass value_columns explicitly.")
    parts: List[pd.DataFrame] = []
    for col in cols:
        if col not in df.columns:
            raise ValidationError(f"Missing value column {col!r}")
        pt = df.pivot_table(
            index="case_index",
            columns="agent_name",
            values=col,
            aggfunc="first",
        )
        pt.columns = pd.MultiIndex.from_product([[col], pt.columns.astype(str)])
        parts.append(pt)
    wide = pd.concat(parts, axis=1)
    by_case = df.drop_duplicates(subset=["case_index"]).set_index("case_index")
    meta_parts: List[pd.DataFrame] = []
    if include_query and "query" in df.columns:
        q = by_case["query"].reindex(wide.index).to_frame()
        q.columns = pd.MultiIndex.from_tuples([(c, "") for c in q.columns])
        meta_parts.append(q)
    if include_reference and "reference" in df.columns:
        r = by_case["reference"].reindex(wide.index).to_frame()
        r.columns = pd.MultiIndex.from_tuples([(c, "") for c in r.columns])
        meta_parts.append(r)
    if meta_parts:
        wide = pd.concat([wide] + meta_parts, axis=1)
    return wide


def summarize_by_agent(df: pd.DataFrame) -> pd.DataFrame:
    """Per-agent row counts, failure counts, and means of numeric metric columns.

    Non-numeric metric columns (e.g. string scores) are omitted from means.
    ``agent_run_failed`` is coerced from strings when loaded from CSV.

    Args:
        df: Long-format evaluation results.

    Returns:
        One row per ``agent_name``.

    Raises:
        ValidationError: If ``agent_name`` is missing.
    """
    if "agent_name" not in df.columns:
        raise ValidationError("DataFrame must include column 'agent_name'")
    work = df.copy()
    if "agent_run_failed" in work.columns:
        fr = work["agent_run_failed"]
        if fr.dtype == object:
            work["_agent_run_failed_bool"] = fr.map(lambda x: str(x).lower() in ("true", "1", "yes"))
        else:
            work["_agent_run_failed_bool"] = fr.astype(bool)
    rows: List[dict[str, Any]] = []
    for name, sub in work.groupby("agent_name", dropna=False):
        row: dict[str, Any] = {"agent_name": name, "n_rows": len(sub)}
        if "_agent_run_failed_bool" in sub.columns:
            row["n_agent_failed"] = int(sub["_agent_run_failed_bool"].sum())
        for col in sub.columns:
            if col in ("agent_name", "_agent_run_failed_bool", "case_index"):
                continue
            if col.startswith("case_meta__"):
                continue
            if not (_is_metric_data_column(col) or col in ("run_time", "used_credits")):
                continue
            if not pd.api.types.is_numeric_dtype(sub[col]):
                continue
            row[f"mean__{col}"] = sub[col].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def case_rows(df: pd.DataFrame, case_index: int) -> pd.DataFrame:
    """Return long-format rows for a single ``case_index``."""
    return df.loc[df["case_index"] == case_index].copy()


def case_comparison_html(
    df: pd.DataFrame,
    case_index: int,
    *,
    max_output_chars: Optional[int] = 8000,
) -> str:
    """Build a simple HTML table comparing agents for one case (for notebooks)."""
    sub = case_rows(df, case_index)
    if sub.empty:
        return "<p>No rows for this case_index.</p>"
    query_txt = ""
    if "query" in sub.columns:
        query_txt = html.escape(str(sub["query"].iloc[0]))
    lines = [
        f"<h4>case_index={case_index}</h4>",
        "<p><b>Query</b></p>",
        f"<pre style='white-space:pre-wrap'>{query_txt}</pre>",
        "<table border='1' style='border-collapse:collapse;width:100%'>",
        "<tr><th>agent_name</th><th>output</th></tr>",
    ]
    for _, row in sub.iterrows():
        agent = html.escape(str(row.get("agent_name", "")))
        out = str(row.get("output", ""))
        if max_output_chars is not None and len(out) > max_output_chars:
            out = out[:max_output_chars] + "..."
        lines.append(
            "<tr><td style='vertical-align:top'>{}</td><td><pre style='white-space:pre-wrap'>{}</pre></td></tr>".format(
                agent,
                html.escape(out),
            )
        )
    lines.append("</table>")
    return "\n".join(lines)
