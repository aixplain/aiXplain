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

Internal, on the guard allowlist:

- `AixplainClient` and its retry/timeout internals (`client.py`).
- `*SearchParams` / `*GetParams` / `*DeleteParams` / `*RunParams` TypedDicts.
- `Base*` classes, `*Mixin` classes and `Has*` protocols (`resource.py`).
- Upload helpers (`MimeTypeDetector`, `S3Uploader`, `RequestManager`, ...).
- Core `*Type` aliases, `plain_data` helpers, `create_operation_failed_error`.

Code that needs an internal keeps the module path, e.g.
`from aixplain.v2.resource import BaseResource`.

## Exceptions

Exceptions have one non-versioned path: `from aixplain import APIError` and
`from aixplain.exceptions import APIError` resolve to the same class. The v2
classes the SDK raises are also re-exported from `aixplain.exceptions`; the
v1-only types stay in `aixplain.exceptions.types`.