---
sidebar_label: exceptions
title: aixplain.exceptions
---

Exception types for the aiXplain SDK.

This module is the non-versioned exceptions path: ``from aixplain.exceptions
import ValidationError`` resolves to the same class the SDK actually raises, so
``except ValidationError`` catches what it looks like it catches. Every name
here is the same object as ``aixplain.<name>`` and ``aixplain.v2.exceptions.<name>``.

The v1-era hierarchy (``AixplainBaseException``, ``AuthenticationError``,
``BillingError``, ..., and ``get_error_from_status_code``) is defined in
``aixplain.exceptions.types``. Its names still resolve here for one release,
with a ``DeprecationWarning``, and are removed from this module in
``V1_EXCEPTIONS_REMOVED_IN``. Nothing in the SDK raises them.

#### V1\_EXCEPTIONS\_REMOVED\_IN

Release that drops the deprecated v1 names from this module.

#### \_\_getattr\_\_

```python
def __getattr__(name: str) -> object
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/__init__.py#L55)

Resolve a deprecated v1 name from ``aixplain.exceptions.types``, with a warning.

Kept off ``__all__`` and out of the module namespace so only an actual
access (``from aixplain.exceptions import AuthenticationError``) warns,
not every ``import aixplain``.

