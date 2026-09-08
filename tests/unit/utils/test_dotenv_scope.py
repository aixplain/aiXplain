"""Tests that ``.env`` loading is scoped to the working directory (BUG-939).

A bare ``load_dotenv()`` walks *up* from the CWD, so a ``.env`` shipped inside a
cloned sample project or a bug-report attachment could hand a user's own script a
different ``BACKEND_URL`` and pick the ``TEAM_API_KEY`` out of the ancestor file.
``find_dotenv(usecwd=True)`` is not a fix -- it still walks up when the CWD has no
``.env`` of its own -- so these tests pin the explicit-path behaviour.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import aixplain

PARENT_ENV = "BACKEND_URL=https://evil.example.com\nTEAM_API_KEY=STOLEN\n"


@pytest.fixture
def nested_tree(tmp_path):
    """Create ``tmp_path/.env`` plus an empty ``tmp_path/child`` directory."""
    (tmp_path / ".env").write_text(PARENT_ENV)
    child = tmp_path / "child"
    child.mkdir()
    return tmp_path, child


def test_parent_dotenv_is_not_loaded(nested_tree, monkeypatch):
    """A ``.env`` one directory up must not reach the process environment."""
    _, child = nested_tree
    monkeypatch.chdir(child)
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv("TEAM_API_KEY", raising=False)

    assert aixplain._load_cwd_dotenv() is False
    assert os.environ.get("BACKEND_URL") is None
    assert os.environ.get("TEAM_API_KEY") is None


def test_cwd_dotenv_is_still_loaded(nested_tree, monkeypatch):
    """The documented behaviour -- a ``.env`` in the working directory -- is kept."""
    parent, _ = nested_tree
    monkeypatch.chdir(parent)
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv("TEAM_API_KEY", raising=False)

    assert aixplain._load_cwd_dotenv() is True
    assert os.environ["BACKEND_URL"] == "https://evil.example.com"


def test_existing_environment_wins(nested_tree, monkeypatch):
    """``override=False`` is preserved: an exported value beats the file."""
    parent, _ = nested_tree
    monkeypatch.chdir(parent)
    monkeypatch.setenv("BACKEND_URL", "https://platform-api.aixplain.com")

    aixplain._load_cwd_dotenv()
    assert os.environ["BACKEND_URL"] == "https://platform-api.aixplain.com"


def test_import_from_nested_cwd_ignores_parent_dotenv(nested_tree):
    """End-to-end: ``import aixplain`` from a subdirectory ignores the ancestor.

    Exercises the real import path in a fresh interpreter rather than just the
    helper, because the walk-up used to happen at import time.
    """
    _, child = nested_tree
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("BACKEND_URL", "TEAM_API_KEY", "AIXPLAIN_API_KEY", "MODELS_RUN_URL", "PIPELINES_RUN_URL")
    }
    # Point at *this* checkout, not whatever copy of the SDK happens to be
    # installed, since the subprocess runs from a temporary directory.
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    result = subprocess.run(
        [sys.executable, "-c", "import aixplain, os; print(os.environ.get('BACKEND_URL'))"],
        cwd=str(child),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "evil.example.com" not in result.stdout
    assert result.stdout.strip() == "None"
