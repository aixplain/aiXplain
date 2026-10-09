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
``BillingError``, ..., and ``get_error_from_status_code``) is no longer
re-exported here: nothing in the SDK raises it, and its ``ValidationError`` /
``ResourceError`` shared names with the v2 classes but were not caught by them.
It is still defined in ``aixplain.exceptions.types``.

