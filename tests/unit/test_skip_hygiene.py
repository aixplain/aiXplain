"""Guard: every permanently-skipped test cites a ticket (ENG-3691).

``@pytest.mark.skip`` is how a test leaves the CI signal while staying in the
tree. Its ``reason`` is the only record of why, so a reason with no ticket key
is a skip nobody owns: it can neither be re-tested against a fixed backend nor
deleted with confidence. This guard requires an ``ENG-``/``PROD-``/``BUG-`` key
in the reason of every ``skip``/``skipif`` decorator under ``tests/``.

The detector is a function of a directory rather than of the live tree, so the
tests below can prove it actually detects -- a guard nobody tests is decorative.
"""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"

#: The ticket projects an owned skip may cite. ``PROD`` and ``BUG`` cover the
#: backend/platform backlogs a functional skip is usually waiting on.
TICKET_PATTERN = re.compile(r"\b(?:ENG|PROD|BUG)-\d+\b")

_SKIP_MARKERS = ("skip", "skipif")


def _iter_test_files(directory: Path):
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _marker_name(decorator: ast.AST):
    """Return ``skip``/``skipif`` if *decorator* is a skip marker, else ``None``."""
    node = decorator.func if isinstance(decorator, ast.Call) else decorator
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    if parts and parts[0] in _SKIP_MARKERS and "mark" in parts:
        return parts[0]
    return None


def _string_constants(module: ast.Module) -> dict:
    """Top-level ``NAME = "literal"`` assignments, for ``reason=SOME_CONST``."""
    constants = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
            continue
        if not isinstance(node.value.value, str):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                constants[target.id] = node.value.value
    return constants


def _reason_text(decorator: ast.AST, constants: dict):
    if not isinstance(decorator, ast.Call):
        return None
    for keyword in decorator.keywords:
        if keyword.arg != "reason":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
        if isinstance(value, ast.Name) and value.id in constants:
            return constants[value.id]
        # Fall back to source so an f-string still contributes its literal ticket.
        return ast.unparse(value)
    return None


def _skip_offenders(directory: Path) -> dict:
    """Map ``relative/path.py::name`` -> reason for every unkeyed skip."""
    offenders = {}
    for path in _iter_test_files(directory):
        module = ast.parse(path.read_text())
        constants = _string_constants(module)
        for node in ast.walk(module):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for decorator in node.decorator_list:
                if _marker_name(decorator) is None:
                    continue
                reason = _reason_text(decorator, constants)
                if reason is None or not TICKET_PATTERN.search(reason):
                    offenders[f"{path.relative_to(directory)}::{node.name}"] = reason
    return offenders


def test_the_detector_finds_skip_decorators_at_all():
    """Without this the guard could pass on an empty scan."""
    found = 0
    for path in _iter_test_files(TESTS_DIR):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            found += sum(1 for decorator in node.decorator_list if _marker_name(decorator) is not None)
    assert found, "no skip/skipif decorators found under tests/; the guard is vacuous"


def test_every_skip_reason_cites_a_ticket():
    """The acceptance criterion: no unkeyed skip anywhere under tests/."""
    offenders = _skip_offenders(TESTS_DIR)
    assert not offenders, (
        "these skips have no ENG-/PROD-/BUG- ticket in their reason, so nobody owns the "
        f"re-test or the deletion: {offenders}"
    )


def test_detector_flags_a_missing_ticket(tmp_path):
    """The guard has to fail on the thing it guards against."""
    (tmp_path / "test_sample.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.skip(reason="no ticket here")\n'
        "def test_unowned():\n"
        "    assert False\n\n"
        '@pytest.mark.skip(reason="owned (BUG-1234)")\n'
        "def test_owned():\n"
        "    assert False\n"
    )
    assert _skip_offenders(tmp_path) == {"test_sample.py::test_unowned": "no ticket here"}


def test_detector_accepts_skipif_and_constant_reason(tmp_path):
    """A constant reason and a ``skipif`` are both legitimate and must pass."""
    (tmp_path / "test_sample.py").write_text(
        "import pytest\n\n"
        'REASON = "needs a key (ENG-1)"\n\n'
        "@pytest.mark.skipif(True, reason=REASON)\n"
        "def test_skipped():\n"
        "    assert False\n"
    )
    assert _skip_offenders(tmp_path) == {}
