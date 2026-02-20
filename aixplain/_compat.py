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
import sys

_REDIRECTS = {
    "aixplain.modules": "aixplain.v1.modules",
    "aixplain.factories": "aixplain.v1.factories",
    "aixplain.enums": "aixplain.v1.enums",
    "aixplain.decorators": "aixplain.v1.decorators",
    "aixplain.base": "aixplain.v1.base",
    "aixplain.processes": "aixplain.v1.processes",
}


class _LegacyImportRedirector(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Intercepts imports for relocated legacy packages and loads them from ``v1/``."""

    def find_module(self, fullname, path=None):
        for old_prefix in _REDIRECTS:
            if fullname == old_prefix or fullname.startswith(old_prefix + "."):
                return self
        return None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        for old_prefix, new_prefix in _REDIRECTS.items():
            if fullname == old_prefix or fullname.startswith(old_prefix + "."):
                new_name = new_prefix + fullname[len(old_prefix) :]
                mod = importlib.import_module(new_name)
                sys.modules[fullname] = mod
                return mod


def install():
    """Install the legacy import redirector (idempotent)."""
    if not any(isinstance(f, _LegacyImportRedirector) for f in sys.meta_path):
        sys.meta_path.insert(0, _LegacyImportRedirector())
