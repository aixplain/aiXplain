"""Local Streamlit dashboard for agent evaluation CSV exports.

Run from anywhere. The app **always** puts this repository’s root first on ``sys.path``,
so Python loads the **checkout** ``aixplain/`` package (no ``pip install -e .`` required
for the SDK itself). You still need this venv to satisfy the SDK’s third-party
dependencies (``pandas``, ``requests``, etc.—see the repo ``pyproject.toml``)::

    streamlit run eval_dashboard/app.py

Load a file produced by :meth:`~aixplain.v2.agent_evaluator.AgentEvaluationRun.to_dataframe`
(``to_csv``). Optional LLM features (executive summary, chat) need ``AIXPLAIN_API_KEY`` and
``AgentEvaluationRun.configure_insights(aix)`` after constructing :class:`~aixplain.Aixplain`.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _use_local_aixplain_repo() -> None:
    """Prefer the checkout on ``sys.path`` over any other ``aixplain`` (e.g. PyPI)."""
    rp = str(_REPO_ROOT)
    try:
        sys.path.remove(rp)
    except ValueError:
        pass
    sys.path.insert(0, rp)


_use_local_aixplain_repo()

import pandas as pd
import streamlit as st

from aixplain import Aixplain
from aixplain.v2.agent_evaluator import AgentEvaluationExecutor, AgentEvaluationRun
from aixplain.v2.eval_results_display import summarize_by_agent
from aixplain.v2.exceptions import ValidationError


def _repo_root() -> Path:
    return _REPO_ROOT


def _failure_rate_by_agent(work: pd.DataFrame) -> Optional[pd.DataFrame]:
    """One column ``failure_rate`` in ``[0, 1]``, indexed by ``agent_name``."""
    if "agent_run_failed" not in work.columns or "agent_name" not in work.columns:
        return None
    fr = work["agent_run_failed"]
    if fr.dtype == object:
        failed = fr.map(lambda x: str(x).lower() in ("true", "1", "yes"))
    else:
        failed = fr.astype(bool)
    rates = work.assign(_agent_failed=failed).groupby("agent_name", dropna=False)["_agent_failed"].mean()
    return rates.to_frame("failure_rate")


def _load_run(source: Any) -> AgentEvaluationRun:
    """Load CSV from path, ``Path``, or file-like object."""
    return AgentEvaluationExecutor.load_from_csv(source, normalize=True)


def _init_insights_if_possible() -> bool:
    """Bind default insight model when ``AIXPLAIN_API_KEY`` is set. Returns success."""
    api_key = os.environ.get("AIXPLAIN_API_KEY", "").strip()
    if not api_key:
        return False
    kwargs: dict[str, Any] = {"api_key": api_key}
    if os.environ.get("BACKEND_URL"):
        kwargs["backend_url"] = os.environ["BACKEND_URL"].strip()
    if os.environ.get("MODEL_URL"):
        kwargs["model_url"] = os.environ["MODEL_URL"].strip()
    try:
        aix = Aixplain(**kwargs)
        AgentEvaluationRun.configure_insights(aix)
        AgentEvaluationRun.ensure_insight_model_loaded()
        return True
    except Exception:
        return False


def _summary_for_display(summary: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Split executive summary from the rest for nicer layout."""
    core = {k: v for k, v in summary.items() if k != "executive_summary"}
    exec_text = str(summary.get("executive_summary", ""))
    return core, exec_text


def _csv_signature(uploaded: Any, path_str: str) -> Optional[tuple[Any, ...]]:
    """Stable tuple so we can reset chat when the loaded file changes."""
    if uploaded is not None:
        raw = uploaded.getvalue()
        return ("upload", str(getattr(uploaded, "name", "")), len(raw))
    p = Path(path_str).expanduser()
    if p.is_file():
        st_ = p.stat()
        return ("path", str(p.resolve()), st_.st_mtime_ns, st_.st_size)
    return None


def main() -> None:
    st.set_page_config(page_title="Agent eval dashboard", layout="wide")
    st.title("Agent evaluation dashboard")
    st.caption("Load results CSV · run summary · charts · optional LLM chat")

    try:
        if "AIXPLAIN_API_KEY" in st.secrets:
            os.environ.setdefault("AIXPLAIN_API_KEY", str(st.secrets["AIXPLAIN_API_KEY"]))
    except Exception:
        pass

    default_csv = _repo_root() / "results.csv"
    with st.sidebar:
        st.subheader("Data source")
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        default_path = st.text_input(
            "Or path to CSV",
            value=str(default_csv) if default_csv.is_file() else "",
            help="Long-format export from AgentEvaluationRun.to_dataframe().to_csv()",
        )
        st.subheader("LLM (optional)")
        st.markdown(
            "Set `AIXPLAIN_API_KEY` (and optionally `BACKEND_URL`, `MODEL_URL`) in the "
            "environment before starting Streamlit for executive summary + chat."
        )
        include_llm_summary = st.checkbox("Include LLM executive summary", value=True)

    run: Optional[AgentEvaluationRun] = None
    err: Optional[str] = None
    try:
        if uploaded is not None:
            run = _load_run(io.BytesIO(uploaded.getvalue()))
        elif default_path.strip():
            p = Path(default_path).expanduser()
            if not p.is_file():
                err = f"File not found: {p}"
            else:
                run = _load_run(p)
        else:
            err = "Upload a CSV or enter a path."
    except ValidationError as e:
        err = str(e)
    except Exception as e:
        err = f"Failed to load CSV: {e}"

    if err:
        st.error(err)
        st.stop()

    assert run is not None
    sig = _csv_signature(uploaded, default_path.strip())
    if sig is not None and st.session_state.get("_eval_csv_sig") != sig:
        st.session_state._eval_csv_sig = sig
        st.session_state.pop("eval_chatbot", None)
        st.session_state.pop("eval_chat_messages", None)

    df = run.to_dataframe()

    tab_summary, tab_plots, tab_data, tab_chat = st.tabs(
        ["Run summary", "Plots", "Data preview", "Chat"]
    )

    with tab_summary:
        if include_llm_summary:
            _init_insights_if_possible()
        try:
            summary = run.run_summary(
                include_executive_summary=include_llm_summary,
            )
        except Exception as e:
            st.warning(f"run_summary raised ({e}); retrying without LLM executive summary.")
            summary = run.run_summary(include_executive_summary=False)

        core, exec_text = _summary_for_display(summary)
        st.subheader("Aggregates")
        st.json(core)
        st.subheader("Executive summary")
        st.markdown(exec_text or "_(empty)_")

        try:
            by_agent = summarize_by_agent(df)
            st.subheader("Per-agent summary (numeric means and metric pass rates)")
            st.dataframe(by_agent, use_container_width=True)
        except Exception as e:
            st.info(f"Per-agent table skipped: {e}")

    with tab_plots:
        st.subheader("Cost, time, failures, and tool usage by agent")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.markdown("**Total cost** (`used_credits` sum)")
            if "used_credits" in df.columns:
                cost_df = df.groupby("agent_name", dropna=False)["used_credits"].sum(numeric_only=True)
                st.bar_chart(cost_df.to_frame("used_credits"))
            else:
                st.caption("Column `used_credits` not present.")
        with r1c2:
            st.markdown("**Total run time** (`run_time` sum, seconds)")
            if "run_time" in df.columns:
                time_df = df.groupby("agent_name", dropna=False)["run_time"].sum(numeric_only=True)
                st.bar_chart(time_df.to_frame("run_time"))
            else:
                st.caption("Column `run_time` not present.")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.markdown("**Agent run failure rate** (share of rows with `agent_run_failed`)")
            fr_df = _failure_rate_by_agent(df)
            if fr_df is not None and not fr_df.empty:
                st.bar_chart(fr_df)
            else:
                st.caption("Column `agent_run_failed` not present or no data.")
        with r2c2:
            st.markdown("**Total tool calls** (`total_tool_calls` sum)")
            if "total_tool_calls" in df.columns:
                tc_df = df.groupby("agent_name", dropna=False)["total_tool_calls"].sum(numeric_only=True)
                st.bar_chart(tc_df.to_frame("total_tool_calls"))
            else:
                st.caption("Column `total_tool_calls` not present.")

        prefixes = run.metric_tool_prefixes()
        if prefixes:
            st.subheader("Metric by agent (Plotly)")
            st.caption(
                "Numeric inner keys: mean per agent. Categorical keys: stacked distribution (shares when normalized)."
            )
            inner_default = "score"
            c1, c2, c3 = st.columns(3)
            with c1:
                tool_prefix = st.selectbox("Metric prefix", options=prefixes, key="plot_prefix")
            with c2:
                inner_key = st.text_input("Metric field (inner key)", value=inner_default, key="plot_inner")
            with c3:
                normalize_enum = st.checkbox(
                    "Normalize enum shares",
                    value=True,
                    help="For categorical metrics only: show proportions per agent.",
                    key="plot_normalize_enum",
                )
            try:
                metric_fig = run.plot_metric_by_agent(
                    inner_key.strip() or inner_default,
                    tool_prefix=tool_prefix,
                    normalize_enum=normalize_enum,
                )
                st.plotly_chart(metric_fig, use_container_width=True)
            except ImportError:
                st.warning("Install plotly for metric bar charts: `pip install plotly`")
            except Exception as e:
                st.warning(str(e))
        else:
            st.info("No metric columns detected for metric bar chart.")

    with tab_data:
        st.caption(f"{len(df)} rows · showing up to 500 in the grid")
        st.dataframe(df.head(500), use_container_width=True, height=400)
        st.download_button(
            "Download loaded CSV (round-trip)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="eval_results_loaded.csv",
            mime="text/csv",
        )

    with tab_chat:
        if not os.environ.get("AIXPLAIN_API_KEY", "").strip():
            st.warning("Set `AIXPLAIN_API_KEY` (or streamlit secrets) to use the chatbot.")
        else:
            st.session_state.setdefault("eval_chat_messages", [])
            if _init_insights_if_possible():
                if "eval_chatbot" not in st.session_state:
                    try:
                        st.session_state.eval_chatbot = run.chatbot()
                    except Exception as e:
                        st.session_state.eval_chatbot = None
                        st.error(f"Could not start chatbot: {e}")
                bot = st.session_state.eval_chatbot
                if bot is not None:
                    if st.button("Reset conversation"):
                        bot.reset_conversation()
                        st.session_state.eval_chat_messages = []
                        st.rerun()
                    for msg in st.session_state.eval_chat_messages:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                    if prompt := st.chat_input("Ask about this evaluation run"):
                        st.session_state.eval_chat_messages.append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking…"):
                                try:
                                    answer = bot.ask(prompt)
                                except Exception as e:
                                    answer = f"Error: {e}"
                            st.markdown(answer)
                        st.session_state.eval_chat_messages.append({"role": "assistant", "content": answer})
            else:
                st.error("Could not configure insights; check API key and URLs.")


if __name__ == "__main__":
    main()
