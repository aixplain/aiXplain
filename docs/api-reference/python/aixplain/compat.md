---
sidebar_label: _compat
title: aixplain._compat
---

Backward-compatible import redirector for the v1 → legacy reorganization.

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

#### V1\_REMOVAL\_DATE

The date after which aiXplain SDK v1 is no longer supported. Single source of
truth — every hand-written doc (both READMEs, both AGENTS files, ``MIGRATION.md``)
is checked against this value by ``tests/unit/test_v1_deprecation_docs.py``.
Do not hardcode the date anywhere else; change it here and let the docs follow.

Note that the eight v1 factories listed as gaps in ``MIGRATION.md`` have no v2
equivalent yet, so this date is contingent on closing them first.

#### V1\_REMOVAL\_DATE\_HUMAN

Human-readable rendering of :data:`V1_REMOVAL_DATE`, as it appears in prose docs.

#### MIGRATION\_GUIDE\_URL

Where users are sent to migrate off v1.

#### SUPPRESS\_ENV\_VAR

Set this environment variable to any non-empty value to silence the v1 notice.

### AixplainV1DeprecationWarning Objects

```python
class AixplainV1DeprecationWarning(DeprecationWarning)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/_compat.py#L43)

Emitted once per process when aiXplain SDK v1 code is imported.

Subclasses :class:`DeprecationWarning` so that ``-W error::DeprecationWarning``
and ``pytest.warns(DeprecationWarning)`` both match it, while still giving users
a dedicated category they can silence on its own.

#### warn\_v1\_deprecated

```python
def warn_v1_deprecated(import_path)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/_compat.py#L103)

Emit the v1 sunset notice, at most once per process.

**Arguments**:

- `import_path` - The v1 import path that triggered the notice, e.g.
  ``aixplain.modules``. Named in the message so the user sees a concrete
  path from their own code rather than an abstract &quot;v1 is deprecated&quot;.
  

**Notes**:

  The notice is emitted once for the whole v1 surface, not once per module or
  per legacy prefix. A single ``import aixplain.modules`` fans out to ~161
  redirected submodule imports, and v1 imports *itself* through the legacy
  paths (e.g. ``aixplain/v1/enums/function.py`` does
  ``from aixplain.modules.model import Model``). Keying any finer would make
  the SDK warn about itself dozens of times, which is precisely the noise that
  drives users to blanket-suppress ``DeprecationWarning``. One notice plus
  ``MIGRATION.md`` is enough: remediation is a codebase-wide grep, not a
  per-import fix.

#### install

```python
def install()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/_compat.py#L229)

Install the legacy import redirector and the v1 notice filter (idempotent).

