# Import paths

The version segment is not needed in any user-facing import. `from aixplain import X`
is the canonical form for every public name. `from aixplain.v2.<module> import X`
keeps working, so nothing breaks, but new code and docs should use the root.

`aixplain/__init__.py` star-re-exports `aixplain.v2.__all__`, so adding a name to
that list is all it takes to make it importable from the root. A guard test
(`tests/unit/v2/test_public_exports.py`) fails when a public class in
`aixplain/v2/` is neither exported nor on its allowlist, so a new class cannot
silently keep a versioned-only path.

## The rule

Export a class when a caller *types or catches* it: resources, result types,
plain-data input types, and exceptions. Keep it internal when it only
parameterizes a call or is an implementation detail.

Internal classes, on the guard allowlist:

- `AixplainClient` (`client.py`).
- `*SearchParams` / `*GetParams` / `*DeleteParams` / `*RunParams` TypedDicts.
- `Base*` classes, `*Mixin` classes and `Has*` protocols (`resource.py`).
- Upload helpers (`MimeTypeDetector`, `S3Uploader`, `RequestManager`, ...).

The guard only inspects `class` statements. Module-level names that are not
classes -- the retry/timeout constants in `client.py`, the core `*Type`
TypeVars, `plain_data` helpers -- are internal by convention and not checked, so
a new user-facing alias (a `Union` input type, a functional `TypedDict`) has to
be added to `__all__` by hand.

Code that needs an internal keeps the module path, e.g.
`from aixplain.v2.resource import BaseResource`.

## Exceptions

Exceptions have one non-versioned path: `from aixplain import APIError` and
`from aixplain.exceptions import APIError` resolve to the same class. The v2
classes the SDK raises, plus `create_operation_failed_error`, are also
re-exported from `aixplain.exceptions`.

The v1-only types (`AuthenticationError`, `BillingError`, ...), their base
`AixplainBaseException` and `get_error_from_status_code` are defined in
`aixplain.exceptions.types` and still re-exported from `aixplain.exceptions`.
They are a separate hierarchy: the v2 `ValidationError` / `ResourceError` do not
subclass `AixplainBaseException`, and `get_error_from_status_code` returns the v1
classes, which `except aixplain.exceptions.ValidationError` does not catch.
