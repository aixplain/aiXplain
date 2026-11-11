"""Linear, capped reassembly of JSON payloads split across SSE lines (BUG-949).

The streamer used to grow the payload with ``+=`` and re-run ``json.loads`` on
the whole buffer after every continuation line, with no cap -- quadratic in the
number of lines.
"""

import json
from unittest.mock import Mock, patch

import pytest

from aixplain.v2 import model as model_module
from aixplain.v2.model import ModelResponseStreamer


def _streamer(lines):
    response = Mock()
    response.iter_lines.return_value = iter(lines)
    return ModelResponseStreamer(response)


def _split_payload(obj, pieces):
    text = json.dumps(obj)
    step = max(1, len(text) // pieces)
    return [text[i : i + step] for i in range(0, len(text), step)]


def test_payload_split_across_three_lines_reassembles():
    parts = _split_payload({"choices": [{"delta": {"content": "hello world"}, "finish_reason": None}]}, 3)
    assert len(parts) >= 3
    streamer = _streamer([f"data: {p}" for p in parts] + ["data: [DONE]"])

    chunk = next(streamer)

    assert chunk.data == "hello world"
    with pytest.raises(StopIteration):
        next(streamer)


def test_done_after_partial_payload_is_preserved():
    streamer = _streamer(['data: {"choices": [{"delta": {"content": "x', "data: [DONE]"])

    chunk = next(streamer)

    # The unparseable fragment is emitted raw, then [DONE] still ends the stream cleanly.
    assert chunk.data.startswith('{"choices"')
    with pytest.raises(StopIteration):
        next(streamer)
    assert streamer.status.value.upper() in {"SUCCESS", "COMPLETED"}


def test_parse_attempts_are_linear_in_closing_lines():
    """A 1,000-line payload whose fragments never end in } or ] parses O(1) times."""
    content = "a" * 5000
    text = json.dumps({"choices": [{"delta": {"content": content}, "finish_reason": None}]})
    # Fragments that end on a plain letter so only the last one can close the object.
    body, tail = text[:-40], text[-40:]
    step = max(1, len(body) // 1000)
    parts = [body[i : i + step] for i in range(0, len(body), step)] + [tail]
    assert all(not p.rstrip().endswith(("}", "]")) for p in parts[:-1])
    lines = [f"data: {p}" for p in parts] + ["data: [DONE]"]

    real_loads = json.loads
    calls = {"n": 0}

    def counting_loads(s, *a, **kw):
        calls["n"] += 1
        return real_loads(s, *a, **kw)

    streamer = _streamer(lines)
    with patch.object(model_module.json, "loads", side_effect=counting_loads):
        chunk = next(streamer)

    assert chunk.data == content
    # first-line attempt + one attempt per closing fragment (+ a little slack for sniffing)
    assert calls["n"] <= 5, calls["n"]


def test_oversize_payload_is_capped_and_emitted_raw(monkeypatch):
    monkeypatch.setattr(model_module, "_SSE_MAX_BUFFER_CHARS", 100)
    lines = ['data: {"choices": [{"delta": {"content": "'] + ["data: " + "x" * 30] * 1000 + ["data: [DONE]"]

    streamer = _streamer(lines)
    chunk = next(streamer)

    assert isinstance(chunk.data, str)
    assert len(chunk.data) < 1000  # stopped near the cap instead of buffering everything


def test_continuation_line_cap(monkeypatch):
    monkeypatch.setattr(model_module, "_SSE_MAX_CONTINUATION_LINES", 5)
    lines = ['data: {"choices": [{"delta": {"content": "'] + ["data: y"] * 50 + ["data: [DONE]"]

    streamer = _streamer(lines)
    chunk = next(streamer)

    assert chunk.data.count("y") <= 6
