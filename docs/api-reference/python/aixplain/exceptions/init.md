---
sidebar_label: exceptions
title: aixplain.exceptions
---

Exception types for the aiXplain SDK.

This module is the non-versioned exceptions path: ``from aixplain.exceptions
import ValidationError`` resolves to the same class the SDK actually raises, so
``except ValidationError`` catches what it looks like it catches. Before this,
the package carried its own v1-era ``ValidationError`` / ``ResourceError``
classes that nothing in ``aixplain.v2`` raised, and the obvious spelling
silently caught nothing.

The classes the v2 SDK raises are re-exported here from
`aixplain.v2.exceptions`. The v1-only types that have no v2 counterpart
(``AuthenticationError``, ``BillingError``, ...), their base
``AixplainBaseException`` and ``get_error_from_status_code`` are still
re-exported here so existing imports keep working; they are defined in
``aixplain.exceptions.types``.

The two hierarchies are separate. ``ValidationError`` and ``ResourceError``
here are v2 classes and do not subclass ``AixplainBaseException``, and
``get_error_from_status_code`` returns the v1 classes from
``aixplain.exceptions.types``, which ``except ValidationError`` here does not
catch.

