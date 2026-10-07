---
sidebar_label: v2
title: aixplain.v2
---

aiXplain SDK v2 - Modern Python SDK for the aiXplain platform.

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/__init__.py#L381)

PEP 562: warn on the deprecated ``Resource`` alias, matching ``Aixplain().Resource``.

``Resource`` is deliberately not a plain module attribute, and deliberately
absent from ``__all__``: a plain ``from .file import Resource`` above, or
listing it in ``__all__``, would fire the warning on every
``import aixplain.v2`` (and, transitively, every ``import aixplain`` — its
``from .v2 import *`` walks every name in this module's ``__all__``)
regardless of whether the caller ever touches the name. This way only an
actual access to ``aixplain.v2.Resource`` (or ``from aixplain.v2 import
Resource``) does.

