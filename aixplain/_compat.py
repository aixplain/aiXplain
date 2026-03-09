"""Backward-compatible import redirector for the v1 → legacy reorganization.

After the legacy code was moved from e.g. ``aixplain/modules/`` to
``aixplain/v1/modules/``, this module ensures that all existing import paths
(``from aixplain.modules import …``, ``from aixplain.factories.model_factory import …``,
etc.) continue to work transparently via a custom ``sys.meta_path`` finder.

The redirector is installed once during package init and has negligible runtime
cost — it only activates for import paths that match a known legacy prefix.
"""

import importlib
import importlib.abc
import importlib.util
import sys

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
        mod = importlib.import_module(new_name)
        sys.modules[fullname] = mod
        return mod


def install():
    """Install the legacy import redirector (idempotent)."""
    if not any(isinstance(f, _LegacyImportRedirector) for f in sys.meta_path):
        sys.meta_path.insert(0, _LegacyImportRedirector())
