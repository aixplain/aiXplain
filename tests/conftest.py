import ast
import inspect
import textwrap
from pathlib import Path

import pytest
from typing import Any, Callable

from dotenv import load_dotenv

# Load environment variables once for all tests
load_dotenv(override=True)

SDK_VERSION_ARG = "--sdk_version"
SDK_VERSION_PARAM_ARG = "--sdk_version_param"
PIPELINE_VERSION_ARG = "--pipeline_version"

SDK_VERSION_V1 = "v1"
SDK_VERSION_V2 = "v2"
SDK_VERSIONS = [SDK_VERSION_V1, SDK_VERSION_V2]

PIPELINE_VERSION_2_0 = "2.0"
PIPELINE_VERSION_3_0 = "3.0"
PIPELINE_VERSIONS = [PIPELINE_VERSION_2_0, PIPELINE_VERSION_3_0]


def pytest_addoption(parser: pytest.Parser):
    # Here we're adding the options for the pipeline version and the sdk version
    parser.addoption(f"{PIPELINE_VERSION_ARG}", action="store", help="pipeline version")
    parser.addoption(f"{SDK_VERSION_ARG}", action="store", help="sdk version")
    parser.addoption(f"{SDK_VERSION_PARAM_ARG}", action="store", help="sdk version parameter")


def filter_items(items: list, param_name: str, predicate: Callable):
    """Filter the items based on the parameter name and the predicate.

    Args:
        items (list): The list of items to filter.
        param_name (str): The parameter name to filter by.
        predicate (callable): The predicate to filter by.
    """
    items[:] = [
        item
        for item in items
        if hasattr(item, "callspec")
        and param_name in item.callspec.params
        and predicate(item.callspec.params[param_name])
    ]


def filter_pipeline_version(items: list, pipeline_version: str):
    """Filter the items based on the pipeline version.

    Args:
        items (list): The list of items to filter.
        pipeline_version (str): The pipeline version to filter by.

    Raises:
        ValueError: If the pipeline version is invalid.
    """
    if pipeline_version not in PIPELINE_VERSIONS:
        raise ValueError(f"Invalid pipeline version: {pipeline_version}")

    filter_items(items, "version", lambda version: version == pipeline_version)


def filter_sdk_version(items: list, sdk_version: str, sdk_param: str):
    """Filter the items based on the SDK version.

    Args:
        items (list): The list of items to filter.
        sdk_version (str): The SDK version to filter by.

    Raises:
        ValueError: If the SDK version is invalid.
    """
    if sdk_version not in SDK_VERSIONS:
        raise ValueError(f"Invalid SDK version: {sdk_version}")

    from aixplain.v2.resource import BaseResource

    def predicate(param: Any):
        # v1 SDK uses factory classes (NOT BaseResource subclasses)
        # v2 SDK uses BaseResource subclasses
        return not issubclass(param, BaseResource) if sdk_version == SDK_VERSION_V1 else issubclass(param, BaseResource)

    filter_items(items, sdk_param, predicate)


# ---------------------------------------------------------------------------
# Assertion guard: no collected unit test may be silently assertion-free.
#
# A test that never asserts still reports "passed", so it contributes to a green
# suite while checking nothing (ENG-3431). This runs at collection time, over
# the items pytest actually collected, so it cannot drift out of sync with the
# collection rules the way a standalone lint sweep would.
# ---------------------------------------------------------------------------

UNIT_TESTS_DIR = Path(__file__).resolve().parent / "unit"

# nodeid (without parametrisation suffix) -> reason. Every entry needs a written
# reason and a reviewer: this is an escape hatch for tests whose assertion is
# genuinely expressed some other way, not a place to park unfinished tests.
ASSERT_FREE_ALLOWLIST = {
    # "tests/unit/example_test.py::test_x": "import-only smoke test; failure mode is an exception",
}

# How many levels of same-module helper functions to follow before giving up.
_MAX_HELPER_DEPTH = 3

# Calls that assert without using the `assert` statement. Names beginning with
# `assert` (after any leading underscores) are additionally treated as asserting,
# which covers project-local helpers like `_assert_payload`.
_ASSERTING_CALLS = frozenset(
    {
        # pytest
        "raises",
        "warns",
        "deprecated_call",
        "fail",
        "approx",
        "xfail",
        # unittest.mock
        "assert_called",
        "assert_called_once",
        "assert_called_with",
        "assert_called_once_with",
        "assert_not_called",
        "assert_has_calls",
        "assert_any_call",
        "assert_awaited",
        "assert_awaited_once",
        "assert_awaited_with",
        "assert_awaited_once_with",
        "assert_not_awaited",
        # unittest.TestCase
        "assertEqual",
        "assertNotEqual",
        "assertTrue",
        "assertFalse",
        "assertIn",
        "assertNotIn",
        "assertIs",
        "assertIsNone",
        "assertIsNotNone",
        "assertRaises",
        "assertRaisesRegex",
        "assertAlmostEqual",
        "assertListEqual",
        "assertDictEqual",
    }
)


def _source_tree(func: Callable):
    """Parse *func*'s own source, or return None if it cannot be read."""
    try:
        return ast.parse(textwrap.dedent(inspect.getsource(inspect.unwrap(func))))
    except (OSError, TypeError, SyntaxError, IndentationError):
        return None


def _is_asserting_name(name: str) -> bool:
    return name in _ASSERTING_CALLS or name.lstrip("_").startswith("assert")


def _asserts_in_tree(tree: ast.AST, namespace: dict, depth: int, seen: set) -> bool:
    """True if *tree* asserts, directly or via a helper it calls.

    Following helpers matters because delegating the assertion to a shared
    ``_assert_payload(...)``/``_check_payload(...)`` helper is an ordinary,
    correct way to write a test. Without this, such a test is reported as an
    offender and -- because the guard raises ``UsageError`` -- takes the *entire*
    suite down with it, which is a far worse failure than the one being guarded
    against. Erring toward a false negative here is the right trade.
    """
    called_helpers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if not name:
                continue
            if _is_asserting_name(name):
                return True
            # `helper(...)` resolves against module globals; `self.helper(...)`
            # against the test class, which was merged into `namespace` by the
            # caller. Both are ordinary ways to share an assertion.
            is_self_method = isinstance(func, ast.Attribute) and getattr(func.value, "id", None) == "self"
            if isinstance(func, ast.Name) or is_self_method:
                called_helpers.append(name)

    if depth >= _MAX_HELPER_DEPTH:
        return False

    for name in called_helpers:
        helper = namespace.get(name)
        if not inspect.isfunction(helper) or helper in seen:
            continue
        seen.add(helper)
        subtree = _source_tree(helper)
        if subtree is None:
            # Unreadable helper: assume it asserts rather than aborting the run.
            return True
        if _asserts_in_tree(subtree, getattr(helper, "__globals__", {}), depth + 1, seen):
            return True
    return False


def _has_assertion(func: Callable, cls=None) -> bool:
    """True if the collected test function asserts something.

    Reads the *resolved* function's source rather than sweeping the file, so a
    nested helper named ``test_...`` inside a real test is never mistaken for a
    test of its own -- a file-level AST sweep produces exactly that false
    positive in ``tests/unit/utility_tool_decorator_test.py``.

    *cls* is the enclosing test class, if any, so that ``self._helper(...)``
    can be resolved the same way a module-level helper is.
    """
    tree = _source_tree(func)
    if tree is None:
        # Dynamically generated or otherwise unreadable: give it the benefit of
        # the doubt rather than failing the whole run on a parsing limitation.
        return True

    namespace = dict(getattr(inspect.unwrap(func), "__globals__", {}))
    if cls is not None:
        for klass in reversed(getattr(cls, "__mro__", [cls])):
            namespace.update(vars(klass))

    return _asserts_in_tree(tree, namespace, depth=0, seen=set())


def check_tests_have_assertions(items: list) -> None:
    """Raise if any collected unit test has no assertion.

    Scoped to ``tests/unit`` on purpose: functional tests hit a live backend and
    some of them legitimately assert only by not raising. Widening the scope is
    a follow-up, not a silent side effect of this guard.
    """
    offenders = {}
    for item in items:
        if not isinstance(item, pytest.Function):
            continue
        # `item.path` is pytest >= 7; `item.fspath` covers the >= 6.1 floor in
        # pyproject.toml. Without the fallback the guard would silently inspect
        # nothing on an older pytest -- the exact "green but checking nothing"
        # failure it exists to prevent. `.resolve()` for the same reason: an
        # unresolved item path never matches the resolved UNIT_TESTS_DIR when the
        # checkout sits behind a symlink.
        raw_path = getattr(item, "path", None) or getattr(item, "fspath", None)
        if raw_path is None:  # pragma: no cover - defensive
            continue
        item_path = Path(str(raw_path)).resolve()
        if UNIT_TESTS_DIR not in item_path.parents:
            continue
        # Parametrised tests collect as N items sharing one function; report once.
        base_nodeid = item.nodeid.split("[")[0]
        if base_nodeid in ASSERT_FREE_ALLOWLIST or base_nodeid in offenders:
            continue
        function = getattr(item, "function", None)
        if function is None or _has_assertion(function, getattr(item, "cls", None)):
            continue
        offenders[base_nodeid] = None

    if offenders:
        raise pytest.UsageError(
            "Tests with no assertion (add one, or allowlist it with a written "
            "reason in ASSERT_FREE_ALLOWLIST in tests/conftest.py):\n  " + "\n  ".join(sorted(offenders))
        )


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list):
    """Modify the items based on the pipeline version and the SDK version.

    Args:
        session (pytest.Session): The pytest session.
        config (pytest.Config): The pytest config.
        items (list): The list of items to modify.

    Raises:
        ValueError: If the pipeline version or the SDK version is invalid.
        pytest.UsageError: If a collected unit test has no assertion.
    """
    pipeline_version = config.getoption(f"{PIPELINE_VERSION_ARG}")
    sdk_version = config.getoption(f"{SDK_VERSION_ARG}")

    if pipeline_version:
        filter_pipeline_version(items, pipeline_version)

    if sdk_version:
        sdk_param = config.getoption(f"{SDK_VERSION_PARAM_ARG}")
        if not sdk_param:
            raise ValueError(f"{SDK_VERSION_PARAM_ARG} parameter is required when using {SDK_VERSION_ARG}")
        filter_sdk_version(items, sdk_version, sdk_param)

    # Run last, so it only sees the items that survived the filters above.
    check_tests_have_assertions(items)
