"""Tests that ``.env`` loading is scoped to the working directory (BUG-939).

The working directory's own ``.env`` may not set the endpoint and URL-policy
settings either (BUG-1451): those come only from the real process environment.

A bare ``load_dotenv()`` walks *up* from the CWD, so a ``.env`` shipped inside a
cloned sample project or a bug-report attachment could hand a user's own script a
different ``BACKEND_URL`` and pick the ``TEAM_API_KEY`` out of the ancestor file.
``find_dotenv(usecwd=True)`` is not a fix -- it still walks up when the CWD has no
``.env`` of its own -- so these tests pin the explicit-path behaviour.
"""

import logging
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
    # Ordinary settings still load from the working directory's .env ...
    assert os.environ["TEAM_API_KEY"] == "STOLEN"
    # ... but not the endpoint that decides where that key is sent (BUG-1451).
    assert os.environ.get("BACKEND_URL") is None


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


# --------------------------------------------------------------------------
# BUG-1451: protected names are ignored when they come only from ./.env
# --------------------------------------------------------------------------

PROTECTED_NAMES = [
    "BACKEND_URL",
    "MODELS_RUN_URL",
    "PIPELINES_RUN_URL",
    "FUTURE_SERVICE_RUN_URL",
    "AIXPLAIN_TRUSTED_HOSTS",
    "AIXPLAIN_ALLOW_PRIVATE_FETCH",
    "AIXPLAIN_UPLOAD_HOST_ALLOWLIST",
    "AIXPLAIN_ALLOW_INSECURE_URLS",
    "SENTRY_DSN",
]
FOREIGN_VALUE = "https://not-aixplain.example/secret-path-marker"


def _write_env(directory: Path, lines: dict) -> None:
    (directory / ".env").write_text("".join(f"{k}={v}\n" for k, v in lines.items()))


@pytest.mark.parametrize("name", PROTECTED_NAMES)
def test_protected_name_from_cwd_dotenv_is_dropped_with_a_warning(name, tmp_path, monkeypatch, caplog):
    _write_env(tmp_path, {name: FOREIGN_VALUE, "LOG_LEVEL": "DEBUG"})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    with caplog.at_level(logging.WARNING, logger="aixplain"):
        assert aixplain._load_cwd_dotenv() is True

    assert os.environ.get(name) is None
    assert os.environ["LOG_LEVEL"] == "DEBUG"
    messages = " ".join(r.getMessage() for r in caplog.records if r.name == "aixplain")
    assert name in messages
    assert "secret-path-marker" not in messages


@pytest.mark.parametrize("name", PROTECTED_NAMES)
def test_protected_name_already_exported_is_kept_silently(name, tmp_path, monkeypatch, caplog):
    _write_env(tmp_path, {name: FOREIGN_VALUE})
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(name, "from-the-real-environment")

    with caplog.at_level(logging.WARNING, logger="aixplain"):
        aixplain._load_cwd_dotenv()

    assert os.environ[name] == "from-the-real-environment"
    assert not [r for r in caplog.records if r.name == "aixplain"]


@pytest.mark.parametrize("name", ["BACKEND_URL", "MODELS_RUN_URL"])
def test_https_aixplain_endpoint_in_dotenv_is_kept(name, tmp_path, monkeypatch, caplog):
    value = "https://dev-platform-api.aixplain.com"
    _write_env(tmp_path, {name: value})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(name, raising=False)

    with caplog.at_level(logging.WARNING, logger="aixplain"):
        aixplain._load_cwd_dotenv()

    assert os.environ[name] == value
    assert not [r for r in caplog.records if r.name == "aixplain"]


@pytest.mark.parametrize(
    "value",
    [
        "https://evil-aixplain.com",
        "http://platform-api.aixplain.com",
        "https://platform-api.aixplain.com@evil.example",
        "https://aixplain.com.evil.example",
    ],
)
def test_lookalike_or_insecure_aixplain_endpoint_is_dropped(value, tmp_path, monkeypatch):
    _write_env(tmp_path, {"BACKEND_URL": value})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BACKEND_URL", raising=False)

    aixplain._load_cwd_dotenv()

    assert os.environ.get("BACKEND_URL") is None


def test_aixplain_host_exemption_does_not_cover_trust_flags(tmp_path, monkeypatch):
    _write_env(tmp_path, {"AIXPLAIN_TRUSTED_HOSTS": "https://platform-api.aixplain.com"})
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AIXPLAIN_TRUSTED_HOSTS", raising=False)

    aixplain._load_cwd_dotenv()

    assert os.environ.get("AIXPLAIN_TRUSTED_HOSTS") is None


def test_cwd_dotenv_cannot_redirect_aixplain_end_to_end(tmp_path):
    """Fresh interpreter: ``import aixplain`` + ``Aixplain()`` ignore the cwd .env's endpoint and trust knobs."""
    _write_env(
        tmp_path,
        {
            "BACKEND_URL": "https://not-aixplain.example",
            "AIXPLAIN_TRUSTED_HOSTS": "https://other.example",
            "AIXPLAIN_ALLOW_PRIVATE_FETCH": "1",
            "TEAM_API_KEY": "k" * 40,
        },
    )
    stripped = {"TEAM_API_KEY", "AIXPLAIN_API_KEY", "LOG_LEVEL"} | set(PROTECTED_NAMES)
    env = {key: value for key, value in os.environ.items() if key not in stripped and not key.endswith("_RUN_URL")}
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    script = (
        "import os\n"
        "from aixplain import Aixplain\n"
        "a = Aixplain()\n"
        "print(a.backend_url)\n"
        "print(os.environ.get('AIXPLAIN_TRUSTED_HOSTS'))\n"
        "print(os.environ.get('AIXPLAIN_ALLOW_PRIVATE_FETCH'))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    lines = result.stdout.strip().splitlines()[-3:]
    assert lines == ["https://platform-api.aixplain.com", "None", "None"]
    for name in ("BACKEND_URL", "AIXPLAIN_TRUSTED_HOSTS", "AIXPLAIN_ALLOW_PRIVATE_FETCH"):
        assert name in result.stderr
    assert "not-aixplain.example" not in result.stderr
