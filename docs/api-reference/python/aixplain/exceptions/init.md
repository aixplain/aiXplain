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
(``AuthenticationError``, ``BillingError``, ...) are kept importable from
``aixplain.exceptions.types`` so existing imports keep working.

