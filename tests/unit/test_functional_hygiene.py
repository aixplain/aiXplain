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
