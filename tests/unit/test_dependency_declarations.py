"""Guard: no test may skip itself on a package nobody installs.

Four tests used to call ``pytest.importorskip("plotly")`` while ``plotly``
appeared in no dependency list (ENG-3431). They skipped 100% of the time in CI,
so three public plotting methods were untested by construction while the suite
reported green.

This test walks every test module, extracts the literal argument of each
``importorskip`` call, and requires the corresponding distribution to be
declared in ``pyproject.toml`` -- either as a runtime dependency or in an
optional-dependency group CI installs.
"""

import ast
import importlib
import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Import name -> distribution name, for the cases where they differ
# (e.g. ``import yaml`` is provided by the ``PyYAML`` distribution).
IMPORT_TO_DISTRIBUTION = {
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
}


def _normalize(name: str) -> str:
    """Normalise a distribution name per PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_distributions() -> set:
    """Distribution names declared in pyproject's dependency arrays.

    Hand-rolled rather than tomllib-based: the SDK supports Python 3.9, where
    ``tomllib`` does not exist, and pulling in a TOML parser just for this check
    is not worth a new dependency.
    """
    names = set()
    section = None
    in_array = False

    for raw_line in PYPROJECT.read_text().splitlines():
        line = raw_line.strip()

        if line.startswith("[") and line.endswith("]") and "=" not in line:
            section = line.strip("[]")
            in_array = False
            continue

        if not in_array:
            is_runtime_deps = section == "project" and line.startswith("dependencies")
            is_optional_group = section == "project.optional-dependencies" and "= [" in line
            if (is_runtime_deps or is_optional_group) and line.endswith("["):
                in_array = True
            continue

        if line.startswith("]"):
            in_array = False
            continue

        match = re.match(r'^"([^"]+)"', line)
        if match:
            # Strip version specifiers, extras and environment markers.
            names.add(_normalize(re.split(r"[<>=!~\[;\s]", match.group(1))[0]))

    return names


def _importorskip_targets():
    """Yield (path, module name) for every ``importorskip`` literal in tests/."""
    for path in sorted(TESTS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name != "importorskip" or not node.args:
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                yield path.relative_to(REPO_ROOT), first.value


def test_pyproject_dependencies_are_parsed():
    """Sanity check on the hand-rolled parser used by the guard below."""
    declared = _declared_distributions()

    assert "requests" in declared, declared  # runtime dependency
    assert "pytest" in declared, declared  # from the `test` extra


def test_every_importorskip_target_is_a_declared_dependency():
    """An `importorskip` on an undeclared package is a permanent silent skip."""
    declared = _declared_distributions()

    undeclared = [
        f"{path}: importorskip({module!r})"
        for path, module in _importorskip_targets()
        if _normalize(IMPORT_TO_DISTRIBUTION.get(module, module)) not in declared
    ]

    assert not undeclared, (
        "These tests skip on a package that is in no dependency list, so they "
        "never run. Declare the package in pyproject.toml (or delete the "
        "tests):\n  " + "\n  ".join(undeclared)
    )


@pytest.mark.parametrize("module", sorted({module for _, module in _importorskip_targets()}))
def test_importorskip_targets_are_actually_importable(module):
    """The declared packages must really be installed in the test environment.

    Deliberately a failure, not a skip: declaring `plotly` but forgetting to
    install it would silently put the four skipped plotting tests right back.
    """
    try:
        importlib.import_module(module)
    except ImportError as exc:  # pragma: no cover - only fires on a broken env
        pytest.fail(
            f"{module!r} is declared in pyproject.toml but is not installed, so every "
            f"test guarded by importorskip({module!r}) silently skips. "
            f"Install the test extra (`pip install '.[test]'`). Import error: {exc}"
        )

    assert importlib.util.find_spec(module) is not None
