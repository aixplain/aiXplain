"""aiXplain SDK v1 - Legacy SDK modules, factories, and enums.

.. deprecated::
    SDK v1 is deprecated and will be removed on February 1, 2027. Use the v2 API
    (``from aixplain import Aixplain``) instead. For a factory-by-factory migration
    map see https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md — the guide
    is not shipped inside the wheel, so an installed copy has no local ``MIGRATION.md``
    to read.

    Importing this package (or any legacy path that redirects into it, such as
    ``aixplain.modules`` or ``aixplain.factories``) emits an
    :class:`aixplain._compat.AixplainV1DeprecationWarning`. It is emitted at most once
    per process, for the whole v1 surface — not once per module and not once per legacy
    prefix — and names whichever import path tripped it first.
    Set ``AIXPLAIN_SUPPRESS_V1_DEPRECATION=1`` to silence it.
"""

from aixplain._compat import warn_v1_deprecated

# Warn unconditionally at import time rather than via a PEP 562 module __getattr__:
# submodule imports (``import aixplain.v1.factories``) bypass the parent package's
# __getattr__, so a lazy hook would stay silent for the most common usage.
warn_v1_deprecated("aixplain.v1")
