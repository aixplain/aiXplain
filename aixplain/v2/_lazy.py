"""Deferred imports for heavy, optional-path dependencies (BUG-949).

``import aixplain`` imports the evaluation modules eagerly (``v2.core`` needs
``Eval``/``Metric`` at class-definition time), and those modules used to import
``pandas``/``numpy`` at module scope. That cost ~250-450 ms and tens of MB of RSS
on every process start, even for callers that only run agents. ``_LazyModule``
defers the real import to the first attribute access.
"""

import importlib
from types import ModuleType
from typing import Any


class _LazyModule:
    """Module proxy that imports the named module on first attribute access."""

    __slots__ = ("_name", "_mod")

    def __init__(self, name: str) -> None:
        """Record the module name; nothing is imported yet."""
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_mod", None)

    def _load(self) -> ModuleType:
        mod = object.__getattribute__(self, "_mod")
        if mod is None:
            mod = importlib.import_module(object.__getattribute__(self, "_name"))
            object.__setattr__(self, "_mod", mod)
        return mod

    def __getattr__(self, attr: str) -> Any:
        """Import the module (once) and delegate the attribute lookup to it."""
        return getattr(self._load(), attr)

    def __dir__(self) -> list:
        """List the real module's attributes."""
        return dir(self._load())

    def __repr__(self) -> str:
        """Show the proxied module name without importing it."""
        return f"<lazy module {object.__getattribute__(self, '_name')!r}>"
