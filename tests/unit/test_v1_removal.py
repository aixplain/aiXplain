"""Guards for the removal of aiXplain SDK v1 (PROD-2918).

Replaces ``test_v1_deprecation_warning.py`` and ``test_v1_deprecation_docs.py``,
which policed a sunset date and a redirector that no longer exist. What has to
stay true now is narrower and permanent: no v1 code ships, every legacy import
fails with a message naming its v2 replacement rather than a bare
``ModuleNotFoundError``, and the docs say the same thing the code does.

The import assertions run in clean subprocesses. ``sys.modules`` caching makes a
second ``import aixplain.factories`` in one interpreter a no-op, and a failed
import leaves no entry, so in-process checks would be testing the cache rather
than the finder.
"""

import os
import pathlib
import re
import subprocess
import sys
import textwrap

import pytest

from aixplain._compat import (
    LAST_V1_RELEASE,
    MIGRATION_GUIDE_URL,
    V1_IMPORT_PREFIXES,
    V1_REMOVED_IN,
    removal_message,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Every import route that used to reach v1: the package itself, the six legacy
#: prefixes the redirector served, and two ``from ... import`` spellings that
#: fail on the parent package rather than on the name the caller asked for.
LEGACY_IMPORTS = [
    "import aixplain.v1",
    "import aixplain.modules",
    "import aixplain.factories",
    "import aixplain.enums",
    "import aixplain.decorators",
    "import aixplain.base",
    "import aixplain.processes",
    "from aixplain.factories import AgentFactory",
    "from aixplain.factories import ModelFactory",
    "from aixplain.modules.model import Model",
]


def _run(script):
    """Run *script* in a clean interpreter against this checkout."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        capture_output=True,
        text=True,
        env=env,
    )


def read(relative_path):
    """Return the text of a repo-relative doc, failing loudly if it is missing."""
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"expected doc {relative_path} to exist at {path}"
    return path.read_text(encoding="utf-8")


# -- v1 is gone ---------------------------------------------------------------------


def test_no_v1_package_in_the_tree():
    """The source of truth for "not present in the published package"."""
    assert not (REPO_ROOT / "aixplain" / "v1").exists(), "aixplain/v1 is back in the tree"


def test_no_module_imports_a_v1_path():
    """No shipped module may reference a legacy import path.

    A leftover ``from aixplain.enums import ...`` inside ``aixplain/`` would now
    raise at import time, so this catches a half-finished removal before a user
    does.
    """
    pattern = re.compile(r"^\s*(?:from|import)\s+aixplain\.(v1|modules|factories|enums|decorators|base|processes)\b")
    offenders = []
    for path in sorted((REPO_ROOT / "aixplain").rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.match(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}")
    assert offenders == [], "shipped modules still import removed v1 paths:\n" + "\n".join(offenders)


def test_importing_aixplain_still_works():
    """Removing v1 must not disturb the package's own import."""
    result = _run("import aixplain; print(aixplain.Aixplain.__name__)")
    assert result.returncode == 0, result.stderr
    assert "Aixplain" in result.stdout


# -- Legacy imports fail with an actionable error ------------------------------------


@pytest.mark.parametrize("statement", LEGACY_IMPORTS)
def test_legacy_import_fails_with_a_named_v2_equivalent(statement):
    """The acceptance criterion, demonstrated literally for every legacy route."""
    result = _run(
        f"""
        import aixplain
        try:
            {statement}
        except ModuleNotFoundError as exc:
            print(exc)
        else:
            raise SystemExit("legacy import unexpectedly succeeded")
        """
    )
    assert result.returncode == 0, result.stderr
    message = result.stdout
    named_v2 = "aix." in message or "aixplain.v2" in message or "from aixplain import Aixplain" in message
    assert named_v2, f"no v2 equivalent named:\n{message}"
    assert V1_REMOVED_IN in message
    assert LAST_V1_RELEASE in message, "the error must name the release users can pin"
    assert MIGRATION_GUIDE_URL in message


def test_legacy_import_is_catchable_as_importerror():
    """Callers guarding an optional import with ``except ImportError`` keep working."""
    result = _run(
        """
        import aixplain
        try:
            import aixplain.factories
        except ImportError as exc:
            print(type(exc).__name__)
        """
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ModuleNotFoundError"


def test_factories_error_names_every_factory_and_the_gaps():
    """``aixplain.factories`` is the busiest route, so its message carries the table.

    Python imports a package before its submodules, so ``from
    aixplain.factories.model_factory import ModelFactory`` fails on
    ``aixplain.factories`` and never reaches a per-submodule message. The
    package-level text therefore has to name every factory itself.
    """
    message = removal_message("aixplain.factories")
    for factory in ("AgentFactory", "ModelFactory", "ToolFactory", "APIKeyFactory"):
        assert factory in message, f"{factory} is missing from the aixplain.factories error"
    for gap in ("IndexFactory", "PipelineFactory", "FinetuneFactory", "WalletFactory"):
        assert gap in message, f"{gap} has no v2 equivalent and must be named as such"


@pytest.mark.parametrize("prefix", V1_IMPORT_PREFIXES)
def test_every_removed_prefix_has_its_own_guidance(prefix):
    """No prefix may fall through to the generic text without saying anything useful."""
    message = removal_message(prefix)
    assert prefix in message
    assert len(message.splitlines()) >= 4, f"{prefix} produced a bare message:\n{message}"


def test_the_guard_defers_to_everything_else():
    """A finder that raised too eagerly would break unrelated imports."""
    result = _run("import aixplain, aixplain.v2.agent, aixplain.utils.url_safety; print('ok')")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


# -- The docs say what the code does -------------------------------------------------

#: Hand-written docs that must describe the removal.
DOCS_WITH_REMOVAL_NOTICE = ["README.md", "AGENTS.md", "docs/README.md", "MIGRATION.md"]


@pytest.mark.parametrize("doc", DOCS_WITH_REMOVAL_NOTICE)
def test_doc_names_the_release_that_removed_v1(doc):
    assert V1_REMOVED_IN in read(doc), f"{doc} does not name the release that removed v1 ({V1_REMOVED_IN})"


def test_migration_guide_names_the_last_release_that_contained_v1():
    """Users who cannot migrate yet need a version to pin, not just a "removed"."""
    assert LAST_V1_RELEASE in read("MIGRATION.md")


def test_migration_guide_no_longer_promises_that_v1_imports_work():
    """The backward-compatibility section is the one that must not survive."""
    migration = read("MIGRATION.md")
    for claim in (
        "Nothing is broken today",
        "still resolves to the same objects",
        "migrate at your own pace",
        "AIXPLAIN_SUPPRESS_V1_DEPRECATION",
    ):
        assert claim not in migration, f"MIGRATION.md still tells users v1 keeps working: {claim!r}"


def test_release_notes_name_the_removal_and_link_the_guide():
    changelog = read("CHANGELOG.md")
    assert V1_REMOVED_IN in changelog
    assert LAST_V1_RELEASE in changelog
    assert "MIGRATION.md" in changelog


def shipped_markdown_files():
    """Yield the repo's hand-written Markdown docs.

    Excludes ``docs/api-reference/`` (regenerated by .github/workflows/docs.yaml)
    and any dot-directory.
    """
    for path in REPO_ROOT.rglob("*.md"):
        relative = path.relative_to(REPO_ROOT)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if "api-reference" in relative.parts:
            continue
        yield relative, path


def test_the_doc_scan_actually_reads_files():
    """Guard the guard: an empty file list would make the scan below vacuous."""
    scanned = [str(relative) for relative, _ in shipped_markdown_files()]
    assert "README.md" in scanned and "MIGRATION.md" in scanned, scanned


def test_no_doc_page_imports_from_a_removed_v1_path():
    """A snippet nobody can run is worse than no snippet.

    ``MIGRATION.md`` is exempt: showing the v1 line next to its v2 replacement is
    the entire point of a migration guide.
    """
    pattern = re.compile(r"^\s*(?:from|import)\s+aixplain\.(v1|modules|factories|enums|decorators|base|processes)\b")
    offenders = []
    for relative, path in shipped_markdown_files():
        if relative.as_posix() == "MIGRATION.md":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.match(line):
                offenders.append(f"{relative}:{number}: {line.strip()}")
    assert offenders == [], "documentation still imports removed v1 paths:\n" + "\n".join(offenders)
