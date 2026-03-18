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

#### install

```python
def install()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/_compat.py#L74)

Install the legacy import redirector (idempotent).

