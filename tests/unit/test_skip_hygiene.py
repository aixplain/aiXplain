"""Guard: every permanently-skipped test cites a ticket (ENG-3691).

A permanent skip is how a test leaves the CI signal while staying in the tree.
Its reason is the only record of why, so a reason with no ticket key is a skip
nobody owns: it can neither be re-tested against a fixed backend nor deleted
with confidence. This guard requires an ``ENG-``/``PROD-``/``BUG-`` key in the
reason of every *permanent* skip under ``tests/``, which is:

- ``pytest.mark.skip`` (reason as ``reason=`` or the first positional argument);
- ``pytest.mark.skipif`` with no condition, or with a constant truthy literal
  condition such as ``skipif(True, ...)``;
- ``pytest.mark.xfail(run=False)`` under the same condition rule;
- ``pytest.skip(...)`` as a top-level statement of a ``test*`` function body or
  of a module -- not under an ``if``/``try``/loop, where it is conditional.

Those markers are recognised wherever pytest applies them: function and class
decorators, ``pytestmark`` (a marker, list or tuple, at module or class level),
``pytest.param(..., marks=...)``, and a module-level alias
(``skip_x = pytest.mark.skip(...)`` then ``@skip_x``).

A reason resolves through string literals, module- and class-level string
constants (``reason=SOME_CONST``), ``+`` concatenation and f-strings; an
f-string part that cannot be resolved contributes nothing, so the ticket has to
be in the part that can.

Environmental skips -- ``skipif(not os.getenv(...))``, ``pytest.skip`` under an
``if`` -- are not required to cite a ticket: they lift by themselves once the
environment provides what they need.

The detector is a function of a directory rather than of the live tree, so the
tests below can prove it actually detects -- a guard nobody tests is decorative.
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"

#: The ticket projects an owned skip may cite. ``PROD`` and ``BUG`` cover the
#: backend/platform backlogs a functional skip is usually waiting on.
TICKET_PATTERN = re.compile(r"\b(?:ENG|PROD|BUG)-\d+\b")

_SKIP_MARKERS = ("skip", "skipif", "xfail")


def _iter_test_files(directory: Path):
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _dotted(node: ast.AST) -> list:
    """``pytest.mark.skip`` -> ``["skip", "mark", "pytest"]`` (innermost last)."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return parts


def _resolve_text(node: ast.AST, constants: dict):
    """The statically known text of a reason expression, or ``None`` if none is.

    Unresolvable f-string parts are dropped rather than failing the whole string,
    so ``f"... ({SLACK_BUG})"`` resolves when ``SLACK_BUG`` is a known constant.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.JoinedStr):
        pieces = []
        for part in node.values:
            if isinstance(part, ast.FormattedValue):
                part = part.value
            text = _resolve_text(part, constants)
            if text is not None:
                pieces.append(text)
        return "".join(pieces)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_text(node.left, constants)
        right = _resolve_text(node.right, constants)
        if left is None and right is None:
            return None
        return (left or "") + (right or "")
    return None


def _string_constants(body: list, inherited: dict) -> dict:
    """``NAME = <string expression>`` assignments in *body*, layered over *inherited*.

    Assignments are resolved in order, so a constant built from an earlier one
    (``REASON = f"... ({BUG})"``) resolves too.
    """
    constants = dict(inherited)
    for node in body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        text = _resolve_text(value, constants)
        if text is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = text
    return constants


def _as_marker(node: ast.AST, aliases: dict):
    """``(name, call)`` if *node* is a skip/skipif/xfail marker, else ``None``.

    *call* is the ``ast.Call`` carrying the marker's arguments, or ``None`` for a
    bare ``@pytest.mark.skip``. A module-level alias resolves to its marker.
    """
    if isinstance(node, ast.Name) and node.id in aliases:
        return _as_marker(aliases[node.id], {})
    call = node if isinstance(node, ast.Call) else None
    func = call.func if call is not None else node
    if call is not None and isinstance(func, ast.Name) and func.id in aliases:
        # ``skip_x = pytest.mark.skip`` then ``@skip_x(reason=...)``.
        aliased = _as_marker(aliases[func.id], {})
        return (aliased[0], call) if aliased and aliased[1] is None else None
    parts = _dotted(func)
    if parts and parts[0] in _SKIP_MARKERS and "mark" in parts[1:]:
        return parts[0], call
    return None


def _marker_aliases(module: ast.Module) -> dict:
    """Module-level ``name = pytest.mark.skip...`` assignments: name -> marker node."""
    aliases = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and _as_marker(node.value, {}) is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    aliases[target.id] = node.value
    return aliases


def _constant_truthy(node: ast.AST) -> bool:
    # A string condition is an expression pytest evaluates, not a literal truth value.
    return isinstance(node, ast.Constant) and not isinstance(node.value, str) and bool(node.value)


def _is_permanent(name: str, call) -> bool:
    if name == "skip":
        return True
    if call is None:
        # Bare ``@pytest.mark.skipif`` skips unconditionally; bare ``xfail`` still runs.
        return name == "skipif"
    conditions = list(call.args) + [kw.value for kw in call.keywords if kw.arg == "condition"]
    unconditional = not conditions or any(_constant_truthy(c) for c in conditions)
    if name == "skipif":
        return unconditional
    run = next((kw.value for kw in call.keywords if kw.arg == "run"), None)
    return isinstance(run, ast.Constant) and run.value is False and unconditional


def _reason_node(name: str, call):
    if call is None:
        return None
    for keyword in call.keywords:
        if keyword.arg in ("reason", "msg"):
            return keyword.value
    # Only ``skip`` takes its reason positionally; skipif/xfail positionals are conditions.
    if name == "skip" and call.args:
        return call.args[0]
    return None


def _is_pytest_call(node: ast.AST, function: str) -> bool:
    return isinstance(node, ast.Call) and _dotted(node.func) == [function, "pytest"]


class _PermanentSkipScanner(ast.NodeVisitor):
    """Collect ``(label, reason)`` for every permanent skip in one module."""

    def __init__(self, module: ast.Module, prefix: str):
        self.aliases = _marker_aliases(module)
        self.constants = [_string_constants(module.body, {})]
        self.scope = [prefix]
        self.found = []

    def _record(self, label: str, name: str, call) -> None:
        if not _is_permanent(name, call):
            return
        node = _reason_node(name, call)
        reason = None if node is None else _resolve_text(node, self.constants[-1])
        self.found.append((label, reason))

    def _check_markers(self, node: ast.AST, label: str) -> None:
        """*node* is one marker, or a list/tuple of them (``pytestmark``, ``marks=``)."""
        elements = node.elts if isinstance(node, (ast.List, ast.Tuple)) else [node]
        for element in elements:
            marker = _as_marker(element, self.aliases)
            if marker is not None:
                self._record(label, *marker)

    def _check_body(self, body: list, label: str, unconditional_skip: bool) -> None:
        for statement in body:
            if isinstance(statement, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "pytestmark" for t in statement.targets
            ):
                self._check_markers(statement.value, "::".join([*self.scope, "pytestmark"]))
            elif unconditional_skip and isinstance(statement, ast.Expr) and _is_pytest_call(statement.value, "skip"):
                self._record(label, "skip", statement.value)

    def visit_Module(self, node: ast.Module) -> None:
        self._check_body(node.body, self.scope[0], unconditional_skip=True)
        self.generic_visit(node)

    def _visit_definition(self, node: ast.AST) -> None:
        label = "::".join([*self.scope, node.name])
        for decorator in node.decorator_list:
            self._check_markers(decorator, label)
            self.visit(decorator)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_definition(node)
        self.scope.append(node.name)
        self.constants.append(_string_constants(node.body, self.constants[-1]))
        self._check_body(node.body, "::".join(self.scope), unconditional_skip=False)
        for statement in node.body:
            self.visit(statement)
        self.constants.pop()
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_definition(node)
        if node.name.startswith("test"):
            self._check_body(node.body, "::".join([*self.scope, node.name]), unconditional_skip=True)
        for statement in node.body:
            self.visit(statement)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if _is_pytest_call(node, "param"):
            for keyword in node.keywords:
                if keyword.arg == "marks":
                    self._check_markers(keyword.value, "::".join([*self.scope, f"pytest.param@L{node.lineno}"]))
        self.generic_visit(node)


def _permanent_skips(directory: Path) -> list:
    """``(relative/path.py::name, reason)`` for every permanent skip under *directory*."""
    found = []
    for path in _iter_test_files(directory):
        module = ast.parse(path.read_text())
        scanner = _PermanentSkipScanner(module, str(path.relative_to(directory)))
        scanner.visit(module)
        found.extend(scanner.found)
    return found


def _skip_offenders(directory: Path) -> dict:
    """Map ``relative/path.py::name`` -> reason for every unkeyed permanent skip."""
    return {
        label: reason
        for label, reason in _permanent_skips(directory)
        if reason is None or not TICKET_PATTERN.search(reason)
    }


def _scan(tmp_path, source: str) -> dict:
    (tmp_path / "test_sample.py").write_text(source)
    return _skip_offenders(tmp_path)


def test_the_detector_finds_permanent_skips_at_all():
    """Without this the guard could pass on an empty scan."""
    assert _permanent_skips(TESTS_DIR), "no permanent skips found under tests/; the guard is vacuous"


def test_every_skip_reason_cites_a_ticket():
    """The acceptance criterion: no unkeyed permanent skip anywhere under tests/."""
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


HEADER = "import os\n\nimport pytest\n\n"

#: ``(source, expected offenders)`` -- each new capability once flagged, once accepted.
CASES = {
    # A positional reason is a reason.
    "positional-owned": ('@pytest.mark.skip("owned BUG-1234")\ndef test_x():\n    pass\n', {}),
    "positional-unowned": (
        '@pytest.mark.skip("no ticket")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "no ticket"},
    ),
    # f-strings resolve module- and class-level constants; unknown parts contribute nothing.
    "fstring-module-constant": (
        'BUG = "BUG-1098"\n\n@pytest.mark.skip(reason=("rejected: " f"payload ({BUG})"))\ndef test_x():\n    pass\n',
        {},
    ),
    "fstring-unknown-name": (
        '@pytest.mark.skip(reason=f"rejected ({UNKNOWN})")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "rejected ()"},
    ),
    "class-constant": (
        'class TestX:\n    BUG = "BUG-7"\n    REASON = f"broken ({BUG})"\n\n'
        "    @pytest.mark.skip(reason=REASON)\n    def test_a(self):\n        pass\n\n"
        '    @pytest.mark.skip(reason=f"also broken ({BUG})")\n    def test_b(self):\n        pass\n',
        {},
    ),
    "class-constant-unowned": (
        'class TestX:\n    REASON = "broken"\n\n    @pytest.mark.skip(reason=REASON)\n    def test_a(self):\n        pass\n',
        {"test_sample.py::TestX::test_a": "broken"},
    ),
    # pytestmark, as a marker, a list or a tuple, at module or class level.
    "pytestmark-name": ('pytestmark = pytest.mark.skip(reason="x")\n', {"test_sample.py::pytestmark": "x"}),
    "pytestmark-list": (
        'pytestmark = [pytest.mark.flaky, pytest.mark.skip(reason="x")]\n',
        {"test_sample.py::pytestmark": "x"},
    ),
    "pytestmark-tuple": ('pytestmark = (pytest.mark.skip(reason="x"),)\n', {"test_sample.py::pytestmark": "x"}),
    "pytestmark-class": (
        'class TestX:\n    pytestmark = pytest.mark.skip(reason="x")\n',
        {"test_sample.py::TestX::pytestmark": "x"},
    ),
    "pytestmark-owned": ('pytestmark = [pytest.mark.skip(reason="x (ENG-2)")]\n', {}),
    # pytest.param(..., marks=...), single or list.
    "param-marks": (
        "@pytest.mark.parametrize('v', [\n"
        "    1,\n"
        '    pytest.param(2, marks=pytest.mark.skip(reason="x")),\n'
        '    pytest.param(3, marks=[pytest.mark.skip(reason="y")]),\n'
        '    pytest.param(4, marks=pytest.mark.skip(reason="z (PROD-3)")),\n'
        "])\ndef test_x(v):\n    pass\n",
        {"test_sample.py::pytest.param@L7": "x", "test_sample.py::pytest.param@L8": "y"},
    ),
    # xfail(run=False) never runs the body; a plain xfail does.
    "xfail-run-false": (
        '@pytest.mark.xfail(run=False, reason="x")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "x"},
    ),
    "xfail-run-false-owned": ('@pytest.mark.xfail(run=False, reason="x BUG-1")\ndef test_x():\n    pass\n', {}),
    "xfail-runs": ('@pytest.mark.xfail(reason="flaky upstream")\ndef test_x():\n    pass\n', {}),
    "xfail-run-false-environmental": (
        '@pytest.mark.xfail(not os.getenv("K"), run=False, reason="x")\ndef test_x():\n    pass\n',
        {},
    ),
    # An unconditional pytest.skip() in a test body (or a module) is permanent; one under an if is not.
    "body-skip": ('def test_x():\n    pytest.skip("broken")\n', {"test_sample.py::test_x": "broken"}),
    "body-skip-owned": ('def test_x():\n    pytest.skip(reason="broken ENG-9")\n', {}),
    "body-skip-conditional": ('def test_x():\n    if not os.getenv("K"):\n        pytest.skip("needs K")\n', {}),
    "body-skip-in-helper": ('def _helper():\n    pytest.skip("not a test")\n', {}),
    "module-skip": ('pytest.skip("gone", allow_module_level=True)\n', {"test_sample.py": "gone"}),
    # A module-level alias resolves to its marker, called or not.
    "alias": (
        'skip_x = pytest.mark.skip(reason="x")\n\n@skip_x\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "x"},
    ),
    "alias-called": (
        'skip_x = pytest.mark.skip\n\n@skip_x(reason="x")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "x"},
    ),
    "alias-owned": ('skip_x = pytest.mark.skip(reason="x BUG-5")\n\n@skip_x\ndef test_x():\n    pass\n', {}),
    # skipif needs a ticket only when it cannot lift: no condition, or a constant truthy one.
    "skipif-environmental": (
        '@pytest.mark.skipif(not os.getenv("SLACK_TOKEN"), reason="needs SLACK_TOKEN")\ndef test_x():\n    pass\n',
        {},
    ),
    "skipif-environmental-alias": (
        'needs_k = pytest.mark.skipif(not os.getenv("K"), reason="needs K")\n\n@needs_k\ndef test_x():\n    pass\n',
        {},
    ),
    "skipif-string-condition": (
        '@pytest.mark.skipif("sys.platform == \'win32\'", reason="posix only")\ndef test_x():\n    pass\n',
        {},
    ),
    "skipif-constant-true": (
        '@pytest.mark.skipif(True, reason="x")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "x"},
    ),
    "skipif-no-condition": (
        '@pytest.mark.skipif(reason="x")\ndef test_x():\n    pass\n',
        {"test_sample.py::test_x": "x"},
    ),
}


@pytest.mark.parametrize(("source", "expected"), list(CASES.values()), ids=list(CASES))
def test_detector_covers_every_permanent_skip_form(tmp_path, source, expected):
    """Every permanent-skip form is flagged without a ticket; environmental skips never are."""
    assert _scan(tmp_path, HEADER + source) == expected
