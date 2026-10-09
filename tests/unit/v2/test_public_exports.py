"""Guard: every public class in ``aixplain/v2`` is root-exported or allowlisted.

``aixplain/__init__.py`` star-re-exports ``aixplain.v2.__all__``, so a name in
that list is importable as ``from aixplain import X``. A new public class that
nobody adds to ``__all__`` silently keeps the version segment in its import
path -- exactly the drift this test exists to catch.

Classes that are deliberately internal (mixins, protocols, ``*Params``,
client/upload helpers) go on ``INTERNAL_ALLOWLIST``. Adding one is a decision,
not an accident: the entry has to be written down here.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import aixplain
import aixplain.v2 as v2

V2_DIR = Path(aixplain.__file__).resolve().parent / "v2"

#: Public classes that intentionally stay off the root surface. Grouped by why.
#: The rule (docs/import-paths.md): a class is exported when a caller types or
#: catches it; it stays internal when it only parameterizes a call.
INTERNAL_ALLOWLIST = frozenset(
    {
        # Client + its retry/timeout internals.
        "AixplainClient",
        # Plain-data / wire plumbing.
        "BaseParams",
        "BaseResource",
        "BaseResult",
        # Mixins and protocols.
        "ActionMixin",
        "BaseMixin",
        "DeleteResourceMixin",
        "GetResourceMixin",
        "HasContext",
        "HasFromDict",
        "HasResourcePath",
        "HasToDict",
        "RunnableResourceMixin",
        "SearchResourceMixin",
        "ToolableMixin",
        # TypedDict search/run param bags (``**kwargs: Unpack[...]``).
        "AgentRunParams",
        "APIKeyDeleteParams",
        "APIKeyGetParams",
        "APIKeySearchParams",
        "BaseDeleteParams",
        "BaseGetParams",
        "BaseRunParams",
        "BaseSearchParams",
        "FileSearchParams",
        "IntegrationSearchParams",
        "ModelRunParams",
        "ModelSearchParams",
        "SkillSearchParams",
        "TriggerDeleteParams",
        "TriggerGetParams",
        "TriggerSearchParams",
        # Upload-utils helpers.
        "ConfigManager",
        "FileValidator",
        "MimeTypeDetector",
        "PresignedUrlManager",
        "RequestManager",
        "S3Uploader",
        # Eval internals.
        "AgentResponseDataFields",
    }
)


def _public_classes() -> list[tuple[str, str]]:
    """Return ``(module, class_name)`` for every public class defined in v2."""
    found: list[tuple[str, str]] = []
    for path in sorted(V2_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                found.append((path.stem, node.name))
    return found


PUBLIC_CLASSES = _public_classes()


@pytest.mark.parametrize("module,name", PUBLIC_CLASSES, ids=[f"{m}.{n}" for m, n in PUBLIC_CLASSES])
def test_public_class_is_exported_or_allowlisted(module, name):
    """A new public class cannot silently miss the package root."""
    assert name in aixplain.__all__ or name in INTERNAL_ALLOWLIST, (
        f"aixplain/v2/{module}.py defines public class {name!r}, but it is neither in "
        f"aixplain.__all__ nor on INTERNAL_ALLOWLIST in {Path(__file__).name}. "
        "Add it to aixplain/v2/__init__.py (import + __all__) if callers use it, "
        "or to the allowlist if it is internal."
    )


def test_allowlist_has_no_stale_entries():
    """An allowlisted name that is exported, or no longer exists, is drift."""
    defined = {name for _, name in PUBLIC_CLASSES}
    stale = sorted(INTERNAL_ALLOWLIST - defined)
    assert stale == [], f"allowlist names no longer defined in aixplain/v2: {stale}"

    both = sorted(INTERNAL_ALLOWLIST & set(aixplain.__all__))
    assert both == [], f"allowlisted but also exported (pick one): {both}"


@pytest.mark.parametrize(
    "name",
    [
        "Model",
        "Integration",
        "ModelResult",
        "AgentRunResult",
        "ToolResult",
        "ActionSpec",
        "ActionInputSpec",
        "Result",
        "Parameter",
        "Usage",
        "StreamChunk",
        "Node",
        "AUTO_DEFAULT_MODEL_ID",
    ],
)
def test_story_names_are_importable_from_the_root(name):
    """The acceptance list, one symbol at a time, and the object is the same."""
    assert getattr(aixplain, name) is getattr(v2, name)


# -- aixplain.exceptions is not a v1 shadow ----------------------------------------


def test_exceptions_package_aliases_the_root():
    """``from aixplain.exceptions import X`` must be the class the SDK raises."""
    import aixplain.exceptions as exceptions

    assert exceptions.ValidationError is aixplain.ValidationError
    assert exceptions.ResourceError is aixplain.ResourceError
    assert exceptions.APIError is aixplain.APIError


def test_a_raised_v2_error_is_caught_through_either_path():
    """The whole point: the obvious spelling catches what is actually raised."""
    from aixplain import ValidationError as RootValidationError
    from aixplain.exceptions import ValidationError as PathValidationError

    with pytest.raises(RootValidationError):
        raise PathValidationError("boom")

    with pytest.raises(PathValidationError):
        raise RootValidationError("boom")


def test_bare_import_binds_the_exceptions_package():
    """``import aixplain`` alone is enough for ``aixplain.exceptions.APIError``.

    Runs in a fresh interpreter: in this process an earlier ``import
    aixplain.exceptions`` would bind the attribute and hide a missing root import.
    """
    code = "import aixplain; assert aixplain.exceptions.APIError is aixplain.APIError"
    env = {**os.environ, "PYTHONPATH": str(V2_DIR.parent.parent)}
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr


def test_exceptions_package_exports_only_the_v2_hierarchy():
    """Every name in ``aixplain.exceptions`` is the root object; no v1 look-alikes."""
    import aixplain.exceptions as exceptions

    for name in exceptions.__all__:
        assert getattr(exceptions, name) is getattr(aixplain, name), name
    for v1_name in ("AixplainBaseException", "AuthenticationError", "get_error_from_status_code"):
        assert not hasattr(exceptions, v1_name), v1_name
    assert "create_operation_failed_error" not in exceptions.__all__


def test_v1_exception_types_stay_importable_from_types():
    """The v1 hierarchy is still defined in ``aixplain.exceptions.types``."""
    from aixplain.exceptions.types import AixplainBaseException, AuthenticationError, get_error_from_status_code

    assert issubclass(AuthenticationError, AixplainBaseException)
    assert isinstance(get_error_from_status_code(401), AuthenticationError)
