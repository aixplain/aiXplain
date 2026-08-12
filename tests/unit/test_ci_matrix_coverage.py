"""Guard: the CI matrix and tests/functional/ agree (ENG-3544).

The matrix in `.github/workflows/main.yaml` is the only inventory of what CI
actually runs, and it drifted from the filesystem in both directions at once:

* the `agent`/`team_agent` legs collected ~50 tests, skipped every one via a
  directory-wide conftest hook, and reported green;
* an earlier matrix trim (04dea96e) deleted the `benchmark`,
  `pipeline_designer`, and `pipeline_create` leg names while leaving their test
  files, so those files ran under no leg at all.

This test asserts the mapping in both directions. It is static and
credential-free on purpose: it runs in the `unit-coverage` job and in
pre-commit (which runs `tests/unit` on every branch push), so an orphaned file
is caught at the moment the matrix is edited rather than at the next release.

The dynamic half of the guard -- a leg that collects fine but skips itself at
runtime -- lives in tests/ci_guards.py, because no static check can see it.
"""

import ast
from pathlib import Path

import pytest
import yaml

from tests.ci_guards import REQUIRE_EXECUTED_ENV, should_fail_for_no_executed_tests

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "main.yaml"
FUNCTIONAL_DIR = REPO_ROOT / "tests" / "functional"

#: Both naming conventions in use under tests/functional/.
TEST_FILE_PATTERNS = ("test_*.py", "*_test.py")

#: Directories with no test module, and why. An entry is a written statement
#: that the absence is intentional; without it, a directory whose tests were all
#: deleted is indistinguishable from a covered one.
DIRS_WITHOUT_TESTS = {
    "finetune": "tests removed in 1539df13; only __init__.py and fixture data remain (ENG-3544 open question: delete or restore)",
}


def _matrix() -> dict:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    return workflow["jobs"]["setup-and-test"]["strategy"]["matrix"]


def _include_targets() -> dict:
    """Map leg name -> path target, i.e. the first token of its `path` value.

    `path` is a command-line tail rather than a bare path -- the pipeline leg
    appends `--pipeline_version 2.0 --sdk_version v1 ...` -- but the target pytest
    is pointed at is always the first token.
    """
    return {entry["test-suite"]: entry["path"].split()[0] for entry in _matrix()["include"]}


def _running_leg_targets() -> dict:
    """The `include` entries that a job is actually spawned for.

    GitHub Actions expands the matrix from the `test-suite` list; an `include`
    entry whose name is absent from that list contributes nothing and runs
    nothing. Coverage is therefore computed from the intersection, so deleting a
    leg *name* orphans its files even while the `include` entry lingers -- which
    is exactly how 04dea96e went unnoticed.
    """
    include = _include_targets()
    return {name: include[name] for name in _matrix()["test-suite"] if name in include}


def _matching_files(directory: Path) -> set:
    """Every test file under *directory*, relative to the repo root."""
    found = set()
    for pattern in TEST_FILE_PATTERNS:
        found.update(path.relative_to(REPO_ROOT) for path in directory.rglob(pattern))
    return found


def _files_claimed_by(target: str) -> set:
    """The test files a leg pointed at *target* would execute."""
    path = REPO_ROOT / target
    if path.is_file():
        return {path.relative_to(REPO_ROOT)}
    if not path.is_dir():
        return set()
    return _matching_files(path)


def test_every_leg_path_exists():
    missing = {leg: target for leg, target in _include_targets().items() if not (REPO_ROOT / target).exists()}
    assert not missing, f"matrix legs point at paths that do not exist: {missing}"


def test_matrix_names_and_include_entries_agree():
    """A name with no `include` entry, or an entry with no name, both mean drift.

    An `include` entry whose `test-suite` is absent from the name list does not
    run at all -- that is how the orphaned legs disappeared without the YAML
    looking wrong.
    """
    names = set(_matrix()["test-suite"])
    targets = set(_include_targets())
    assert names == targets, (
        "every test-suite name needs an include entry and vice versa; "
        f"names without an entry: {sorted(names - targets)}; "
        f"entries without a name (these do not run): {sorted(targets - names)}"
    )


def test_every_functional_test_file_is_claimed_by_exactly_one_leg():
    claims = {}
    for leg, target in _running_leg_targets().items():
        for file in _files_claimed_by(target):
            claims.setdefault(file, []).append(leg)

    unclaimed = sorted(str(file) for file in _matching_files(FUNCTIONAL_DIR) - set(claims))
    assert not unclaimed, (
        f"functional test files executed by NO CI leg: {unclaimed}. Add a leg to "
        ".github/workflows/main.yaml (both the test-suite list and include), or delete the files."
    )

    duplicated = {str(file): legs for file, legs in claims.items() if len(legs) > 1}
    assert not duplicated, (
        f"functional test files executed by MORE THAN ONE CI leg: {duplicated}. "
        "Duplicate execution doubles backend cost and makes a flake look like two failures."
    )


def test_every_functional_directory_maps_to_a_leg():
    targets = list(_running_leg_targets().values())
    directories = sorted(p for p in FUNCTIONAL_DIR.iterdir() if p.is_dir() and p.name != "__pycache__")
    assert directories, f"no directories found under {FUNCTIONAL_DIR}; the audit would pass vacuously"

    for directory in directories:
        name = directory.name
        if not _matching_files(directory):
            assert name in DIRS_WITHOUT_TESTS, (
                f"tests/functional/{name} contains no test module. Delete the directory, add "
                "tests, or record the reason in DIRS_WITHOUT_TESTS in this file."
            )
            continue
        prefix = f"tests/functional/{name}"
        assert any(target == prefix or target.startswith(f"{prefix}/") for target in targets), (
            f"tests/functional/{name} is not executed by any named CI leg"
        )


def test_allowlisted_directories_still_exist_and_are_still_empty():
    """Keeps DIRS_WITHOUT_TESTS from outliving the situation it describes."""
    for name in DIRS_WITHOUT_TESTS:
        directory = FUNCTIONAL_DIR / name
        assert directory.is_dir(), f"tests/functional/{name} no longer exists; drop it from DIRS_WITHOUT_TESTS"
        assert not _matching_files(directory), (
            f"tests/functional/{name} has test files again; drop it from DIRS_WITHOUT_TESTS and give it a CI leg"
        )


#: Anything that makes a skip conditional: an env read, a marker lookup, or a
#: CLI option. A directory-wide skip is only legitimate when it consults one.
_GUARD_CALLS = ("getenv", "environ", "get_closest_marker", "getoption", "getvalue")


def _skips_unconditionally(node: ast.AST) -> bool:
    """True if *node*'s body reaches a skip without consulting anything.

    A deliberate shape check rather than a semantic one: any legitimate
    directory-wide skip reads the environment, a marker, or an option, so
    requiring one of those keeps false positives unlikely and easy to resolve.
    """
    body = ast.dump(node)
    skips = "'skip'" in body or '"skip"' in body
    return skips and not any(call in body for call in _GUARD_CALLS)


def _is_autouse_fixture(node: ast.AST) -> bool:
    return any("autouse" in ast.dump(decorator) for decorator in getattr(node, "decorator_list", []))


#: conftest hooks that run for every item in the directory and can skip it.
#: `pytest_runtest_setup` matters as much as the hook that caused ENG-3544 --
#: `pytest.skip()` there is the shortest way to silence a whole directory, and a
#: detector that only knew the original construct would wave it straight through.
_SKIP_CAPABLE_HOOKS = (
    "pytest_collection_modifyitems",
    "pytest_runtest_setup",
    "pytest_runtest_call",
)


def _blanket_skip_offenders(functional_dir: Path = FUNCTIONAL_DIR, repo_root: Path = REPO_ROOT) -> dict:
    """conftest files that skip their whole directory unconditionally.

    Three constructs can do it, and all are checked, because closing only the
    first would leave the door open in the very idiom this ticket introduced:

    * `pytest_collection_modifyitems` adding a skip marker to every item -- the
      original defect;
    * any other per-item conftest hook that skips (`_SKIP_CAPABLE_HOOKS`) --
      `pytest_runtest_setup` reaches the same end in one line;
    * an autouse fixture calling `pytest.skip()` -- the shape of the *fix*, one
      edit away from being unconditional again.

    The directories are parameters so the detector can be tested against a
    throwaway tree -- see the test below.
    """
    offenders = {}
    for conftest in sorted(functional_dir.rglob("conftest.py")):
        tree = ast.parse(conftest.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name in _SKIP_CAPABLE_HOOKS:
                construct = node.name
            elif _is_autouse_fixture(node):
                construct = f"autouse fixture {node.name}()"
            else:
                continue
            if _skips_unconditionally(node):
                offenders[str(conftest.relative_to(repo_root))] = construct
    return offenders


def test_no_functional_conftest_blanket_skips_its_directory():
    """The ENG-3544 defect itself: an unconditional directory-wide skip."""
    offenders = _blanket_skip_offenders()
    assert not offenders, (
        "conftest applies an unconditional skip to every item in its directory, which makes the "
        f"leg green while running nothing (ENG-3544): {offenders}. Guard it on the API key (see "
        "tests/functional/v2/conftest.py) or skip individual tests with a ticketed reason."
    )


OFFENDER = "tests/functional/agent/conftest.py"

# The original defect: every collected item gets a skip marker, no questions asked.
BLANKET_HOOK = (
    "import pytest\n"
    "def pytest_collection_modifyitems(config, items):\n"
    "    for item in items:\n"
    "        item.add_marker(pytest.mark.skip(reason='skipped'))\n"
)

# The same hook, but conditional on a credential -- legitimate.
GUARDED_HOOK = (
    "import os\n"
    "import pytest\n"
    "def pytest_collection_modifyitems(config, items):\n"
    "    if os.getenv('TEAM_API_KEY'):\n"
    "        return\n"
    "    for item in items:\n"
    "        item.add_marker(pytest.mark.skip(reason='no credentials'))\n"
)

# The fix's own idiom, one edit away from being a blanket skip again.
BLANKET_FIXTURE = (
    "import pytest\n"
    "@pytest.fixture(autouse=True)\n"
    "def _require_api_key():\n"
    "    pytest.skip('agent functional tests skipped')\n"
)

# The fix as written: the same fixture, conditional on a credential.
GUARDED_FIXTURE = (
    "import os\n"
    "import pytest\n"
    "@pytest.fixture(autouse=True)\n"
    "def _require_api_key():\n"
    "    if not os.getenv('TEAM_API_KEY'):\n"
    "        pytest.skip('no credentials')\n"
)

# The one-line route to the same outcome, via a different per-item hook.
BLANKET_SETUP_HOOK = "import pytest\ndef pytest_runtest_setup(item):\n    pytest.skip('not ready')\n"

# The same hook, conditional -- legitimate.
GUARDED_SETUP_HOOK = (
    "import os\n"
    "import pytest\n"
    "def pytest_runtest_setup(item):\n"
    "    if not os.getenv('TEAM_API_KEY'):\n"
    "        pytest.skip('no credentials')\n"
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (BLANKET_HOOK, {OFFENDER: "pytest_collection_modifyitems"}),
        (GUARDED_HOOK, {}),
        (BLANKET_FIXTURE, {OFFENDER: "autouse fixture _require_api_key()"}),
        (GUARDED_FIXTURE, {}),
        (BLANKET_SETUP_HOOK, {OFFENDER: "pytest_runtest_setup"}),
        (GUARDED_SETUP_HOOK, {}),
    ],
    ids=[
        "blanket-hook",
        "guarded-hook",
        "blanket-autouse-fixture",
        "guarded-autouse-fixture",
        "blanket-runtest-setup-hook",
        "guarded-runtest-setup-hook",
    ],
)
def test_blanket_skip_detector_distinguishes_guarded_from_unconditional(tmp_path, source, expected):
    """The detector must actually detect; otherwise the guard above is decorative."""
    agent_dir = tmp_path / "tests" / "functional" / "agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "conftest.py").write_text(source)

    assert _blanket_skip_offenders(agent_dir.parent, tmp_path) == expected


@pytest.mark.parametrize("directory", ["agent", "team_agent"])
def test_the_real_conftests_are_the_guarded_shape(directory):
    """The two files this ticket rewrote still skip only on a missing credential.

    Matched against the parsed tree, not the file text, so the comments that
    explain the defect are not mistaken for the defect.
    """
    conftest = FUNCTIONAL_DIR / directory / "conftest.py"
    functions = [node for node in ast.walk(ast.parse(conftest.read_text())) if isinstance(node, ast.FunctionDef)]

    assert not [f for f in functions if f.name == "pytest_collection_modifyitems"], (
        f"tests/functional/{directory}/conftest.py reintroduced the collection hook that caused "
        "ENG-3544; use the credential-guarded autouse fixture instead."
    )

    guards = [f for f in functions if _is_autouse_fixture(f) and "getenv" in ast.dump(f)]
    assert guards, (
        f"tests/functional/{directory}/conftest.py has no autouse fixture guarding its skip on an "
        "API key; without one the suite either runs with no credential or skips unconditionally."
    )


def test_workflow_enables_the_execution_guard():
    """CI must actually opt in to the runtime half of this ticket.

    `AIXPLAIN_REQUIRE_EXECUTED_TESTS` is opt-in so that laptops and `pytest -k`
    runs behave normally, which means one deleted line in `env:` silently
    restores the exact failure mode ENG-3544 fixed -- and every other test in
    this file would still pass, because the static mapping would be untouched.
    A guard that can be switched off without anything noticing is the bug, not
    the fix.

    The literal value is fed through the real predicate rather than compared to
    a hard-coded list, so a value the workflow sets but the guard does not
    honour (`"yes please"`, `"enabled"`) fails here instead of in six months.
    """
    workflow = yaml.safe_load(WORKFLOW.read_text())
    value = workflow.get("env", {}).get(REQUIRE_EXECUTED_ENV)

    assert value is not None, (
        f"{REQUIRE_EXECUTED_ENV} is missing from the workflow-level `env:` block in "
        f"{WORKFLOW.name}. Without it a leg that skips every test reports green again (ENG-3544)."
    )
    assert should_fail_for_no_executed_tests(0, 0, env={REQUIRE_EXECUTED_ENV: str(value)}), (
        f"{REQUIRE_EXECUTED_ENV} is set to {value!r}, which tests/ci_guards.py does not read as "
        "truthy, so the execution guard is off in CI while looking enabled."
    )


def test_every_leg_declares_a_timeout():
    """`timeout-minutes: ${{ matrix.timeout }}` resolves to empty without one.

    A leg missing `timeout` does not fail loudly -- it loses its per-leg timeout
    and falls back to the job default, so a hung functional suite burns the full
    allowance before anyone notices.
    """
    missing = [entry["test-suite"] for entry in _matrix()["include"] if "timeout" not in entry]
    assert not missing, f"matrix include entries with no `timeout`: {missing}"
