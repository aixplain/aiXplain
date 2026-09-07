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


def test_cli_help_without_api_key(tmp_path):
    """`aixplain --help` must render usage and exit 0 with no credential set.

    The eight CLI commands each declare `--api-key`, which can only be the sole
    source of the key if the process survives long enough for click to parse
    argv. The import-time `validate_api_keys()` call killed it first (BUG-946),
    so a first-run user got a traceback instead of usage text.
    """
    (tmp_path / "sitecustomize.py").write_text(SITECUSTOMIZE)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from aixplain.cli_groups import cli; cli(['--help'])",
        ],
        cwd=str(REPO_ROOT),
        env=_credential_free_env(tmp_path),
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert "has been set" not in output, f"--help still requires a credential:\n{output[-4000:]}"
    assert "Usage:" in result.stdout, f"no usage text:\n{output[-4000:]}"
    assert result.returncode == 0, f"exit code {result.returncode}:\n{output[-4000:]}"


def test_cli_api_key_flag_is_the_sole_key_source(tmp_path):
    """`--api-key K` must authenticate the request with no key in the environment.

    All eight CLI commands declare the flag, but the import-time
    `validate_api_keys()` call killed the process before click ever parsed argv,
    so the flag could never be the only source of the credential (BUG-946). This
    drives one command end to end and asserts the key reaches the outgoing
    `x-api-key` header.
    """
    (tmp_path / "sitecustomize.py").write_text(SITECUSTOMIZE)

    child = """
from unittest.mock import patch, Mock
from click.testing import CliRunner
from aixplain.cli_groups import cli

captured = {}


def fake_request(method, url, **kwargs):
    captured["headers"] = kwargs.get("headers")
    response = Mock()
    response.text = "[]"
    return response


with patch("aixplain.factories.model_factory._request_with_retry", fake_request):
    result = CliRunner().invoke(cli, ["list", "hosts", "--api-key", "cli-only-key"])

print("EXIT", result.exit_code)
print("EXC", repr(result.exception))
print("KEY", (captured.get("headers") or {}).get("x-api-key"))
"""

    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=str(REPO_ROOT),
        env=_credential_free_env(tmp_path),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    assert "EXIT 0" in result.stdout, f"CLI command failed:\n{result.stdout}\n{result.stderr[-2000:]}"
    assert "KEY cli-only-key" in result.stdout, f"--api-key never reached the request:\n{result.stdout}"
