"""Tests for the import-time aiXplain SDK v1 deprecation notice.

Import-time warnings are process-global and one-shot: ``sys.modules`` caching means a
second ``import aixplain.modules`` in the same interpreter never re-enters the
redirector. The primary evidence therefore comes from subprocess tests, one clean
interpreter per legacy route; the in-process tests cover the emitter's own logic.
"""

import os
import pathlib
import subprocess
import sys
import textwrap
import warnings
from contextlib import contextmanager

import pytest

from aixplain._compat import (
    MIGRATION_GUIDE_URL,
    SUPPRESS_ENV_VAR,
    V1_REMOVAL_DATE,
    V1_REMOVAL_DATE_HUMAN,
    _WARNED,
    AixplainV1DeprecationWarning,
    _is_internal_frame_name,
    _reset_v1_deprecation_state,
    _user_stacklevel,
    warn_v1_deprecated,
)

#: The worktree root, put on the subprocess PYTHONPATH so the tests always exercise
#: this checkout rather than an aixplain installed in site-packages.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Every documented v1 entry route: the direct package plus the six legacy prefixes
#: redirected by ``aixplain._compat._REDIRECTS``.
LEGACY_IMPORTS = [
    "import aixplain.v1",
    "import aixplain.modules",
    "import aixplain.factories",
    "import aixplain.enums",
    "import aixplain.decorators",
    "import aixplain.base",
    "import aixplain.processes",
    "from aixplain.factories import ModelFactory",
    "from aixplain.modules.model import Model",
]


def _run(script, env_extra=None, warn_opts=()):
    """Run *script* in a clean interpreter and return the CompletedProcess.

    The suppression variable is stripped from the inherited environment first: a
    developer who has taken the SDK's own advice and exported
    ``AIXPLAIN_SUPPRESS_V1_DEPRECATION=1`` must not get a red suite blaming the code
    under test. Tests that need it set pass it back through *env_extra*.
    """
    env = {key: value for key, value in os.environ.items() if key != SUPPRESS_ENV_VAR}
    env.update({"PYTHONPATH": str(REPO_ROOT), **(env_extra or {})})
    argv = [sys.executable]
    for opt in warn_opts:
        argv += ["-W", opt]
    argv += ["-c", textwrap.dedent(script)]
    return subprocess.run(argv, capture_output=True, text=True, env=env)


@contextmanager
def recorded_warnings():
    """Record every warning raised in the block, bypassing the installed filters."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield caught


# -- Subprocess tests: the acceptance criteria, demonstrated literally --------------


@pytest.mark.parametrize("stmt", LEGACY_IMPORTS)
def test_legacy_import_raises_under_werror(stmt):
    """``-W error::DeprecationWarning`` turns the v1 notice into a hard failure."""
    proc = _run(stmt, warn_opts=["error::DeprecationWarning"])
    assert proc.returncode != 0, f"expected a DeprecationWarning for: {stmt}\n{proc.stderr}"
    assert "AixplainV1DeprecationWarning" in proc.stderr, proc.stderr
    assert "deprecated aiXplain SDK v1" in proc.stderr, proc.stderr
    assert V1_REMOVAL_DATE in proc.stderr, proc.stderr
    assert V1_REMOVAL_DATE_HUMAN in proc.stderr, proc.stderr
    assert "MIGRATION.md" in proc.stderr, proc.stderr


@pytest.mark.parametrize("stmt", LEGACY_IMPORTS)
def test_legacy_import_emits_exactly_one_notice(stmt):
    """One notice per process — not one per redirected submodule.

    ``import aixplain.modules`` fans out to ~161 redirected imports, and v1 imports
    itself through the legacy paths, so this guards against the SDK warning about
    itself dozens of times.
    """
    proc = _run(
        f"""
        import warnings
        from aixplain._compat import AixplainV1DeprecationWarning
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            {stmt}
        ours = [w for w in caught if issubclass(w.category, AixplainV1DeprecationWarning)]
        print(len(ours))
        print(ours[0].message if ours else "")
        """
    )
    assert proc.returncode == 0, proc.stderr
    count, message = proc.stdout.splitlines()[:2]
    assert count == "1", f"expected exactly 1 notice for {stmt!r}, got {count}"
    assert V1_REMOVAL_DATE_HUMAN in message


def test_v2_import_is_silent_under_werror():
    """A pure v2 program must not be punished for v1's deprecation."""
    proc = _run("from aixplain import Aixplain", warn_opts=["error::DeprecationWarning"])
    assert proc.returncode == 0, proc.stderr


def test_v2_import_loads_no_v1_modules():
    """The premise behind keeping the v2 path silent, asserted rather than assumed."""
    proc = _run(
        """
        import sys
        import aixplain  # noqa: F401
        print(len([m for m in sys.modules if m == "aixplain.v1" or m.startswith("aixplain.v1.")]))
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "0", f"import aixplain pulled in v1 modules: {proc.stdout}"


def test_env_var_suppresses_the_notice_end_to_end():
    """``AIXPLAIN_SUPPRESS_V1_DEPRECATION=1`` silences a real legacy import."""
    proc = _run(
        """
        import warnings
        from aixplain._compat import AixplainV1DeprecationWarning
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import aixplain.modules  # noqa: F401
        print(len([w for w in caught if issubclass(w.category, AixplainV1DeprecationWarning)]))
        """,
        env_extra={SUPPRESS_ENV_VAR: "1"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "0", "notice fired despite the suppression env var"


# -- Default visibility: the filter registered by install() -------------------------


def test_notice_is_visible_by_default_from_a_non_main_module():
    """Python hides DeprecationWarning outside ``__main__``; ``install()`` un-hides ours.

    Without the filter registered in ``install()``, a user importing v1 from inside
    their own package would never see the notice — which is exactly how the original
    sunset date managed to pass in silence.
    """
    proc = _run(
        """
        import sys, types
        mod = types.ModuleType("some_user_package")
        mod.__file__ = "some_user_package.py"
        sys.modules["some_user_package"] = mod
        exec("import aixplain.modules", mod.__dict__)
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "AixplainV1DeprecationWarning" in proc.stderr, (
        f"notice was hidden when raised outside __main__; stderr was:\n{proc.stderr}"
    )


def test_command_line_ignore_filter_wins_over_the_default_filter():
    """``install()`` must not make the notice unsuppressable."""
    proc = _run("import aixplain.modules", warn_opts=["ignore::DeprecationWarning"])
    assert proc.returncode == 0, proc.stderr
    assert "AixplainV1DeprecationWarning" not in proc.stderr, proc.stderr


def test_install_leaves_filters_alone_when_the_user_set_warn_options():
    """A non-empty ``sys.warnoptions`` means hands off the global filter list."""
    proc = _run(
        """
        import warnings
        from aixplain._compat import AixplainV1DeprecationWarning
        print(any(f[2] is AixplainV1DeprecationWarning for f in warnings.filters))
        """,
        warn_opts=["ignore::DeprecationWarning"],
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False", "install() mutated filters despite -W being set"


def test_pre_import_simplefilter_ignore_is_overridden_by_the_notice_filter():
    """Pins the deliberate sharp edge in ``_make_notice_visible``.

    ``simplefilter("ignore")`` leaves ``sys.warnoptions`` empty, so ``install()`` still
    inserts its filter at the head and the notice is shown anyway. That is the intended
    trade — a sunset notice that already expired once unseen gets one line per process —
    but it is surprising enough to deserve a test rather than a comment, so that flipping
    it later is a deliberate act.
    """
    proc = _run(
        """
        import warnings
        warnings.simplefilter("ignore")
        import aixplain.modules  # noqa: F401
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "AixplainV1DeprecationWarning" in proc.stderr, proc.stderr


def test_env_var_beats_a_pre_import_filter_ordering_problem():
    """The documented off switch works regardless of when filters were configured."""
    proc = _run(
        """
        import warnings
        warnings.simplefilter("ignore")
        import aixplain.modules  # noqa: F401
        """,
        env_extra={SUPPRESS_ENV_VAR: "1"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "AixplainV1DeprecationWarning" not in proc.stderr, proc.stderr


def test_install_registers_the_filter_when_no_warn_options_are_set():
    """With no user preference expressed, the notice must be promoted to visible."""
    proc = _run(
        """
        import warnings
        from aixplain._compat import AixplainV1DeprecationWarning
        print(any(f[2] is AixplainV1DeprecationWarning for f in warnings.filters))
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True"


# -- In-process tests: the emitter's own logic --------------------------------------


@pytest.fixture(autouse=True)
def _clean_warn_state(monkeypatch):
    """Reset the warn-once guard, and unset the off switch, around each test.

    Clearing ``SUPPRESS_ENV_VAR`` keeps the in-process tests hermetic for a developer
    who has it exported in their own shell. Tests that want it set call
    ``monkeypatch.setenv`` in their body, which runs after this fixture and unwinds
    before it.

    Teardown *restores* the guard rather than clearing it. The guard is process-global,
    so leaving it cleared would re-arm the notice for every test module collected after
    this one: any later test that imports a legacy module for the first time inside a
    ``catch_warnings(record=True)`` block would then record an extra warning and fail an
    exact-count assertion — and several modules in this suite count warnings that way.
    """
    monkeypatch.delenv(SUPPRESS_ENV_VAR, raising=False)
    already_warned = set(_WARNED)
    _reset_v1_deprecation_state()
    yield
    _reset_v1_deprecation_state()
    _WARNED.update(already_warned)


def test_warn_names_the_import_path_date_and_guide():
    """The message must be self-sufficient: what, when, where to go, how to silence."""
    with pytest.warns(AixplainV1DeprecationWarning) as record:
        warn_v1_deprecated("aixplain.modules")
    message = str(record[0].message)
    assert "'aixplain.modules'" in message
    assert V1_REMOVAL_DATE_HUMAN in message
    assert V1_REMOVAL_DATE in message
    assert MIGRATION_GUIDE_URL in message
    assert SUPPRESS_ENV_VAR in message
    assert "from aixplain import Aixplain" in message


def test_warn_is_once_per_process_across_different_paths():
    """The notice covers the whole v1 surface, so later routes stay silent."""
    with pytest.warns(AixplainV1DeprecationWarning):
        warn_v1_deprecated("aixplain.modules")
    with recorded_warnings() as caught:
        warn_v1_deprecated("aixplain.factories")
        warn_v1_deprecated("aixplain.modules")
        warn_v1_deprecated("aixplain.v1")
    ours = [w for w in caught if issubclass(w.category, AixplainV1DeprecationWarning)]
    assert ours == [], f"expected silence after the first notice, got {[str(w.message) for w in ours]}"


def test_warn_is_catchable_as_a_plain_deprecation_warning():
    """The dedicated category must not break ``pytest.warns(DeprecationWarning)``."""
    assert issubclass(AixplainV1DeprecationWarning, DeprecationWarning)
    with pytest.warns(DeprecationWarning):
        warn_v1_deprecated("aixplain.v1")


def test_env_var_suppresses_the_emitter(monkeypatch):
    """The env var is checked on every call, not cached at import time."""
    monkeypatch.setenv(SUPPRESS_ENV_VAR, "1")
    with recorded_warnings() as caught:
        warn_v1_deprecated("aixplain.modules")
    assert [w for w in caught if issubclass(w.category, AixplainV1DeprecationWarning)] == []


def test_empty_env_var_does_not_suppress(monkeypatch):
    """An empty value is not a preference — only a non-empty value silences the notice."""
    monkeypatch.setenv(SUPPRESS_ENV_VAR, "")
    with pytest.warns(AixplainV1DeprecationWarning):
        warn_v1_deprecated("aixplain.modules")


def test_suppression_does_not_consume_the_warn_once_budget(monkeypatch):
    """Suppressing must not mark the notice as delivered, so unsetting still warns."""
    monkeypatch.setenv(SUPPRESS_ENV_VAR, "1")
    with recorded_warnings():
        warn_v1_deprecated("aixplain.modules")
    monkeypatch.delenv(SUPPRESS_ENV_VAR)
    with pytest.warns(AixplainV1DeprecationWarning):
        warn_v1_deprecated("aixplain.modules")


# -- The computed stacklevel --------------------------------------------------------


def test_user_stacklevel_attributes_the_notice_to_the_caller():
    """A fixed stacklevel would blame importlib; the computed one blames this test."""
    with pytest.warns(AixplainV1DeprecationWarning) as record:
        warn_v1_deprecated("aixplain.modules")
    assert record[0].filename == __file__, (
        f"expected the notice to be attributed to {__file__}, got {record[0].filename}"
    )


@pytest.mark.parametrize(
    "stmt",
    [
        "import aixplain.modules",
        "from aixplain.modules.model import Model",
        "from aixplain.factories import ModelFactory",
        "import aixplain.v1",
    ],
)
def test_notice_is_attributed_to_the_users_own_import_line(tmp_path, stmt):
    """The notice must blame the user's ``import``, not the import machinery.

    ``warnings.warn`` skips ``importlib._bootstrap`` frames when resolving
    ``stacklevel``; counting them would overshoot the stack and land on warn's
    ``sys:1`` fallback, so the user would be told nothing about where the import was.
    A real file inside a real package is used because that is the shape that broke.
    """
    pkg = tmp_path / "some_user_package"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "service.py").write_text(f"{stmt}  # noqa: F401\n")
    (tmp_path / "app.py").write_text("from some_user_package import service  # noqa: F401\n")

    proc = subprocess.run(
        [sys.executable, "app.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert proc.returncode == 0, proc.stderr
    assert "AixplainV1DeprecationWarning" in proc.stderr, proc.stderr
    notice_lines = [line for line in proc.stderr.splitlines() if "AixplainV1DeprecationWarning" in line]
    assert len(notice_lines) == 1, proc.stderr
    location = notice_lines[0].split(": AixplainV1DeprecationWarning")[0]
    assert location.endswith("service.py:1"), f"notice was attributed to {location!r}, not the user's import"


def test_user_stacklevel_stops_at_the_first_external_frame():
    """Called directly from external code, the very first frame examined is the answer.

    In production the helper runs one frame deeper (inside ``warn_v1_deprecated``), so
    the emitter's own frame is what occupies level 1 there; see the attribution tests
    above for that path.
    """
    assert _user_stacklevel() == 1


@pytest.mark.parametrize(
    ("name", "internal"),
    [
        ("aixplain", True),
        ("aixplain.v1.modules", True),
        ("importlib", True),
        ("importlib._bootstrap", True),
        ("warnings", True),
        ("", False),
        ("aixplain_extras", False),  # must not be swallowed by a bare startswith
        ("importlibrary", False),
        ("my_app.services", False),
    ],
)
def test_is_internal_frame_name(name, internal):
    """Prefix matching must be package-aware, not a bare string prefix test."""
    assert _is_internal_frame_name(name) is internal
