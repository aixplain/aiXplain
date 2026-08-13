"""Backward-compatible import redirector for the v1 → legacy reorganization.

After the legacy code was moved from e.g. ``aixplain/modules/`` to
``aixplain/v1/modules/``, this module ensures that all existing import paths
(``from aixplain.modules import …``, ``from aixplain.factories.model_factory import …``,
etc.) continue to work transparently via a custom ``sys.meta_path`` finder.

The redirector is installed once during package init and has negligible runtime
cost — it only activates for import paths that match a known legacy prefix.

This module is also the single source of truth for the v1 sunset date and the
``DeprecationWarning`` that announces it. Every legacy import route funnels
through the redirector below, which makes it the one place where the deprecation
can be signalled without touching any v1 module.
"""

import importlib
import importlib.abc
import importlib.util
import os
import sys
import warnings

#: The date after which aiXplain SDK v1 is no longer supported. Single source of
#: truth — every hand-written doc (both READMEs, both AGENTS files, ``MIGRATION.md``)
#: is checked against this value by ``tests/unit/test_v1_deprecation_docs.py``.
#: Do not hardcode the date anywhere else; change it here and let the docs follow.
#:
#: Note that the eight v1 factories listed as gaps in ``MIGRATION.md`` have no v2
#: equivalent yet, so this date is contingent on closing them first.
V1_REMOVAL_DATE = "2027-02-01"

#: Human-readable rendering of :data:`V1_REMOVAL_DATE`, as it appears in prose docs.
V1_REMOVAL_DATE_HUMAN = "February 1, 2027"

#: Where users are sent to migrate off v1.
MIGRATION_GUIDE_URL = "https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md"

#: Set this environment variable to any non-empty value to silence the v1 notice.
SUPPRESS_ENV_VAR = "AIXPLAIN_SUPPRESS_V1_DEPRECATION"


class AixplainV1DeprecationWarning(DeprecationWarning):
    """Emitted once per process when aiXplain SDK v1 code is imported.

    Subclasses :class:`DeprecationWarning` so that ``-W error::DeprecationWarning``
    and ``pytest.warns(DeprecationWarning)`` both match it, while still giving users
    a dedicated category they can silence on its own.
    """


#: Guard for the one-notice-per-process rule. Holds :data:`_WARN_KEY` once the notice
#: has been emitted. A set (rather than a bool) so tests can clear it in place.
_WARNED = set()

_WARN_KEY = "v1"

_INTERNAL_MODULE_PREFIXES = ("importlib", "aixplain", "warnings")


def _is_internal_frame_name(name):
    """Return True if *name* belongs to the import machinery or to this package."""
    return any(name == prefix or name.startswith(prefix + ".") for prefix in _INTERNAL_MODULE_PREFIXES)


def _is_bootstrap_frame(frame):
    """Return True if *frame* is one that ``warnings.warn`` does not count.

    Mirrors CPython's own ``is_internal_frame`` check (``Lib/warnings.py`` and
    ``Python/_warnings.c``): frames from ``importlib._bootstrap`` are skipped when
    ``warn`` resolves ``stacklevel``, so they must not consume a level here either.
    """
    filename = frame.f_code.co_filename
    return "importlib" in filename and "_bootstrap" in filename


def _user_stacklevel():
    """Return the ``stacklevel`` of the first frame outside importlib and aixplain.

    Warnings raised from inside a :class:`~importlib.abc.MetaPathFinder` sit under a
    variable number of ``importlib._bootstrap`` frames (measured: 4-7, depending on
    import depth), so any fixed ``stacklevel`` would blame the import machinery
    instead of the user's ``import`` statement.

    Note that ``warnings.warn`` skips ``importlib._bootstrap`` frames when it walks
    the stack, so those frames must not be counted here — counting them overshoots
    the stack and lands on ``warn``'s ``sys:1`` fallback. Falls back to ``2``.
    """
    # This helper is invoked from warn_v1_deprecated's argument list, so sys._getframe(1)
    # is warn_v1_deprecated's own frame — which is what stacklevel=1 refers to at the
    # warnings.warn() call site.
    frame = sys._getframe(1)
    level = 0
    while frame is not None:
        if not _is_bootstrap_frame(frame):
            level += 1
        if not _is_internal_frame_name(frame.f_globals.get("__name__") or ""):
            return max(level, 1)
        frame = frame.f_back
    return 2


def warn_v1_deprecated(import_path):
    """Emit the v1 sunset notice, at most once per process.

    Args:
        import_path: The v1 import path that triggered the notice, e.g.
            ``aixplain.modules``. Named in the message so the user sees a concrete
            path from their own code rather than an abstract "v1 is deprecated".

    Notes:
        The notice is emitted once for the whole v1 surface, not once per module or
        per legacy prefix. A single ``import aixplain.modules`` fans out to ~161
        redirected submodule imports, and v1 imports *itself* through the legacy
        paths (e.g. ``aixplain/v1/enums/function.py`` does
        ``from aixplain.modules.model import Model``). Keying any finer would make
        the SDK warn about itself dozens of times, which is precisely the noise that
        drives users to blanket-suppress ``DeprecationWarning``. One notice plus
        ``MIGRATION.md`` is enough: remediation is a codebase-wide grep, not a
        per-import fix.
    """
    if os.environ.get(SUPPRESS_ENV_VAR):
        return
    if _WARN_KEY in _WARNED:
        return
    _WARNED.add(_WARN_KEY)
    warnings.warn(
        f"'{import_path}' is part of the deprecated aiXplain SDK v1 and will be removed on "
        f"{V1_REMOVAL_DATE_HUMAN} ({V1_REMOVAL_DATE}). Migrate to the v2 API "
        f"('from aixplain import Aixplain'). Migration guide: {MIGRATION_GUIDE_URL}. "
        f"Set {SUPPRESS_ENV_VAR}=1 to silence this notice.",
        AixplainV1DeprecationWarning,
        stacklevel=_user_stacklevel(),
    )


def _reset_v1_deprecation_state():
    """Clear the warn-once state. Test-only."""
    _WARNED.clear()


_REDIRECTS = {
    "aixplain.modules": "aixplain.v1.modules",
    "aixplain.factories": "aixplain.v1.factories",
    "aixplain.enums": "aixplain.v1.enums",
    "aixplain.decorators": "aixplain.v1.decorators",
    "aixplain.base": "aixplain.v1.base",
    "aixplain.processes": "aixplain.v1.processes",
}


class _LegacyImportRedirector(importlib.abc.MetaPathFinder):
    """Intercepts imports for relocated legacy packages and loads them from ``v1/``.

    Implements both the modern (find_spec) and legacy (find_module/load_module) APIs
    so the redirector works on Python 3.9 through 3.12+.
    """

    @staticmethod
    def _resolve(fullname):
        """Return the new ``v1.`` module name if *fullname* matches a legacy prefix."""
        for old_prefix, new_prefix in _REDIRECTS.items():
            if fullname == old_prefix or fullname.startswith(old_prefix + "."):
                return new_prefix + fullname[len(old_prefix) :]
        return None

    # -- Modern API (required for Python 3.12+ where find_module was removed) --

    def find_spec(self, fullname, path, target=None):
        if self._resolve(fullname) is not None:
            return importlib.util.spec_from_loader(fullname, loader=self)
        return None

    def create_module(self, spec):
        new_name = self._resolve(spec.name)
        warn_v1_deprecated(spec.name)
        mod = importlib.import_module(new_name)
        sys.modules[spec.name] = mod
        return mod

    def exec_module(self, module):
        pass

    # -- Legacy API (Python < 3.12) --

    def find_module(self, fullname, path=None):
        if self._resolve(fullname) is not None:
            return self
        return None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        new_name = self._resolve(fullname)
        warn_v1_deprecated(fullname)
        mod = importlib.import_module(new_name)
        sys.modules[fullname] = mod
        return mod


def _make_notice_visible():
    """Un-hide the v1 notice from Python's blanket ``ignore::DeprecationWarning``.

    Python's default filters show ``DeprecationWarning`` only when it is attributed to
    ``__main__``, so a user importing v1 from inside their own package would never see
    the notice — which is how the sunset date managed to pass in silence.

    Appending a filter does not work: ``warnings.filters`` is first-match-wins and the
    stdlib's ``("ignore", None, DeprecationWarning, None, 0)`` entry already matches our
    subclass, so an appended entry is never reached. We therefore insert at the front —
    but only when the user has expressed no warning preference of their own. If
    ``-W`` or ``PYTHONWARNINGS`` is set, ``sys.warnoptions`` is non-empty and we leave
    the filters completely alone. Filters registered programmatically after
    ``import aixplain`` are inserted at index 0 by ``warnings.filterwarnings`` and so
    still take precedence over ours.

    The sharp edge, which is deliberate: a ``warnings.simplefilter("ignore")`` issued
    *before* ``import aixplain`` leaves ``sys.warnoptions`` empty, so it is overridden
    by the filter inserted here. One line, once per process, with three documented off
    switches (the env var, ``-W``/``PYTHONWARNINGS``, or a filter set after the import)
    is judged the right trade for a sunset notice that already expired once unseen.
    ``tests/unit/test_v1_deprecation_warning.py`` pins this behaviour.
    """
    if sys.warnoptions:
        return
    warnings.filterwarnings("default", category=AixplainV1DeprecationWarning)


def install():
    """Install the legacy import redirector and the v1 notice filter (idempotent)."""
    if not any(isinstance(f, _LegacyImportRedirector) for f in sys.meta_path):
        sys.meta_path.insert(0, _LegacyImportRedirector())
    _make_notice_visible()
