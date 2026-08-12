"""Guard: package discovery in pyproject.toml is declared, not inferred (ENG-3543).

`[tool.setuptools.packages.find].include` patterns are fnmatch'd against the
full dotted package name, so `"aixplain"` matches only the top-level package and
silently discards every subpackage. With no trailing glob a `.git`-less build
shipped 3 of 169 modules -- no error, no warning -- installed cleanly, and then
raised `ModuleNotFoundError: No module named 'aixplain.v2'` at first import. Two
unrelated accidents masked it: a `setuptools-scm` git file sweep and a stale
`aiXplain.egg-info/SOURCES.txt` riding along inside the sdist.

This is the fast half of the guard. The slow half -- actually building the
artifact from a `.git`-less export and importing it -- is the
`package-integrity` job in main.yaml, which only runs on main/test; this file
runs on every branch push via pre-commit.yaml. Neither half subsumes the other:
the static test cannot see a setuptools upgrade changing discovery semantics,
and the CI job does not run on feature branches.
"""

from __future__ import annotations

import sys
from configparser import ConfigParser
from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # `tomllib` is 3.11+; CI runs 3.9. See the `test` extra in pyproject.toml.
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "main.yaml"

#: Directories that hold modules but no __init__.py. They resolve only because
#: `namespaces = true`; see aixplain/_compat.py for the redirects that reach
#: them (aixplain.base -> aixplain.v1.base, aixplain.factories -> ...).
NAMESPACE_ONLY_DIRS = ("aixplain/v1/base", "aixplain/v1/factories/cli")


@pytest.fixture(scope="module")
def pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text())


@pytest.fixture(scope="module")
def find_config(pyproject) -> dict:
    return pyproject["tool"]["setuptools"]["packages"]["find"]


def _package_dirs() -> list[str]:
    """Every directory under aixplain/ that holds at least one module."""
    return sorted(
        {
            path.parent.relative_to(REPO_ROOT).as_posix()
            for path in (REPO_ROOT / "aixplain").rglob("*.py")
            if "__pycache__" not in path.parts
        }
    )


def test_the_scan_finds_the_packages_it_is_meant_to_check():
    """Without this the assertions below could pass vacuously on an empty list."""
    dirs = _package_dirs()
    assert len(dirs) > 20, f"only {len(dirs)} package dirs found under aixplain/: {dirs}"
    for namespace_dir in NAMESPACE_ONLY_DIRS:
        assert namespace_dir in dirs, f"{namespace_dir} no longer holds modules; update NAMESPACE_ONLY_DIRS"


def test_every_package_dir_is_matched_by_an_include_pattern(find_config):
    """The defect itself: a pattern with no glob matches only the top level."""
    include = find_config["include"]
    exclude = find_config.get("exclude", [])

    unmatched = [
        directory
        for directory in _package_dirs()
        if not any(fnmatchcase(directory.replace("/", "."), pattern) for pattern in include)
    ]
    assert not unmatched, (
        f"{len(unmatched)} package director(ies) are not matched by include={include} "
        f"and would be dropped from the wheel: {unmatched[:10]}"
    )

    excluded = [
        directory
        for directory in _package_dirs()
        if any(fnmatchcase(directory.replace("/", "."), pattern) for pattern in exclude)
    ]
    assert not excluded, f"exclude={exclude} discards real packages: {excluded[:10]}"


def test_namespaces_stays_enabled(find_config):
    """`namespaces = false` would drop the two __init__-less dirs back out."""
    missing_init = [d for d in NAMESPACE_ONLY_DIRS if not (REPO_ROOT / d / "__init__.py").exists()]
    if not missing_init:
        pytest.skip("every namespace-only dir gained an __init__.py; this guard is moot")
    assert find_config.get("namespaces") is True, (
        f"namespaces=true is load-bearing: {missing_init} have no __init__.py and are "
        "imported through the aixplain._compat redirector, so flipping it produces a wheel "
        "that looks complete but breaks aixplain.enums"
    )


def test_build_requires_has_no_incidental_setuptools_scm(pyproject):
    """setuptools-scm without config is a git sweep, i.e. a hidden crutch."""
    requires = pyproject["build-system"]["requires"]
    declared = [r for r in requires if r.replace("_", "-").startswith("setuptools-scm")]
    configured = "setuptools_scm" in pyproject.get("tool", {})
    assert not declared or configured, (
        "setuptools-scm is in build-requires with no [tool.setuptools_scm] section; its only "
        "effect is a git file sweep that pulls tracked files into SOURCES.txt and masks broken "
        "package discovery (ENG-3543). Remove it, or configure it deliberately."
    )


def test_license_files_pattern_matches_a_real_file():
    """A pattern that matches nothing is only a warning -- and ships no licence.

    `license_files=LICENSE.rst` matched no file for years; the sdist carried
    LICENSE anyway because the setuptools-scm git sweep hauled it in. Dropping
    the sweep would have shipped an Apache-2.0 distribution with no licence.
    """
    # configparser, not line-splitting: `license_files` is a dangling-list
    # option, so the equally valid multi-line form
    #     license_files =
    #         LICENSE
    # yields an empty first segment that Path.glob rejects with
    # `ValueError: Unacceptable pattern: ''` -- a crash instead of a verdict,
    # in the one test whose job is to be trustworthy.
    parser = ConfigParser()
    parser.read(REPO_ROOT / "setup.cfg")
    raw = parser.get("metadata", "license_files", fallback="")
    patterns = [p.strip() for p in raw.replace(",", "\n").splitlines() if p.strip()]

    assert patterns, "setup.cfg no longer declares license_files"
    for pattern in patterns:
        assert list(REPO_ROOT.glob(pattern)), f"setup.cfg license_files={pattern!r} matches no file in the repo root"


def test_main_workflow_still_gates_the_built_artifact():
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    assert "package-integrity" in jobs, (
        "the package-integrity job is the only check that a built artifact is actually "
        "importable; removing it re-opens ENG-3543"
    )

    # Name-only would pass on a gutted job, which fails just as open as deleting
    # it. Assert the three moves the gate is made of, not their exact wording.
    script = "\n".join(step.get("run", "") for step in jobs["package-integrity"]["steps"])
    for move, what in (
        ("--exclude='.git'", "export the tree without .git"),
        ("-m build", "build an artifact from that export"),
        ("-m venv", "install it into a clean venv"),
    ):
        assert move in script, f"package-integrity no longer seems to {what} ({move!r} is gone)"
