"""Guard test: no unjittered network sleep left in the v2 poll paths (BUG-942).

A bare ``time.sleep(wait_time)`` in a poll loop is what keeps a fleet of clients
phase-locked: ``wait_time`` grows deterministically from a shared start, so a
batch launched together never drifts apart and the platform sees synchronized
waves. Every network-facing sleep in the files below must go through
``aixplain.v2._backoff.sleep_with_jitter``.

Modelled on ``test_no_unbounded_requests.py``: AST-based, so a comment or a
string literal can't trip it, and scoped to a fixed file list so it has no
false-positive surface.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# The v2 modules that sleep between network polls.
GUARDED_FILES = [
    "aixplain/v2/resource.py",
    "aixplain/v2/integration.py",
    "aixplain/v2/agent_progress.py",
]

# ``agent_progress`` animates a local spinner at 20 FPS. Those sleeps issue no
# requests, so there is no fleet to decorrelate -- jittering them would only
# make the animation stutter.
ALLOWED_SLEEP_ARGS = frozenset({"DISPLAY_REFRESH_RATE"})


def _bare_sleep_calls(path):
    """``time.sleep(...)`` nodes in *path* that are not on the allowlist."""
    tree = ast.parse((REPO_ROOT / path).read_text())
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "sleep"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "time"):
            continue
        arg = node.args[0] if node.args else None
        # ``time.sleep(self.DISPLAY_REFRESH_RATE)`` / ``time.sleep(X.DISPLAY_REFRESH_RATE)``
        if isinstance(arg, ast.Attribute) and arg.attr in ALLOWED_SLEEP_ARGS:
            continue
        if isinstance(arg, ast.Name) and arg.id in ALLOWED_SLEEP_ARGS:
            continue
        offenders.append(node.lineno)
    return offenders


@pytest.mark.parametrize("path", GUARDED_FILES)
def test_no_unjittered_sleep_in_v2_poll_paths(path):
    offenders = _bare_sleep_calls(path)

    assert not offenders, f"{path} sleeps without jitter at line(s) {offenders}; use sleep_with_jitter"


@pytest.mark.parametrize("path", GUARDED_FILES)
def test_guarded_files_import_the_jitter_helper(path):
    """A file that polls must actually have the helper available.

    Without this, deleting every sleep would satisfy the test above vacuously.
    """
    source = (REPO_ROOT / path).read_text()

    assert "sleep_with_jitter" in source, f"{path} has no jittered sleep"


def test_the_guard_detects_a_regression():
    """Meta-test: the AST walk really does flag a bare sleep."""
    tree = ast.parse("import time\nwait = 5\ntime.sleep(wait)\n")
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "sleep"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "time"
    ]

    assert offenders == [3]
