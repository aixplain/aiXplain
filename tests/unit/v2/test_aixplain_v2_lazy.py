"""Guard: the deprecated ``aixplain.aixplain_v2`` must never be a silent ``None``.

It used to be constructed eagerly at import and the failure swallowed::

    aixplain_v2 = None
    try:
        aixplain_v2 = Aixplain()
    except Exception:
        pass

With no credential that discarded a precise, actionable message -- ``AssertionError:
API key is required. Pass api_key=... to Aixplain() or set TEAM_API_KEY or
AIXPLAIN_API_KEY.`` -- and left a public symbol bound to ``None``, so the first
consumer hit ``AttributeError: 'NoneType' object has no attribute 'Agent'`` far
from the cause (BUG-946).

A module-level ``__getattr__`` now builds it on first access, so ``import aixplain``
still works without a key (``aixplain --help`` and unit-test collection depend on
that) while the real error reaches whoever actually asks for the client.

``Aixplain(api_key=...)`` mutates ``os.environ``, and ``aixplain/__init__.py``
loads a working-directory ``.env``, so every keyless case runs in a subprocess
with the variables stripped and ``python-dotenv`` neutered.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def _run(code: str, tmp_path: Path, with_key: bool = False) -> subprocess.CompletedProcess:
    (tmp_path / "sitecustomize.py").write_text(SITECUSTOMIZE)
    env = _credential_free_env(tmp_path)
    if with_key:
        env["TEAM_API_KEY"] = "unit-test-key"
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


def test_import_succeeds_without_api_key(tmp_path):
    """`import aixplain` must not require a credential."""
    result = _run("import aixplain; print('imported')", tmp_path)

    assert result.returncode == 0, result.stderr[-4000:]
    assert "imported" in result.stdout


def test_access_without_key_raises_the_real_error(tmp_path):
    """Accessing the attribute with no key must raise -- not hand back ``None``."""
    result = _run(
        """
import aixplain

try:
    client = aixplain.aixplain_v2
except AssertionError as e:
    print("RAISED:", e)
else:
    print("RETURNED:", repr(client))
""",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    assert "RAISED: API key is required" in result.stdout, result.stdout
    assert "RETURNED" not in result.stdout


def test_from_import_without_key_raises_too(tmp_path):
    """`from aixplain import aixplain_v2` must go through the same hook."""
    result = _run(
        """
try:
    from aixplain import aixplain_v2
except AssertionError as e:
    print("RAISED:", e)
else:
    print("RETURNED:", repr(aixplain_v2))
""",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    assert "RAISED: API key is required" in result.stdout, result.stdout


def test_star_import_without_key_still_works(tmp_path):
    """`from aixplain import *` must not construct the deprecated client.

    ``aixplain_v2`` is deliberately absent from ``__all__``: leaving it there
    would make a star import raise for a keyless user who intends to construct
    ``Aixplain(api_key=...)`` themselves.
    """
    result = _run(
        "from aixplain import *; print(Aixplain.__name__, File.__name__)",
        tmp_path,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    assert "Aixplain File" in result.stdout


def test_returns_cached_client_when_key_is_set(tmp_path):
    """With a key, the attribute yields one `Aixplain`, stable across accesses."""
    result = _run(
        """
import aixplain
from aixplain import Aixplain

first = aixplain.aixplain_v2
second = aixplain.aixplain_v2
print(isinstance(first, Aixplain), first is second)
""",
        tmp_path,
        with_key=True,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    assert result.stdout.strip().endswith("True True"), result.stdout


def test_first_access_warns_deprecation(tmp_path):
    """First access must emit a `DeprecationWarning` naming the replacement."""
    result = _run(
        """
import warnings
import aixplain

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    aixplain.aixplain_v2

deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
print(len(deprecations))
print(str(deprecations[0].message))
""",
        tmp_path,
        with_key=True,
    )

    assert result.returncode == 0, result.stderr[-4000:]
    lines = result.stdout.strip().splitlines()
    assert lines[0] == "1", result.stdout
    assert "'aixplain.aixplain_v2' is deprecated" in lines[1]
    assert "Aixplain()" in lines[1]


def test_unknown_attribute_still_raises_attribute_error():
    """The hook must not swallow genuine typos."""
    import aixplain

    with pytest.raises(AttributeError, match="no attribute 'not_a_real_symbol'"):
        aixplain.not_a_real_symbol


def test_dir_advertises_aixplain_v2():
    """`dir(aixplain)` must keep listing the lazily provided symbol."""
    import aixplain

    listed = dir(aixplain)
    assert "aixplain_v2" in listed
    assert "Aixplain" in listed
