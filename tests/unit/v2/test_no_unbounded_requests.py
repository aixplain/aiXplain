"""Guard test: no unbounded ``requests`` call on the v2 upload/file path.

Without a ``timeout`` ``requests`` waits forever, so a peer that accepts the
connection and then goes silent pins the calling thread with no upper bound
(BUG-938).  Every HTTP dispatch in the files below must either pass ``timeout=``
explicitly, or live in a function that ``setdefault``s one onto the kwargs it
forwards.

Modelled on ``test_no_v1_imports.py``: AST-based so comments and string
literals (e.g. the generated worker code in ``rlm.py``) can't trip it, and
scoped to a fixed file list so it has no false-positive surface.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# The v2 upload/file transfer path. Extending this list is a one-line change.
GUARDED_FILES = [
    "aixplain/v2/client.py",
    "aixplain/v2/upload_utils.py",
    "aixplain/v2/code_utils.py",
    "aixplain/utils/file_utils.py",
]

# ``requests``/``Session`` methods that actually put bytes on a socket.
DISPATCH_ATTRS = frozenset({"get", "post", "put", "patch", "delete", "head", "options", "request", "send"})

# A receiver whose dotted expression contains one of these is an HTTP dispatcher
# rather than an ordinary object (``error_obj.get(...)``, ``payload.get(...)``).
DISPATCH_RECEIVERS = ("requests", "session")


def _receiver_repr(node: ast.AST) -> str:
    """Best-effort dotted-name rendering of a call's receiver expression.

    Handles the three shapes that appear on this path: ``requests.get``,
    ``self.session.request`` and ``cls.create_session().request``.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_receiver_repr(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _receiver_repr(node.func)
    return ""


def _is_http_dispatch(node: ast.Call) -> bool:
    """True if ``node`` looks like an HTTP dispatch on requests/a Session."""
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in DISPATCH_ATTRS:
        return False
    receiver = _receiver_repr(node.func.value).lower()
    return any(marker in receiver for marker in DISPATCH_RECEIVERS)


def _forwards_kwargs(node: ast.Call) -> bool:
    """True if the call splats a mapping (``**kwargs``) into the request."""
    return any(keyword.arg is None for keyword in node.keywords)


def _has_timeout_kwarg(node: ast.Call) -> bool:
    return any(keyword.arg == "timeout" for keyword in node.keywords)


def _sets_default_timeout(func_node: ast.AST) -> bool:
    """True if the enclosing function ``setdefault``s a timeout onto its kwargs."""
    for node in ast.walk(func_node):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "timeout"
        ):
            return True
    return False


def find_unbounded_dispatches(source: str, filename: str = "<source>") -> list:
    """Return ``"line N: <code>"`` for every dispatch with no bounded timeout."""
    tree = ast.parse(source, filename=filename)

    # Map each dispatch to its enclosing function so ``**kwargs`` forwarding can
    # be credited to a ``setdefault`` earlier in that same function.
    enclosing = {}
    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(func_node):
            if isinstance(child, ast.Call) and child not in enclosing:
                enclosing[child] = func_node

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_http_dispatch(node):
            continue
        if _has_timeout_kwarg(node):
            continue
        func_node = enclosing.get(node)
        if _forwards_kwargs(node) and func_node is not None and _sets_default_timeout(func_node):
            continue
        violations.append(f"  line {node.lineno}: {_receiver_repr(node.func)}(...) dispatches without a timeout")
    return violations


@pytest.mark.parametrize("rel_path", GUARDED_FILES)
def test_no_unbounded_requests(rel_path):
    """``rel_path`` must not dispatch HTTP without a bounded timeout."""
    path = REPO_ROOT / rel_path
    assert path.exists(), f"{rel_path} is guarded but missing — update GUARDED_FILES deliberately, not by accident"

    violations = find_unbounded_dispatches(path.read_text(), filename=str(path))
    assert not violations, f"unbounded requests call(s) in {rel_path} (BUG-938):\n" + "\n".join(violations)


class TestDetectorIsNotVacuous:
    """The guard is worthless if it can silently rot into always-passing."""

    @pytest.mark.parametrize(
        "source",
        [
            "import requests\nrequests.get(url)\n",
            "import requests\nrequests.post(url, data=payload)\n",
            "def f(s):\n    return s.session.request('GET', url)\n",
            "def f(cls):\n    return cls.create_session().request(method='GET', url=url)\n",
            "def f(**kwargs):\n    return requests.get(url, **kwargs)\n",
        ],
    )
    def test_flags_unbounded_dispatch(self, source):
        assert find_unbounded_dispatches(source)

    @pytest.mark.parametrize(
        "source",
        [
            "import requests\nrequests.get(url, timeout=(10, 300))\n",
            "def f(s):\n    return s.session.request('GET', url, timeout=5)\n",
            "def f(session, **kwargs):\n    kwargs.setdefault('timeout', (10, 300))\n    return session.request(url, **kwargs)\n",
            # Ordinary attribute access that merely shares a method name.
            "error_obj.get('message')\npayload.get('key', None)\n",
        ],
    )
    def test_accepts_bounded_or_unrelated_calls(self, source):
        assert not find_unbounded_dispatches(source)
