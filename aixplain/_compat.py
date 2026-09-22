"""Actionable failures for the removed aiXplain SDK v1 import paths.

v1 -- the legacy factory API reached through ``aixplain.factories``,
``aixplain.modules``, ``aixplain.enums``, ``aixplain.decorators``,
``aixplain.base``, ``aixplain.processes`` and ``aixplain.v1`` -- was removed in
:data:`V1_REMOVED_IN`. Those packages no longer exist, so Python's own answer
would be a bare ``ModuleNotFoundError: No module named 'aixplain.factories'``,
which tells a user nothing about where the code went.

This module installs a :class:`~importlib.abc.MetaPathFinder` that intercepts
exactly those prefixes and raises a ``ModuleNotFoundError`` naming the v2
replacement, the last release that still shipped v1, and the migration guide.
It is the only thing left of the old redirector: nothing is redirected, and no
v1 code ships.

The finder is also the single source of truth for the removal metadata every
hand-written doc quotes; ``tests/unit/test_v1_removal.py`` fails if a doc
disagrees with it.
"""

import importlib.abc
import sys

#: The first release that ships without v1. Quoted by the docs; change it here.
V1_REMOVED_IN = "0.3.0"

#: The last release that contained v1. It stays on PyPI and stays installable,
#: so a caller who cannot migrate yet has somewhere to pin.
LAST_V1_RELEASE = "0.2.48"

#: Where users are sent to migrate off v1.
MIGRATION_GUIDE_URL = "https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md"

#: The legacy top-level packages that no longer exist. Every name below (and
#: every submodule of it) gets the tailored error rather than a bare one.
V1_IMPORT_PREFIXES = (
    "aixplain.v1",
    "aixplain.modules",
    "aixplain.factories",
    "aixplain.enums",
    "aixplain.decorators",
    "aixplain.base",
    "aixplain.processes",
)

#: v1 factory -> v2 replacement, as spelled in MIGRATION.md. Listed in the error
#: for ``aixplain.factories`` because the import fails on the *package*, so the
#: symbol the caller actually asked for (``from aixplain.factories import
#: AgentFactory``) is not available to name individually.
_FACTORY_MAP = (
    ("AgentFactory", "aix.Agent"),
    ("TeamAgentFactory", "aix.Agent(..., subagents=[...])"),
    ("ModelFactory", "aix.Model"),
    ("ToolFactory", "aix.Tool"),
    ("IntegrationFactory", "aix.Integration"),
    ("MetricFactory", "aix.Metric"),
    ("APIKeyFactory", "aix.APIKey"),
    ("FileFactory", "aix.File"),
    ("ScriptFactory", "aix.Utility"),
)

#: The eight factories that never got a v2 equivalent. Named explicitly so a
#: caller who depends on one learns to pin rather than hunting for a v2 spelling
#: that does not exist.
_FACTORY_GAPS = (
    "IndexFactory",
    "PipelineFactory",
    "BenchmarkFactory",
    "CorpusFactory",
    "DataFactory",
    "DatasetFactory",
    "FinetuneFactory",
    "WalletFactory",
)

#: v1 domain object -> v2 replacement, for the ``aixplain.modules`` message.
_MODULE_MAP = (
    ("Agent", "aix.Agent"),
    ("TeamAgent", "aix.Agent(..., subagents=[...])"),
    ("Model", "aix.Model"),
    ("LLM", "aix.Model"),
    ("Tool", "aix.Tool"),
    ("UtilityModel", "aix.Utility"),
    ("APIKey", "aix.APIKey"),
    ("File", "aix.File"),
)

#: Guidance keyed by removed prefix. Keyed by *prefix*, not by exact module,
#: because Python imports a package before its submodules: ``import
#: aixplain.factories.model_factory`` fails on ``aixplain.factories``, so the
#: submodule name never reaches a finder and a per-submodule table would be
#: unreachable. Each prefix message therefore carries its whole mapping.
_PREFIX_GUIDANCE = {
    "aixplain.factories": (
        "Construct a client and use its resources:\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()\n"
        + "".join(f"  {old:<18} -> {new}\n" for old, new in _FACTORY_MAP)
        + "  No v2 equivalent: "
        + ", ".join(_FACTORY_GAPS)
        + "."
    ),
    "aixplain.modules": (
        "v2 resources replace the v1 domain objects:\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()\n" + "".join(f"  {old:<12} -> {new}\n" for old, new in _MODULE_MAP)
    ).rstrip("\n"),
    "aixplain.enums": (
        "Import the enums from the package root -- 'from aixplain import Function, Supplier, "
        "License, Language, Privacy, DataType, StorageType' -- or read them off a client "
        "('aix.Function'). Most of them also accept their plain string value now."
    ),
    "aixplain.decorators": (
        "Internal v1 helper with no public v2 counterpart. Start from\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()"
    ),
    "aixplain.base": (
        "Internal v1 helper with no public v2 counterpart. Start from\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()"
    ),
    "aixplain.processes": (
        "v1 data onboarding (corpora, datasets, data assets) has no v2 counterpart. "
        "Everything else starts from\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()"
    ),
    "aixplain.v1": (
        "The whole v1 surface is gone. Start from\n"
        "    from aixplain import Aixplain\n"
        "    aix = Aixplain()\n"
        "  and read resources off the client: aix.Agent, aix.Model, aix.Tool, aix.APIKey, ..."
    ),
}


def _matched_prefix(fullname):
    """Return the removed v1 prefix *fullname* belongs to, or None."""
    for prefix in V1_IMPORT_PREFIXES:
        if fullname == prefix or fullname.startswith(prefix + "."):
            return prefix
    return None


def removal_message(fullname):
    """Build the ``ModuleNotFoundError`` text for a removed v1 import path.

    Args:
        fullname: The module the caller tried to import, e.g.
            ``aixplain.factories``. Named in the message so the error points at
            the caller's own import statement rather than at "v1" in the
            abstract.

    Returns:
        str: A message naming the v2 equivalent, the last release that shipped
        v1, and the migration guide.
    """
    prefix = _matched_prefix(fullname)
    guidance = _PREFIX_GUIDANCE.get(prefix, _PREFIX_GUIDANCE["aixplain.v1"])
    return (
        f"'{fullname}' was part of aiXplain SDK v1, which was removed in {V1_REMOVED_IN}.\n"
        f"{guidance}\n"
        f"The last release that shipped v1 is {LAST_V1_RELEASE}; pin it with "
        f"\"pip install 'aiXplain=={LAST_V1_RELEASE}'\" if you need more time.\n"
        f"Migration guide: {MIGRATION_GUIDE_URL}"
    )


class _RemovedV1Finder(importlib.abc.MetaPathFinder):
    """Turns an import of a removed v1 path into an error that says what to use.

    Raising from ``find_spec`` rather than returning a spec whose loader raises
    keeps the traceback short -- it ends at the user's ``import`` statement --
    and still produces a ``ModuleNotFoundError``, so ``except ImportError``
    around an optional import keeps working.
    """

    def find_spec(self, fullname, path=None, target=None):
        """Raise for a removed v1 path; return None (defer) for anything else."""
        if _matched_prefix(fullname) is None:
            return None
        raise ModuleNotFoundError(removal_message(fullname), name=fullname)

    # -- Legacy API (Python < 3.12, where find_module is still consulted) --

    def find_module(self, fullname, path=None):
        """Raise for a removed v1 path; return None (defer) for anything else."""
        if _matched_prefix(fullname) is None:
            return None
        raise ModuleNotFoundError(removal_message(fullname), name=fullname)


def install():
    """Install the removed-v1 import guard (idempotent)."""
    if not any(isinstance(finder, _RemovedV1Finder) for finder in sys.meta_path):
        sys.meta_path.insert(0, _RemovedV1Finder())
