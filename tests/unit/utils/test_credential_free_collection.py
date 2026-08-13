"""Guard: the unit suite must be collectible without any API credential.

``aixplain/utils/config.py`` used to call ``validate_api_keys()`` at module
import time, which made ~27 unit test files fail *at collection* when neither
``TEAM_API_KEY`` nor ``AIXPLAIN_API_KEY`` was set. That coupled the unit suite
to a secret it does not need, and made a rotated key look like a code failure.

This test re-runs collection in a subprocess with both variables stripped. It
also neutralises ``python-dotenv``: ``aixplain/__init__.py`` calls
``load_dotenv()``, which walks *up* the directory tree, so a ``.env`` anywhere
above the checkout would silently supply a key and hide the regression on a
developer machine while still breaking CI.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Imported by the interpreter at startup (via `site`), before anything else can
# read the environment, so the `from dotenv import load_dotenv` in
# aixplain/__init__.py binds the neutered version.
SITECUSTOMIZE = """
import dotenv

dotenv.load_dotenv = lambda *args, **kwargs: False
dotenv.main.load_dotenv = dotenv.load_dotenv
"""


def _credential_free_env(sitecustomize_dir: Path) -> dict:
    env = os.environ.copy()
    env.pop("TEAM_API_KEY", None)
    env.pop("AIXPLAIN_API_KEY", None)
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(sitecustomize_dir), existing_path) if p)
    return env


def test_unit_suite_collects_without_api_key(tmp_path):
    """`pytest tests/unit --collect-only` must exit 0 with no credential set."""
    (tmp_path / "sitecustomize.py").write_text(SITECUSTOMIZE)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit",
            "--collect-only",
            "-q",
            # The rerun plugin binds a socket at startup, which collection does
            # not need and which is blocked in some sandboxed environments.
            "-p",
            "no:rerunfailures",
        ],
        cwd=str(REPO_ROOT),
        env=_credential_free_env(tmp_path),
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert "has been set" not in output, f"collection still requires a credential:\n{output[-4000:]}"
    assert "errors during collection" not in output, f"collection errors:\n{output[-4000:]}"
    assert result.returncode == 0, f"exit code {result.returncode}:\n{output[-4000:]}"


def test_dotenv_neutralisation_actually_works(tmp_path):
    """The neutralisation above must really stop `.env` discovery.

    Without this, `test_unit_suite_collects_without_api_key` could pass for the
    wrong reason on any machine with an ancestor `.env` file.
    """
    (tmp_path / "sitecustomize.py").write_text(SITECUSTOMIZE)

    result = subprocess.run(
        [sys.executable, "-c", "from aixplain.utils import config; print(repr(config.TEAM_API_KEY))"],
        cwd=str(REPO_ROOT),
        env=_credential_free_env(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "''", f"a credential leaked into the subprocess: {result.stdout!r}"
