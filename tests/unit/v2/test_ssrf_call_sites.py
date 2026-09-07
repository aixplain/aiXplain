"""Tests that every caller/response URL sink goes through the SSRF guard (BUG-939).

``validators.url()`` is a syntax check, and against the pinned validators 0.35.0
it returns True for ``http://169.254.169.254/latest/meta-data/``,
``http://127.0.0.1:8080/x`` and ``http://10.0.0.1/``. Each sink below used to
fetch such a URL directly; these tests assert that the request is now refused
before any socket is opened.
"""

import ast
import socket
from pathlib import Path

import pytest
import requests

from aixplain.utils.url_safety import UnsafeURLError

METADATA_URL = "http://169.254.169.254/latest/meta-data/"

REPO_ROOT = Path(__file__).resolve().parents[3]

# Every module that fetches a URL chosen by a caller or by a response body.
GUARDED_SINK_FILES = [
    "aixplain/v2/code_utils.py",
    "aixplain/v2/rlm.py",
    "aixplain/v1/modules/model/utils.py",
    "aixplain/v1/modules/model/rlm.py",
    "aixplain/v1/modules/agent/tool/sql_tool.py",
    "aixplain/v1/factories/model_factory/utils.py",
]


@pytest.fixture(autouse=True)
def no_sockets(monkeypatch):
    """Fail loudly if any of these code paths actually tries to connect."""

    def explode(*args, **kwargs):
        raise AssertionError("an outbound request was attempted")

    monkeypatch.setattr(requests.Session, "send", explode)
    monkeypatch.setattr(socket, "create_connection", explode)


def test_parse_code_refuses_a_metadata_url():
    """The v2 utility-model sink no longer fetches the cloud metadata endpoint."""
    from aixplain.v2.code_utils import parse_code

    with pytest.raises(UnsafeURLError):
        parse_code(METADATA_URL)


def test_parse_code_decorated_refuses_a_private_url():
    """The decorated variant is the second sink in the same module."""
    from aixplain.v2.code_utils import parse_code_decorated

    with pytest.raises(UnsafeURLError):
        parse_code_decorated("http://127.0.0.1:8080/tool.py")


def test_rlm_url_context_is_guarded():
    """``_resolve_url_context`` fetches a caller-supplied URL, so it is gated."""
    from aixplain.v2.rlm import RLM

    with pytest.raises(UnsafeURLError):
        RLM._resolve_url_context(METADATA_URL)


def test_v1_parse_code_refuses_a_private_url():
    """v1 gets the same guard, as a one-line call-site change."""
    from aixplain.v1.modules.model.utils import parse_code

    with pytest.raises(UnsafeURLError):
        parse_code("http://10.0.0.1/code.py")


def test_v1_model_factory_version_link_is_guarded():
    """A ``version.id`` taken from a response is a blind-SSRF port scanner otherwise.

    The surrounding ``except Exception: code = ""`` is left in place (v1 is
    unmaintained), so the guard has to refuse the request rather than rely on an
    informative exception reaching the caller.
    """
    from aixplain.utils.url_safety import safe_get
    from aixplain.v1.factories.model_factory import utils as factory_utils

    assert factory_utils.safe_get is safe_get
    with pytest.raises(UnsafeURLError):
        factory_utils.safe_get("http://127.0.0.1:22/")


def test_v1_benchmark_report_url_is_guarded():
    """``reportUrl`` is also a response field, so it is validated before download."""
    from aixplain.utils.url_safety import validate_fetch_url
    from aixplain.v1.modules import benchmark_job

    assert benchmark_job.validate_fetch_url is validate_fetch_url
    with pytest.raises(UnsafeURLError):
        benchmark_job.validate_fetch_url("http://169.254.169.254/latest/meta-data/")


def _fetch_sinks(path):
    """Return the ``requests.<verb>(...)`` dispatch nodes in *path*.

    String literals are ignored, which matters because ``rlm.py`` embeds worker
    source code that legitimately calls ``requests.get`` *inside the sandbox*.
    """
    tree = ast.parse((REPO_ROOT / path).read_text())
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        target = node.func
        if target.attr not in ("get",) or not isinstance(target.value, ast.Name):
            continue
        if target.value.id == "requests":
            found.append(node.lineno)
    return found


@pytest.mark.parametrize("path", GUARDED_SINK_FILES)
def test_no_direct_requests_get_remains(path):
    """Guard test: these modules must reach remote URLs only via ``safe_get``."""
    assert _fetch_sinks(path) == [], f"{path} still calls requests.get directly"
