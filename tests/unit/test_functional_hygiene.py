"""Guard: functional tests only touch resources they created (BUG-947).

The functional suite runs against the production tenant on every push to `main`,
and two of its tests mutated live data they did not own: one rewrote the rate
limits of the *first* key ``APIKeyFactory.list()`` happened to return and never
restored them, and a module-scoped autouse fixture deleted every production key
named ``"Test API Key"`` -- with the failure swallowed.

Both were fixed by review once before and both came back, so the invariants are
asserted here instead. These checks are static and credential-free, so they run
in the `unit-coverage` job and in pre-commit: a regression fails when it is
written rather than after it has already randomised a customer's rate limits.

Each detector takes its directory as a parameter so it can be pointed at a
synthetic tree and tested -- the `_blanket_skip_offenders` precedent in
tests/unit/test_ci_matrix_coverage.py. A guard nobody tested is decorative.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FUNCTIONAL_DIR = REPO_ROOT / "tests" / "functional"
APIKEY_DIR = FUNCTIONAL_DIR / "apikey"

#: The one place `resource_tracker` may be defined.
TRACKER_CONFTEST = "tests/functional/conftest.py"

#: The generic name the old sweep matched on. A human could plausibly have named
#: a real key this, which is why deleting by it reached beyond the test's own
#: resources. Banned from the apikey directory entirely -- including the JSON
#: fixture, which is where the literal originally came from -- so the sweep
#: cannot be reconstructed from anything left in the tree. The mocked unit tests
#: in tests/unit/api_key_test.py may keep using it: they talk to no tenant.
GENERIC_API_KEY_NAME = "Test API Key"

#: Env flag that opts a test into an upload the SDK cannot delete. A decorator
#: may name it either as the literal or through a module constant, so both
#: spellings count as the opt-in.
ALLOW_PERMANENT_ENV = "AIXPLAIN_ALLOW_PERMANENT_UPLOADS"
_ALLOW_PERMANENT_SPELLINGS = (ALLOW_PERMANENT_ENV, "ALLOW_PERMANENT_ENV")

#: Method names that write to or destroy a resource.
_MUTATING_METHODS = ("delete", "update", "save", "deploy")

#: Calls that return resources the test does not own.
_LISTING_METHODS = ("list", "paginate")

#: The fixture every functional test registers its resources with.
TRACKER = "resource_tracker"

#: Methods that register a resource for cleanup. ``insert`` is how a test
#: places a resource at a chosen depth rather than on top, which is a deliberate
#: statement about teardown order, so the ordering detector below defers to it.
_REGISTERING_METHODS = ("append", "insert")

#: Calls that create or re-create a resource on the backend. Anything after the
#: first of these can fail, and a failure before registration leaks whatever the
#: first one created.
_CREATING_METHODS = ("save", "deploy", "update")


# ---------------------------------------------------------------------------
# Swallowed cleanup
# ---------------------------------------------------------------------------

#: Files that still end a cleanup `except` with a bare `pass`, and why they are
#: not fixed here. BUG-947's file list is apikey, file_asset, data_asset,
#: benchmark, sql_tool and test_rlm plus the four `resource_tracker` copies;
#: apikey, file_asset and data_asset are fixed, sql_tool and test_rlm create
#: nothing on a backend to leak (local SQLite files, already removed in a
#: `finally`, and an in-process RLM handle), benchmark is covered by
#: BENCHMARK_UNDELETABLE below, and every one of these files is a `v2` or
#: `agent` module outside that list. Declared rather than silently tolerated,
#: following PARKED_TARGETS
#: in test_ci_matrix_coverage.py: adopting the shared `resource_tracker` fixture
#: is a one-line change per test, so each entry is a small, separately reviewable
#: follow-up rather than 39 unrelated edits bolted onto the production-mutation
#: fix. Dropping an entry as it is fixed is the intended direction of travel; the
#: guard exists so the count cannot grow.
SWALLOWED_CLEANUP_BACKLOG = {
    "tests/functional/agent/agent_mcp_deploy_test.py": "3 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/team_agent/evolver_test.py": "2 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_agent.py": "2 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_agent_duplicate.py": "9 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_agent_llm_persistence.py": "1 site; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_session.py": "11 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_snake_case_e2e.py": "4 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_tool.py": "4 sites; adopt resource_tracker (BUG-947 follow-up)",
    "tests/functional/v2/test_trigger.py": "3 sites; adopt resource_tracker (BUG-947 follow-up)",
}


def _python_files(directory: Path) -> list:
    return sorted(path for path in directory.rglob("*.py") if "__pycache__" not in path.parts)


def _relative(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root))


def _swallowed_cleanup_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> cleanup `try` line numbers whose handler is a bare `pass`.

    Scoped to `try` blocks that actually clean something up, so an unrelated
    best-effort `pass` is not swept in with it. The construct this looks for is
    the exact one the four `resource_tracker` copies used, and the reason
    orphaned production assets accumulated invisibly.
    """
    offenders = {}
    for path in _python_files(functional_dir):
        lines = []
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Try):
                continue
            if not any(all(isinstance(stmt, ast.Pass) for stmt in handler.body) for handler in node.handlers):
                continue
            body = ast.dump(ast.Module(body=node.body, type_ignores=[]))
            if any(f"attr='{method}'" in body for method in _MUTATING_METHODS):
                lines.append(node.lineno)
        if lines:
            offenders[_relative(path, repo_root)] = sorted(lines)
    return offenders


def test_no_new_file_swallows_a_cleanup_failure():
    """`except Exception: pass` around a delete is what hid the leaks."""
    offenders = _swallowed_cleanup_offenders()
    unexpected = {file: lines for file, lines in offenders.items() if file not in SWALLOWED_CLEANUP_BACKLOG}
    assert not unexpected, (
        "cleanup failure swallowed by a bare `except ...: pass`, so an orphaned resource in the "
        f"target tenant leaves no trace (BUG-947): {unexpected}. Register the resource with the "
        "shared `resource_tracker` fixture instead, which reports what it could not delete."
    )


@pytest.mark.parametrize("file", sorted(SWALLOWED_CLEANUP_BACKLOG))
def test_swallowed_cleanup_backlog_is_not_stale(file):
    """A fixed file must leave the backlog, or the guard stops covering it."""
    offenders = _swallowed_cleanup_offenders()
    assert file in offenders, (
        f"{file} no longer swallows a cleanup failure; drop its SWALLOWED_CLEANUP_BACKLOG entry so "
        "the guard starts holding it to the rule."
    )


# ---------------------------------------------------------------------------
# Benchmark: on BUG-947's list, but there is nothing to register
# ---------------------------------------------------------------------------

#: BUG-947 asks for `resource_tracker` in `tests/functional/benchmark/`, and
#: `benchmark_functional_test.py` does create real benchmarks with no cleanup.
#: It cannot register them: neither `Benchmark` nor `BenchmarkFactory` exposes a
#: delete, so there is no call for a tracker entry to make, and adding one to the
#: SDK is out of scope for a test-hygiene fix on an unmaintained `v1` surface.
#: `benchmark` is also not a CI leg (see the matrix comment in
#: .github/workflows/main.yaml), so it leaks only when run by hand. The guard
#: below is what stops that reasoning from going stale: the day a delete lands,
#: this test fails and names the file to fix.
BENCHMARK_CREATING_TEST = "tests/functional/benchmark/benchmark_functional_test.py"


def test_benchmark_cleanup_is_still_unimplementable():
    """When Benchmark gains a delete, register the benchmark tests with the tracker."""
    from aixplain.factories import BenchmarkFactory
    from aixplain.modules.benchmark import Benchmark

    deletable = [
        f"{owner.__module__}.{owner.__name__}" for owner in (Benchmark, BenchmarkFactory) if hasattr(owner, "delete")
    ]
    assert not deletable, (
        f"{deletable} now exposes a delete, so {BENCHMARK_CREATING_TEST} can finally clean up the "
        "benchmarks it creates. Register them with the shared `resource_tracker` fixture and drop "
        "this guard (BUG-947)."
    )


# ---------------------------------------------------------------------------
# One tracker definition
# ---------------------------------------------------------------------------


def _is_fixture(node: ast.AST) -> bool:
    return any("fixture" in ast.dump(decorator) for decorator in getattr(node, "decorator_list", []))


def _resource_tracker_definitions(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> line numbers defining a `resource_tracker` fixture."""
    definitions = {}
    for path in _python_files(functional_dir):
        lines = [
            node.lineno
            for node in ast.walk(ast.parse(path.read_text()))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "resource_tracker"
            and _is_fixture(node)
        ]
        if lines:
            definitions[_relative(path, repo_root)] = lines
    return definitions


def test_resource_tracker_is_defined_exactly_once():
    """Four copies existed, two files defined it twice, and every copy swallowed.

    The second definition in `team_agent_functional_test.py` and
    `inspector_functional_test.py` silently shadowed the first, so "fix the
    fixture" meant editing six identical bodies -- which is how a copy gets
    missed.
    """
    definitions = _resource_tracker_definitions()

    assert sorted(definitions) == [TRACKER_CONFTEST], (
        f"`resource_tracker` must be defined only in {TRACKER_CONFTEST}; found it in "
        f"{sorted(definitions)}. A local copy shadows the shared fixture and loses its failure "
        "reporting (BUG-947)."
    )
    assert len(definitions[TRACKER_CONFTEST]) == 1, (
        f"{TRACKER_CONFTEST} defines `resource_tracker` more than once, at lines "
        f"{definitions[TRACKER_CONFTEST]}. The later definition silently shadows the earlier one."
    )


# ---------------------------------------------------------------------------
# Permanent uploads
# ---------------------------------------------------------------------------


def _permanent_upload_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> lines passing `is_temp=False` without the opt-in guard.

    Neither the v1 `FileFactory` nor the v2 `File` resource exposes a delete for
    a permanent upload, so such a test *cannot* clean up after itself; the only
    safe shapes are `is_temp=True` or a test skipped unless
    ``AIXPLAIN_ALLOW_PERMANENT_UPLOADS`` is set. The guard is the enclosing
    function's decorators mentioning that flag.
    """
    offenders = {}
    for path in _python_files(functional_dir):
        lines = []
        for function in ast.walk(ast.parse(path.read_text())):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = " ".join(ast.dump(decorator) for decorator in function.decorator_list)
            opted_in = any(spelling in decorators for spelling in _ALLOW_PERMANENT_SPELLINGS)
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                for keyword in node.keywords:
                    is_permanent = (
                        keyword.arg == "is_temp"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is False
                    )
                    if is_permanent and not opted_in:
                        lines.append(node.lineno)
        if lines:
            offenders[_relative(path, repo_root)] = sorted(set(lines))
    return offenders


def test_no_unguarded_permanent_upload():
    """`is_temp=False` left a permanent production S3 object behind per push."""
    offenders = _permanent_upload_offenders()
    assert not offenders, (
        f"`is_temp=False` uploads a file the SDK cannot delete, so it leaks permanently (BUG-947): "
        f"{offenders}. Use `is_temp=True`, or skip the test unless {ALLOW_PERMANENT_ENV} is set."
    )


# ---------------------------------------------------------------------------
# The generic API key name
# ---------------------------------------------------------------------------


def _generic_api_key_name_offenders(apikey_dir: Path = APIKEY_DIR, repo_root: Path = REPO_ROOT) -> list:
    """Files under *apikey_dir* containing the generic key name."""
    offenders = []
    for path in sorted(apikey_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if GENERIC_API_KEY_NAME in text:
            offenders.append(_relative(path, repo_root))
    return offenders


def test_the_generic_api_key_name_is_absent_from_the_apikey_directory():
    """Deleting by this name reached keys real users could have created."""
    offenders = _generic_api_key_name_offenders()
    assert not offenders, (
        f"{GENERIC_API_KEY_NAME!r} appears in {offenders}. A cleanup sweep matching this name deleted "
        "every production key a team member had plausibly given the same name (BUG-947). Use the "
        "per-session unique `TEST_API_KEY_NAME`, and delete by id, never by name."
    )


# ---------------------------------------------------------------------------
# List, then mutate
# ---------------------------------------------------------------------------


def _root_name(node: ast.AST):
    """The base Name of an expression like `x`, `x[0]`, or `x['results'][0]`."""
    while isinstance(node, ast.Subscript):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _is_listing_call(node: ast.AST) -> bool:
    """True for `Something.list(...)` / `Something.paginate(...)`, possibly indexed."""
    while isinstance(node, ast.Subscript):
        node = node.value
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _LISTING_METHODS


def _foreign_bindings(function: ast.AST) -> dict:
    """Map name -> the lines at which it starts, or stops, holding a foreign resource.

    Returns ``{name: [(line, is_foreign), ...]}``, sorted by line, so a mutation
    can be tested against whatever the name held *at that point*. Tracking the
    "stops" half matters: reusing a loop variable for a resource the test then
    creates itself (``for pipeline in ...:`` followed by
    ``pipeline = PipelineFactory.init(...)``) is legitimate, and flagging it
    would push contributors toward an allowlist rather than toward the fix.
    """
    events = {}

    def record(name, line, is_foreign):
        events.setdefault(name, []).append((line, is_foreign))
        events[name].sort()

    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    record(target.id, node.lineno, _is_listing_call(node.value))

    # Loops second, and in source order, so `for x in y:` can ask what `y` held
    # at that point rather than merely whether it was ever assigned -- otherwise
    # iterating an ordinary local list reads as iterating a listing result.
    # Source order also makes a nested loop see its enclosing one.
    loops = sorted(
        (node for node in ast.walk(function) if isinstance(node, (ast.For, ast.AsyncFor))),
        key=lambda node: node.lineno,
    )
    for node in loops:
        if not isinstance(node.target, ast.Name):
            continue
        iterates_foreign = _is_listing_call(node.iter) or _is_foreign_at(events, _root_name(node.iter), node.lineno)
        record(node.target.id, node.lineno, iterates_foreign)

    return events


def _is_foreign_at(bindings: dict, name, line: int) -> bool:
    """True if *name* held a foreign resource at *line*, per the latest binding."""
    foreign = False
    for bound_at, is_foreign in bindings.get(name, []):
        if bound_at > line:
            break
        foreign = is_foreign
    return foreign


def _list_then_mutate_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> lines that mutate a resource obtained from a listing call.

    A shape check, not a semantic one: within a single function it tracks names
    bound from a `list()`/`paginate()` call -- directly, indexed, or as a loop
    variable -- and flags two shapes, both of which the audited `test_05` used:
    a mutating method on the foreign resource (`api_key.delete()`), and handing
    it to a factory (`APIKeyFactory.update(api_key)`).

    A false positive is resolved by having the test create its own resource,
    which is the desired outcome anyway.
    """
    offenders = {}
    for path in _python_files(functional_dir):
        lines = []
        for function in ast.walk(ast.parse(path.read_text())):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            bindings = _foreign_bindings(function)
            if not bindings:
                continue
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in _MUTATING_METHODS:
                    continue
                targets = [_root_name(node.func.value)] + [_root_name(argument) for argument in node.args]
                if any(_is_foreign_at(bindings, target, node.lineno) for target in targets):
                    lines.append(node.lineno)
        if lines:
            offenders[_relative(path, repo_root)] = sorted(set(lines))
    return offenders


def test_no_functional_test_mutates_a_resource_it_did_not_create():
    """The headline defect: `test_05` rewrote a pre-existing key's rate limits.

    It iterated `APIKeyFactory.list()`, took the first key -- whatever real key
    that happened to be -- set its global and asset limits to `randint(0, 10000)`
    and never restored them. On `main` that changed live rate limits on a
    production key on every push, with no audit trail (BUG-947).
    """
    offenders = _list_then_mutate_offenders()
    assert not offenders, (
        f"a functional test writes to a resource it obtained from `list()`/`paginate()`, i.e. one it "
        f"did not create and does not own (BUG-947): {offenders}. Create the resource in the test, "
        "mutate that, and register it with `resource_tracker`."
    )


# ---------------------------------------------------------------------------
# Teardown order
# ---------------------------------------------------------------------------


def _owner_name(node: ast.AST):
    """The base Name of `x`, `x.y`, `x.y[0]` -- the object an expression hangs off."""
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _registration_lines(function: ast.AST) -> tuple:
    """Map name -> line it is first registered at, and the set placed explicitly.

    Returns ``(appended, positioned)``. ``appended`` is registration *order*,
    since `ResourceTracker.cleanup` deletes in reverse of it; ``positioned``
    holds names registered with ``insert``, whose place in the tracker cannot be
    read off the source line and which the caller therefore leaves alone.
    """
    appended, positioned = {}, set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if _owner_name(node.func) != TRACKER or node.func.attr not in _REGISTERING_METHODS:
            continue
        names = [argument.id for argument in node.args if isinstance(argument, ast.Name)]
        if node.func.attr == "insert":
            positioned.update(names)
        else:
            for name in names:
                appended.setdefault(name, node.lineno)
    return appended, positioned


def _dependency_edges(function: ast.AST) -> list:
    """Return ``(dependent, dependency)`` pairs visible in *function*.

    Two shapes, both of which appear in the suite: a resource built from another
    (``agent = AgentFactory.create(tools=[connection])``), and a resource a test
    later attaches to another (``team_agent.agents.append(new_agent)``). Only
    the second shape catches a dependency created *after* both resources exist,
    which is precisely the case the reviewer found.
    """
    edges = []
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            used = {inner.id for inner in ast.walk(node.value) if isinstance(inner, ast.Name)}
            for target in node.targets:
                if isinstance(target, ast.Name):
                    edges.extend((target.id, name) for name in used if name != target.id)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and isinstance(node.func.value, ast.Attribute)
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            owner = _owner_name(node.func.value)
            if owner and owner != node.args[0].id:
                edges.append((owner, node.args[0].id))
    return edges


def _teardown_order_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> lines registering a dependency after the resource that uses it.

    `ResourceTracker.cleanup` deletes newest-first, so a dependency has to be
    registered *before* its dependent to be deleted *after* it. Get it backwards
    and teardown deletes, say, the agent's connection while the agent still
    lists it -- and the backend refuses. Under the old swallowing fixture that
    was invisible; under BUG-947's strict teardown it fails the test on every
    run, so the ordering is now an invariant rather than a convention.
    """
    offenders = {}
    for path in _python_files(functional_dir):
        lines = []
        for function in ast.walk(ast.parse(path.read_text())):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            appended, positioned = _registration_lines(function)
            for dependent, dependency in _dependency_edges(function):
                if dependent in positioned or dependency in positioned:
                    continue
                if dependent not in appended or dependency not in appended:
                    continue
                if appended[dependency] > appended[dependent]:
                    lines.append(appended[dependency])
        if lines:
            offenders[_relative(path, repo_root)] = sorted(set(lines))
    return offenders


def test_no_dependency_is_registered_after_the_resource_that_uses_it():
    """Newest-first teardown means the dependency must be registered first."""
    offenders = _teardown_order_offenders()
    assert not offenders, (
        f"a resource is registered with `resource_tracker` after something that depends on it, so "
        f"teardown deletes it first and the backend refuses (BUG-947): {offenders}. Register the "
        "dependency before its dependent, or use `resource_tracker.insert(...)` to place it."
    )


def _late_registration_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """Map file -> lines creating on the backend before the resource is registered.

    A resource can only be registered once the call that creates it returns, so
    the *first* `save()`/`deploy()`/`update()` is allowed to precede the
    registration. Every later one is not: `pipeline.save()` had already created
    the pipeline, so a `pipeline.deploy()` that raised before
    `resource_tracker.append(pipeline)` leaked it with nothing tracking it.
    """
    offenders = {}
    for path in _python_files(functional_dir):
        lines = []
        for function in ast.walk(ast.parse(path.read_text())):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            appended, positioned = _registration_lines(function)
            creations = {}
            for node in ast.walk(function):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in _CREATING_METHODS:
                    continue
                owner = _owner_name(node.func)
                if owner is not None:
                    creations.setdefault(owner, []).append(node.lineno)
            for name, registered_at in appended.items():
                if name in positioned:
                    continue
                lines.extend(line for line in sorted(creations.get(name, []))[1:] if line < registered_at)
        if lines:
            offenders[_relative(path, repo_root)] = sorted(set(lines))
    return offenders


def test_a_resource_is_registered_before_the_step_that_can_leak_it():
    """`save()` creates the pipeline; a failing `deploy()` after it must not leak."""
    offenders = _late_registration_offenders()
    assert not offenders, (
        f"a tracked resource already existed on the backend and was mutated again before being "
        f"registered with `resource_tracker`, so a failure there leaks it (BUG-947): {offenders}. "
        "Register it on the line after the call that creates it."
    )


# ---------------------------------------------------------------------------
# The detectors themselves, against synthetic trees
# ---------------------------------------------------------------------------


def _tree(tmp_path: Path, source: str, name: str = "some_test.py") -> Path:
    directory = tmp_path / "functional"
    directory.mkdir(exist_ok=True)
    (directory / name).write_text(source)
    return directory


SWALLOWED = "def teardown(agent):\n    try:\n        agent.delete()\n    except Exception:\n        pass\n"
REPORTED = "def teardown(agent, log):\n    try:\n        agent.delete()\n    except Exception as e:\n        log(e)\n"
# A bare `pass` that guards no cleanup at all: out of scope, and flagging it
# would push contributors toward an allowlist rather than toward the fix.
UNRELATED_PASS = "def read(agent):\n    try:\n        agent.reload()\n    except Exception:\n        pass\n"


@pytest.mark.parametrize(
    ("source", "expected"),
    [(SWALLOWED, {"functional/some_test.py": [2]}), (REPORTED, {}), (UNRELATED_PASS, {})],
    ids=["swallowed-delete", "reported-delete", "unrelated-pass"],
)
def test_swallowed_cleanup_detector(tmp_path, source, expected):
    assert _swallowed_cleanup_offenders(_tree(tmp_path, source), tmp_path) == expected


LOCAL_TRACKER = "import pytest\n\n\n@pytest.fixture\ndef resource_tracker():\n    yield []\n"
UNRELATED_FIXTURE = "import pytest\n\n\n@pytest.fixture\ndef other_tracker():\n    yield []\n"
# A plain function of that name is not a fixture, so it shadows nothing.
PLAIN_FUNCTION = "def resource_tracker():\n    return []\n"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (LOCAL_TRACKER, {"functional/some_test.py": [5]}),
        (UNRELATED_FIXTURE, {}),
        (PLAIN_FUNCTION, {}),
    ],
    ids=["local-copy", "unrelated-fixture", "plain-function"],
)
def test_resource_tracker_definition_detector(tmp_path, source, expected):
    assert _resource_tracker_definitions(_tree(tmp_path, source), tmp_path) == expected


PERMANENT = "def test_upload():\n    FileFactory.create(path='x', is_temp=False)\n"
TEMPORARY = "def test_upload():\n    FileFactory.create(path='x', is_temp=True)\n"
PARAMETRISED = "def test_upload(is_temp):\n    FileFactory.create(path='x', is_temp=is_temp)\n"
OPTED_IN = (
    "import os\n"
    "import pytest\n\n\n"
    "@pytest.mark.skipif(not os.getenv('AIXPLAIN_ALLOW_PERMANENT_UPLOADS'), reason='leaks')\n"
    "def test_upload():\n"
    "    FileFactory.create(path='x', is_temp=False)\n"
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (PERMANENT, {"functional/some_test.py": [2]}),
        (TEMPORARY, {}),
        (PARAMETRISED, {}),
        (OPTED_IN, {}),
    ],
    ids=["permanent", "temporary", "parametrised", "opted-in"],
)
def test_permanent_upload_detector(tmp_path, source, expected):
    assert _permanent_upload_offenders(_tree(tmp_path, source), tmp_path) == expected


def test_generic_api_key_name_detector_reads_non_python_files(tmp_path):
    """The literal originally came from `apikey.json`, not from a `.py` file."""
    directory = tmp_path / "apikey"
    directory.mkdir()
    (directory / "fixture.json").write_text('{"name": "Test API Key"}')
    (directory / "clean.json").write_text('{"name": "TEST_API_KEY_FUNCTIONAL_abc"}')

    assert _generic_api_key_name_offenders(directory, tmp_path) == ["apikey/fixture.json"]


def test_generic_api_key_name_detector_tolerates_binary(tmp_path):
    directory = tmp_path / "apikey"
    directory.mkdir()
    (directory / "blob.bin").write_bytes(b"\xff\xfe\x00binary")

    assert _generic_api_key_name_offenders(directory, tmp_path) == []


# The audited defect, reduced to its shape.
LIST_THEN_UPDATE = (
    "def test_x(APIKeyFactory):\n"
    "    api_keys = APIKeyFactory.list()\n"
    "    for api_key in api_keys:\n"
    "        api_key.global_limits.token_per_day = 5\n"
    "        APIKeyFactory.update(api_key)\n"
    "        break\n"
)
LIST_THEN_DELETE = "def test_x(APIKeyFactory):\n    for api_key in APIKeyFactory.list():\n        api_key.delete()\n"
# `PipelineFactory.list()["results"][0]` -- "take the first one" without a loop.
LIST_INDEX_THEN_MUTATE = (
    "def test_x(PipelineFactory):\n    pipeline = PipelineFactory.list()['results'][0]\n    pipeline.save()\n"
)
LIST_READ_ONLY = (
    "def test_x(APIKeyFactory):\n"
    "    api_keys = APIKeyFactory.list()\n"
    "    for api_key in api_keys:\n"
    "        assert api_key.id\n"
    "        api_key.get_usage()\n"
)
# The fix: create the resource, then mutate that.
CREATE_THEN_UPDATE = (
    "def test_x(APIKeyFactory, resource_tracker):\n"
    "    api_key = APIKeyFactory.create(name='x')\n"
    "    resource_tracker.append(api_key)\n"
    "    assert api_key.id in {k.id for k in APIKeyFactory.list()}\n"
    "    APIKeyFactory.update(api_key)\n"
)
# An ordinary local list of resources the test created: iterating it is not
# iterating a listing result, and deleting from it is the correct behaviour.
LOCAL_LIST_THEN_DELETE = (
    "def test_x():\n"
    "    created = []\n"
    "    created.append(make_trigger())\n"
    "    for trigger in created:\n"
    "        trigger.delete()\n"
)
# A loop variable reused for a resource the test then creates itself.
LOOP_VARIABLE_REBOUND = (
    "def test_x(PipelineFactory, resource_tracker):\n"
    "    for pipeline in PipelineFactory.list()['results']:\n"
    "        assert pipeline.id\n"
    "    pipeline = PipelineFactory.init('mine')\n"
    "    pipeline.save()\n"
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (LIST_THEN_UPDATE, {"functional/some_test.py": [5]}),
        (LIST_THEN_DELETE, {"functional/some_test.py": [3]}),
        (LIST_INDEX_THEN_MUTATE, {"functional/some_test.py": [3]}),
        (LIST_READ_ONLY, {}),
        (CREATE_THEN_UPDATE, {}),
        (LOCAL_LIST_THEN_DELETE, {}),
        (LOOP_VARIABLE_REBOUND, {}),
    ],
    ids=[
        "list-then-update",
        "list-then-delete",
        "list-index-then-mutate",
        "list-read-only",
        "create-then-update",
        "local-list-then-delete",
        "loop-variable-rebound",
    ],
)
def test_list_then_mutate_detector(tmp_path, source, expected):
    assert _list_then_mutate_offenders(_tree(tmp_path, source), tmp_path) == expected


# The reviewed defects, reduced to their shapes.
DEPENDENCY_REGISTERED_LAST = (
    "def test_x(AgentFactory, resource_tracker):\n"
    "    tool = AgentFactory.create_custom_python_code_tool(code='x')\n"
    "    agent = AgentFactory.create(name='a', tools=[tool])\n"
    "    resource_tracker.append(agent)\n"
    "    resource_tracker.append(tool)\n"
)
DEPENDENCY_REGISTERED_FIRST = (
    "def test_x(AgentFactory, resource_tracker):\n"
    "    tool = AgentFactory.create_custom_python_code_tool(code='x')\n"
    "    resource_tracker.append(tool)\n"
    "    agent = AgentFactory.create(name='a', tools=[tool])\n"
    "    resource_tracker.append(agent)\n"
)
# The dependency is created after both resources exist, by mutating the team.
JOINED_AFTER_REGISTRATION = (
    "def test_x(AgentFactory, TeamAgentFactory, resource_tracker):\n"
    "    team_agent = TeamAgentFactory.create(name='t')\n"
    "    resource_tracker.append(team_agent)\n"
    "    new_agent = AgentFactory.create(name='a')\n"
    "    resource_tracker.append(new_agent)\n"
    "    team_agent.agents.append(new_agent)\n"
)
# The same test, with the agent placed below the team it joins.
JOINED_BUT_POSITIONED = (
    "def test_x(AgentFactory, TeamAgentFactory, resource_tracker):\n"
    "    team_agent = TeamAgentFactory.create(name='t')\n"
    "    position = len(resource_tracker)\n"
    "    resource_tracker.append(team_agent)\n"
    "    new_agent = AgentFactory.create(name='a')\n"
    "    resource_tracker.insert(position, new_agent)\n"
    "    team_agent.agents.append(new_agent)\n"
)
# Re-fetching a resource into its own name is not a dependency on itself.
REFETCHED_IN_PLACE = (
    "def test_x(TeamAgentFactory, resource_tracker):\n"
    "    team_agent = TeamAgentFactory.create(name='t')\n"
    "    resource_tracker.append(team_agent)\n"
    "    team_agent = TeamAgentFactory.get(team_agent.id)\n"
)
UNTRACKED_DEPENDENCY = (
    "def test_x(AgentFactory, resource_tracker):\n"
    "    tool = AgentFactory.create_model_tool(model='m')\n"
    "    agent = AgentFactory.create(name='a', tools=[tool])\n"
    "    resource_tracker.append(agent)\n"
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (DEPENDENCY_REGISTERED_LAST, {"functional/some_test.py": [5]}),
        (DEPENDENCY_REGISTERED_FIRST, {}),
        (JOINED_AFTER_REGISTRATION, {"functional/some_test.py": [5]}),
        (JOINED_BUT_POSITIONED, {}),
        (REFETCHED_IN_PLACE, {}),
        (UNTRACKED_DEPENDENCY, {}),
    ],
    ids=[
        "dependency-registered-last",
        "dependency-registered-first",
        "joined-after-registration",
        "joined-but-positioned",
        "refetched-in-place",
        "untracked-dependency",
    ],
)
def test_teardown_order_detector(tmp_path, source, expected):
    assert _teardown_order_offenders(_tree(tmp_path, source), tmp_path) == expected


# `save()` creates the pipeline, so a failing `deploy()` before registration
# leaks it -- the reviewed defect.
DEPLOY_BEFORE_REGISTRATION = (
    "def test_x(PipelineFactory, resource_tracker):\n"
    "    pipeline = PipelineFactory.init('p')\n"
    "    pipeline.save()\n"
    "    pipeline.deploy()\n"
    "    resource_tracker.append(pipeline)\n"
)
REGISTERED_BETWEEN_SAVE_AND_DEPLOY = (
    "def test_x(PipelineFactory, resource_tracker):\n"
    "    pipeline = PipelineFactory.init('p')\n"
    "    pipeline.save()\n"
    "    resource_tracker.append(pipeline)\n"
    "    pipeline.deploy()\n"
)
# The creating call has to run before the resource exists to be registered.
SAVE_BEFORE_REGISTRATION_ONLY = (
    "def test_x(PipelineFactory, resource_tracker):\n"
    "    pipeline = PipelineFactory.init('p')\n"
    "    pipeline.save()\n"
    "    resource_tracker.append(pipeline)\n"
)
DEPLOY_AFTER_REGISTRATION = (
    "def test_x(AgentFactory, resource_tracker):\n"
    "    agent = AgentFactory.create(name='a')\n"
    "    resource_tracker.append(agent)\n"
    "    agent.update()\n"
    "    agent.deploy()\n"
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (DEPLOY_BEFORE_REGISTRATION, {"functional/some_test.py": [4]}),
        (REGISTERED_BETWEEN_SAVE_AND_DEPLOY, {}),
        (SAVE_BEFORE_REGISTRATION_ONLY, {}),
        (DEPLOY_AFTER_REGISTRATION, {}),
    ],
    ids=[
        "deploy-before-registration",
        "registered-between-save-and-deploy",
        "save-before-registration-only",
        "deploy-after-registration",
    ],
)
def test_late_registration_detector(tmp_path, source, expected):
    assert _late_registration_offenders(_tree(tmp_path, source), tmp_path) == expected
