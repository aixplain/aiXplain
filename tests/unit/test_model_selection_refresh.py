"""Offline tests for ``skills/model-selection/tooling/refresh.py`` (no network)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "model-selection" / "tooling" / "refresh.py"
_spec = importlib.util.spec_from_file_location("model_selection_refresh", _SCRIPT)
assert _spec is not None and _spec.loader is not None
refresh = importlib.util.module_from_spec(_spec)
sys.modules["model_selection_refresh"] = refresh
_spec.loader.exec_module(refresh)


def _model(model_id: str, input_price: float = 1e-6, output_price: float = 2e-6, zdr: bool = False) -> dict:
    return {
        "id": model_id,
        "path": f"vendor/{model_id}/host",
        "name": model_id.upper(),
        "pricing": {"input_price": input_price, "output_price": output_price},
        "zdr": zdr,
    }


def _tiers(*model_ids: str) -> dict:
    return {
        "models": {
            i: {"path": f"vendor/{i}/host", "tier": "balanced", "good_for": [], "reviewed": None} for i in model_ids
        },
        "excluded": {},
    }


class FakeMcp:
    """Serves `search` pages from a fixed list, optionally reporting a larger total than it returns."""

    def __init__(self, models: list[dict], page_size: int, total: int | None = None):
        self.pages = [models[i : i + page_size] for i in range(0, len(models), page_size)] or [[]]
        self.total = len(models) if total is None else total
        self.calls: list[tuple[str, dict]] = []

    def call(self, tool: str, arguments: dict) -> dict:
        self.calls.append((tool, arguments))
        page = arguments["page_number"]
        results = self.pages[page] if page < len(self.pages) else []
        return {
            "model": {
                "results": results,
                "stats": {"total": self.total, "pages_count": len(self.pages), "current_page": page},
            }
        }


def test_snapshot_keeps_diff_fields_sorted_by_path() -> None:
    snap = refresh.snapshot([_model("b"), _model("a", zdr=True)])
    assert list(snap) == ["a", "b"]
    assert snap["a"] == {
        "path": "vendor/a/host",
        "name": "A",
        "input_price": 1e-6,
        "output_price": 2e-6,
        "zdr": True,
    }


def test_first_run_reports_no_comparison() -> None:
    new = refresh.snapshot([_model("a"), _model("b")])
    report = refresh.build_report({}, new, _tiers("a"))
    assert "First snapshot" in report
    assert "New on the marketplace" not in report
    assert "Price or ZDR changed" not in report


def test_price_change_is_reported() -> None:
    old = refresh.snapshot([_model("a")])
    new = refresh.snapshot([_model("a", input_price=3e-6)])
    report = refresh.build_report(old, new, _tiers("a"))
    assert "Price or ZDR changed (1)" in report
    assert "input_price 1e-06 → 3e-06" in report


def test_removed_tiered_model_is_reported() -> None:
    old = refresh.snapshot([_model("a"), _model("b")])
    new = refresh.snapshot([_model("a")])
    report = refresh.build_report(old, new, _tiers("a", "b"))
    assert "gone from the marketplace: remove (1)" in report
    assert "`vendor/b/host` (`b`)" in report


def test_suspect_price_is_reported() -> None:
    new = refresh.snapshot([_model("a", input_price=0.2, output_price=10)])
    report = refresh.build_report({}, new, _tiers())
    assert "wrong unit (above 0.001 per token) (1)" in report


def test_fetch_pages_search_with_flat_filters_from_page_zero() -> None:
    models = [_model(f"m{i}") for i in range(5)]
    mcp = FakeMcp(models, page_size=2)
    fetched = refresh.fetch_llms(mcp)
    assert [m["id"] for m in fetched] == [m["id"] for m in models]
    assert [args["page_number"] for _, args in mcp.calls] == [0, 1, 2]
    tool, args = mcp.calls[0]
    assert tool == "search"
    assert args["asset_type"] == "model"
    assert args["categories"] == "LLM"


def test_truncated_fetch_fails_instead_of_reporting_removals() -> None:
    mcp = FakeMcp([_model("a"), _model("b")], page_size=2, total=21)
    with pytest.raises(refresh.IncompleteFetch, match="Fetched 2 unique LLMs but the marketplace reports 21"):
        refresh.fetch_llms(mcp)


def test_main_exits_non_zero_on_truncated_fetch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    monkeypatch.setenv("AIXPLAIN_API_KEY", "test-key")
    monkeypatch.setattr(refresh, "CATALOG", catalog)
    monkeypatch.setattr(refresh, "Mcp", lambda url, key: FakeMcp([_model("a")], page_size=2, total=3))
    monkeypatch.setattr(sys, "argv", ["refresh.py"])
    with pytest.raises(SystemExit) as exit_info:
        refresh.main()
    assert exit_info.value.code != 0
    assert "partial catalog" in str(exit_info.value.code)
    assert not catalog.exists()
