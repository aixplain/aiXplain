"""Guard: every pytest marker used under ``tests/`` is registered in pytest.ini (ENG-3691).

``--strict-markers`` turns a typo'd marker (``@pytest.mark.flakey``) into a
collection error instead of a silently inert decoration, but pytest 9.0.x
ignores it when it comes from ``addopts`` and only warns. This static check
gives the same guarantee on every pytest version: a marker name used in a
``pytest.mark.<name>`` expression or passed as a string to ``add_marker`` /
``applymarker`` must be one of pytest's built-ins or listed under ``markers``
in pytest.ini.

The detector is a function of a directory so the tests below can prove it
detects.
"""

import ast
import configparser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"
PYTEST_INI = REPO_ROOT / "pytest.ini"

#: Markers pytest itself registers.
BUILTIN_MARKERS = frozenset({"filterwarnings", "parametrize", "skip", "skipif", "usefixtures", "xfail"})


def _registered_markers(ini_path: Path) -> set:
    parser = configparser.ConfigParser()
    parser.read(ini_path)
    lines = parser.get("pytest", "markers", fallback="").splitlines()
    return {line.split(":", 1)[0].split("(", 1)[0].strip() for line in lines if line.strip()}


def _markers_used(directory: Path) -> dict:
    """Map marker name -> sorted ``relative/path.py:line`` sites where it is used."""
    used = {}
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            name = None
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Attribute)
                and node.value.attr == "mark"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "pytest"
            ):
                name = node.attr
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("add_marker", "applymarker")
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                name = node.args[0].value
            if name is not None:
                used.setdefault(name, []).append(f"{path.relative_to(directory)}:{node.lineno}")
    return used


def _unregistered_markers(directory: Path, ini_path: Path) -> dict:
    allowed = BUILTIN_MARKERS | _registered_markers(ini_path)
    return {name: sites for name, sites in _markers_used(directory).items() if name not in allowed}


def test_the_detector_finds_markers_at_all():
    """Without this the guard could pass on an empty scan."""
    assert "flaky" in _markers_used(TESTS_DIR), "no pytest.mark.flaky found under tests/; the scan is broken"
    assert "flaky" in _registered_markers(PYTEST_INI), "pytest.ini markers did not parse"


def test_every_marker_used_is_registered():
    """The acceptance criterion, independent of whether this pytest honours --strict-markers."""
    unregistered = _unregistered_markers(TESTS_DIR, PYTEST_INI)
    assert not unregistered, f"register these markers under `markers =` in pytest.ini: {unregistered}"


def test_detector_flags_an_unregistered_marker(tmp_path):
    """Attribute and string forms are both caught; built-ins and registered names are not."""
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers =\n    slow: a slow test\n")
    (tmp_path / "test_sample.py").write_text(
        "import pytest\n\n"
        "@pytest.mark.slow\n"
        "@pytest.mark.parametrize('v', [1])\n"
        "@pytest.mark.flakey\n"
        "def test_x(v):\n"
        "    pass\n\n"
        "def pytest_collection_modifyitems(items):\n"
        "    for item in items:\n"
        "        item.add_marker('typo')\n"
    )
    assert _unregistered_markers(tmp_path, tmp_path / "pytest.ini") == {
        "flakey": ["test_sample.py:5"],
        "typo": ["test_sample.py:11"],
    }
