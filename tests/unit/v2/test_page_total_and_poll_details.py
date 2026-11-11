"""BUG-1459: ``Page.page_total`` counts pages, and a polled model run keeps ``details``.

All mocked -- no network. ``page_total`` used to be read from the backend's
``pageTotal``, which is the number of items on the page; a loop bounded by it
skipped or over-fetched pages. ``poll()`` copied a fixed key list without
``details``, so ``ModelResult.details`` (a declared field, so the raw-data
fallback never fires) was ``None`` on async models.
"""

from unittest.mock import Mock

import pytest

from aixplain import Model
from aixplain.v2.model import Detail


def _bind(monkeypatch, cls, response):
    context = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="test_key")
    context.client.request.return_value = response
    monkeypatch.setattr(cls, "context", context, raising=False)
    return context


def _items(n):
    return [{"id": f"m{i}", "name": f"Model {i}"} for i in range(n)]


# =============================================================================
# page_total
# =============================================================================


def test_page_total_reads_pages_count(monkeypatch):
    """The ticket's acceptance case: 500 records, 20 per page -> 25 pages, not 20."""
    _bind(monkeypatch, Model, {"results": _items(20), "total": 500, "pageTotal": 20, "pagesCount": 25})

    page = Model.search(page_size=20)

    assert page.page_total == 25
    assert page.total == 500
    assert len(page.results) == 20


def test_page_total_falls_back_to_ceil_of_total_over_page_size(monkeypatch):
    """Without ``pagesCount``, 45 records at 20 per page span 3 pages (not 20)."""
    _bind(monkeypatch, Model, {"results": _items(20), "total": 45, "pageTotal": 20})

    page = Model.search(page_size=20)

    assert page.page_total == 3


def test_page_total_is_zero_for_an_empty_result(monkeypatch):
    _bind(monkeypatch, Model, {"results": [], "total": 0, "pageTotal": 0})

    assert Model.search().page_total == 0


@pytest.mark.parametrize("bad", [True, -1, "25", None], ids=["bool", "negative", "string", "null"])
def test_invalid_pages_count_is_ignored(monkeypatch, bad):
    _bind(monkeypatch, Model, {"results": _items(2), "total": 41, "pageTotal": 2, "pagesCount": bad})

    assert Model.search(page_size=20).page_total == 3


def test_page_total_without_page_size_falls_back_to_one_page(monkeypatch):
    """``_build_page`` called without a page size still reports a sane count."""
    _bind(monkeypatch, Model, {})
    page = Model._build_page({"results": _items(2), "total": 2}, Model.context, page_number=0)

    assert page.page_total == 1


def test_page_loop_visits_every_page(monkeypatch):
    """A ``page_number + 1 >= page_total`` loop (tests/functional/_helpers.py) now sees every page."""
    total, size = 45, 20
    context = _bind(monkeypatch, Model, None)

    def respond(method, path, json):
        start = json["pageNumber"] * size
        return {"results": _items(total)[start : start + size], "total": total, "pageTotal": size}

    context.client.request.side_effect = respond

    seen, page_number = [], 0
    while True:
        page = Model.search(page_number=page_number, page_size=size)
        seen.extend(r.id for r in page.results)
        if page_number + 1 >= page.page_total:
            break
        page_number += 1

    assert len(seen) == total
    assert context.client.request.call_count == 3


# =============================================================================
# poll() keeps details
# =============================================================================


BODY = {
    "status": "SUCCESS",
    "completed": True,
    "data": "answer",
    "details": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "answer",
                "reasoning_content": "think",
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "f", "arguments": "{}"}}],
            },
            "finish_reason": "tool_calls",
        }
    ],
}


def _model():
    model = Model(id="m1", name="Model")
    model.context = Mock()
    return model


def test_poll_details_match_the_sync_path():
    sync_result = _model().handle_run_response(dict(BODY))

    polled = _model()
    polled.context.client.get = Mock(return_value=dict(BODY))
    poll_result = polled.poll("https://models.aixplain.com/api/v1/data/req-1")

    assert poll_result.details is not None
    assert poll_result.details == sync_result.details
    detail = poll_result.details[0]
    assert isinstance(detail, Detail)
    assert detail.message.reasoning_content == "think"
    assert detail.message.tool_calls[0]["id"] == "call_1"
    assert detail.finish_reason == "tool_calls"


def test_poll_dict_details_pass_through():
    """Guardrail/utility models return ``details`` as a dict; it survives polling too."""
    model = _model()
    model.context.client.get = Mock(
        return_value={"status": "SUCCESS", "completed": True, "details": {"action": "NONE"}}
    )

    assert model.poll("https://models.aixplain.com/api/v1/data/req-1").details == {"action": "NONE"}


def test_poll_without_details_keeps_none():
    model = _model()
    model.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": "x"})

    assert model.poll("https://models.aixplain.com/api/v1/data/req-1").details is None
