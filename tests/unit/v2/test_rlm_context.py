"""``RLM.run`` treats every ``str`` as text, never as a file path (BUG-1451).

Applications forward end-user text to ``RLM.run``. When a ``str`` that named
an existing file was opened, a "document" of ``.env`` read the server's own
``.env`` and sent it to the worker. Files are now loaded only from a
``pathlib.Path`` or an explicit ``context_path=``.
"""

import builtins
import json
import pathlib
import threading
import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import aixplain.v2.rlm as rlm_v2
from aixplain.v2.rlm import RLM

FILE_CONTENT = "FILE-CONTENT-MARKER-1451"


def _echo_worker():
    """Worker double whose answer is the prompt it received."""
    worker = SimpleNamespace(attributes={}, prompts=[])

    def run(text, max_tokens=None):
        worker.prompts.append(text)
        return SimpleNamespace(completed=True, status="SUCCESS", data=text, used_credits=0.0)

    worker.run = run
    return worker


def _make_rlm():
    rlm = RLM.__new__(RLM)
    rlm.orchestrator_id = "orch-id"
    rlm.worker_id = "worker-id"
    rlm.max_iterations = 3
    rlm.timeout = 60.0
    rlm._orchestrator = None
    rlm._worker = _echo_worker()
    rlm._messages = []
    rlm._used_credits = 0.0
    rlm._credits_lock = threading.Lock()
    client = MagicMock()
    client.api_key = "unit-test-key-0000"
    rlm.context = client
    return rlm


@pytest.fixture
def dotenv_dir(tmp_path, monkeypatch):
    """A working directory holding a ``.env`` and a ``.json`` file."""
    (tmp_path / ".env").write_text(f"SECRET={FILE_CONTENT}\n")
    (tmp_path / "doc.json").write_text(json.dumps({"k": FILE_CONTENT}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(rlm_v2, "_STR_PATH_WARNED", False, raising=False)
    return tmp_path


@pytest.fixture
def open_spy(monkeypatch):
    """Record every path passed to ``open`` while letting the call through."""
    opened = []
    real_open = builtins.open

    def spy(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    return opened


def _worker_saw(rlm, needle):
    return any(needle in p for p in rlm._worker.prompts)


@pytest.mark.parametrize("data", [".env", {"context": ".env"}])
def test_str_naming_a_file_is_treated_as_text(dotenv_dir, open_spy, data):
    rlm = _make_rlm()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        result = rlm.run(data=data, mode="parallel")

    assert result.status == "SUCCESS"
    assert FILE_CONTENT not in result.data
    assert not _worker_saw(rlm, FILE_CONTENT)
    assert not any(p.endswith(".env") for p in open_spy)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"data": pathlib.Path(".env")},
        {"data": {"context": pathlib.Path(".env")}},
        {"context_path": ".env"},
        {"context_path": pathlib.Path(".env")},
        {"data": {"query": "what is SECRET?"}, "context_path": ".env"},
    ],
)
def test_path_or_context_path_still_loads_the_file(dotenv_dir, kwargs):
    rlm = _make_rlm()
    result = rlm.run(mode="parallel", **kwargs)

    assert result.status == "SUCCESS"
    assert _worker_saw(rlm, FILE_CONTENT)


def test_context_path_query_is_used(dotenv_dir):
    rlm = _make_rlm()
    rlm.run(data={"query": "QUERY-MARKER"}, context_path=".env", mode="parallel")
    assert _worker_saw(rlm, "QUERY-MARKER")


def test_unreadable_path_raises():
    with pytest.raises(ValueError):
        RLM._resolve_context(pathlib.Path("/nonexistent/definitely/missing.json"))


def test_json_path_is_parsed_into_a_dict(dotenv_dir):
    assert RLM._resolve_context(pathlib.Path("doc.json")) == {"k": FILE_CONTENT}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        assert RLM._resolve_context("doc.json") == "doc.json"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"data": "some text", "context_path": ".env"},
        {"data": {"context": "x"}, "context_path": ".env"},
        {"data": pathlib.Path(".env"), "context_path": ".env"},
        {},
    ],
)
def test_ambiguous_or_missing_context_is_rejected(dotenv_dir, kwargs):
    with pytest.raises(ValueError):
        _make_rlm().run(mode="parallel", **kwargs)


def test_future_warning_once_without_the_path(dotenv_dir):
    rlm = _make_rlm()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rlm.run(data=".env", mode="parallel")
        rlm.run(data=".env", mode="parallel")

    future = [w for w in caught if issubclass(w.category, FutureWarning)]
    assert len(future) == 1
    message = str(future[0].message)
    assert ".env" not in message
    assert "pathlib.Path" in message and "context_path" in message
    assert future[0].filename == __file__


def test_plain_text_does_not_warn(dotenv_dir):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _make_rlm().run(data="just some prose, not a file", mode="parallel")
    assert not [w for w in caught if issubclass(w.category, FutureWarning)]


@pytest.mark.parametrize("text", ["\\\\server\\share\\x", "//server/share/x"])
def test_unc_like_text_is_not_probed(text, monkeypatch):
    probed = []
    monkeypatch.setattr(rlm_v2.os.path, "isfile", lambda p: probed.append(p) or False)
    rlm_v2._warn_if_str_names_a_file(text)
    assert probed == []
