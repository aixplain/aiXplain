"""Guard: no plaintext credentials in the tree, and the scanner stays wired up (ENG-3686).

Live 64-hex platform keys sat in tracked scratch files for months, as a literal
``api_key=`` argument and as a ``TEAM_API_KEY`` assignment whose saved notebook
output echoed the key back many times over. Neither file ran under pytest: both
were outside ``testpaths``, so no suite ever looked at them. They were removed
in ENG-3686; docs/ci/secret-scanning.md says what remains to be done.

Gitleaks now runs on the staged diff via .pre-commit-config.yaml and over the
whole tree in .github/workflows/pre-commit.yaml. That is the real scanner; this
module is the part of it that survives having no network and no Go toolchain,
and it fails in the credential-free ``unit-coverage`` job:

* :func:`test_no_plaintext_key_literals` re-states the specific defect, so a key
  pasted into a file nobody runs is caught by the ordinary unit suite.
* The wiring tests fail if someone drops or disables the hook, the CI step or
  the config -- a scanner that has been quietly unhooked reports the same "no
  leaks found" as a clean tree.

The detectors take their root as a parameter so they can be pointed at a
synthetic tree and tested, following ``_blanket_skip_offenders`` in
tests/unit/test_ci_matrix_coverage.py. A guard nobody tested is decorative.
"""

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:  # `tomllib` is 3.11+; CI runs 3.9. See the `test` extra in pyproject.toml.
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
PRE_COMMIT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pre-commit.yaml"
GITLEAKS_CONFIG = REPO_ROOT / ".gitleaks.toml"

GITLEAKS_REPO = "https://github.com/gitleaks/gitleaks"

#: The repo-specific rules in .gitleaks.toml. The curated defaults miss every
#: shape in :data:`_LEAKED_SHAPES`.
CUSTOM_RULE_IDS = ("aixplain-platform-key", "aixplain-client-positional-key")

#: Obviously fake, but shaped like a real key so the detectors have to work for it.
#: .gitleaks.toml allowlists exactly this value; never put a real key here.
_FAKE_API_KEY = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

#: A sha256 digest (the artifact checksum in tests/unit/v2/test_agent_artifacts.py): 64 hex, but not a key.
_SHA256_DIGEST = "19b413378251d828b0c0347ebcfb50343f3aff8ebd54ee5d0fe439f974dfecb3"

#: The ways a platform key has been committed to this repository, as code.
_LEAKED_SHAPES = (
    f'os.environ["TEAM_API_KEY"] = "{_FAKE_API_KEY}"',
    f'headers = {{"Authorization": "Token {_FAKE_API_KEY}"}}',
    f'aix = Aixplain("{_FAKE_API_KEY}")',
    f'client = Aixplain(api_key="{_FAKE_API_KEY}")',
    # Per-environment names: the text between the name and the key holds hex letters.
    f'TEAM_API_KEY_PROD="{_FAKE_API_KEY}"',
    f"AIXPLAIN_API_KEY_DEV={_FAKE_API_KEY}",
    f'SECRET_KEY = "{_FAKE_API_KEY}"',
    f"api_key_test: {_FAKE_API_KEY}",
    f'headers = {{"x-aixplain-key": "{_FAKE_API_KEY}"}}',
)

#: A 64-hex platform API key, as a standalone token. Both leaked keys had this
#: shape, and so does every key the platform issues.
_KEY_LITERAL = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")

#: A 64-hex string is only a finding when something on the line says it is a
#: credential. Unqualified 64-hex strings are overwhelmingly sha256 digests --
#: the lockfile hashes in uv.lock, the artifact checksums in
#: tests/unit/v2/test_agent_artifacts.py -- and banning those outright would make
#: this guard unrunnable rather than strict.
_CREDENTIAL_CONTEXT = re.compile(r"api[_-]?key|team[_-]?key|access[_-]?key|token|secret|password", re.IGNORECASE)

#: Directories with no hand-written source to protect, matched against the path
#: relative to the scanned root so a checkout that happens to live under, say,
#: ``~/build/`` is still scanned. Git tracks none of these; they matter only on
#: the synthetic-tree path below.
_SKIP_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "build", "dist"})

#: Generated output, skipped by leading path parts. ``docs/api-reference`` is
#: rendered from docstrings by pydoc-markdown (pydoc-markdown.yml and
#: post_process_docs.py). The rest of ``docs/`` is hand-written and is scanned.
_SKIP_PREFIXES = frozenset({("docs", "api-reference")})

#: ``uv.lock`` is thousands of sha256 digests; this module plants fake keys.
_SKIP_FILES = frozenset({"uv.lock", "test_secret_scanning.py"})

#: Extensions worth reading. Binary assets cannot carry a reviewable literal.
_TEXT_SUFFIXES = frozenset(
    {".py", ".ipynb", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".md", ".txt", ".sh", ".example"}
)


def _git(*args, **kwargs):
    """Run git with every ``GIT_*`` variable stripped from the environment.

    The ``pytest-check`` hook runs this module from inside ``git commit``, which
    exports ``GIT_INDEX_FILE`` (and ``GIT_DIR`` in a linked worktree) to hooks.
    Inherited, they point the throwaway repositories below at the developer's
    real one: ``git add`` stages into its index, and ``git init`` from a worktree
    rewrites its config to ``core.bare = true``.
    """
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.run(["git", *args], env=env, check=True, **kwargs)


def _tracked_files(root: Path):
    """Return ``root``'s git-tracked files, or ``None`` when ``root`` is not a checkout.

    Scope is deliberately what git tracks. This guard is about a credential
    reaching history, and the working tree is full of ignored files that hold
    real keys by design: ``.cache/model.json``, which the SDK writes an
    ``api_key`` into on every run, and the ``.env`` that tests/conftest.py loads
    via ``load_dotenv``. Walking those fails the unit suite on any developer
    machine that has ever run the SDK, over files git will never accept.

    ``None`` keeps the synthetic ``tmp_path`` trees below on a plain filesystem
    walk; the check is on ``root`` itself so a temporary directory can never
    inherit an enclosing repository's index.
    """
    if not (root / ".git").exists():
        return None
    try:
        listing = _git("-C", str(root), "ls-files", "-z", capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover - needs a broken checkout
        pytest.fail(f"cannot list tracked files under {root}: {exc}")
    return [root / name for name in listing.split("\0") if name]


def _is_scannable(path: Path) -> bool:
    """Whether ``path`` is a text file worth reading.

    ``Path(".env").suffix`` is ``""``, so ``.env`` and its ``.env.local``-style
    variants are matched by name.
    """
    return path.suffix in _TEXT_SUFFIXES or path.name == ".env" or path.name.startswith(".env.")


def _key_literal_offenders(root: Path):
    """Return ``(relative path, line number)`` for each credential-shaped literal under ``root``."""
    tracked = _tracked_files(root)
    candidates = root.rglob("*") if tracked is None else tracked
    offenders = []
    for path in sorted(candidates):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if any(part in _SKIP_DIRS for part in parts):
            continue
        if any(parts[: len(prefix)] == prefix for prefix in _SKIP_PREFIXES):
            continue
        if path.name in _SKIP_FILES or not _is_scannable(path):
            continue
        try:
            # A stray Latin-1 byte must not make the whole file invisible.
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _KEY_LITERAL.search(line) and _CREDENTIAL_CONTEXT.search(line):
                offenders.append((Path(*parts).as_posix(), lineno))
    return offenders


def test_no_plaintext_key_literals():
    """No tracked file pairs a 64-hex literal with a credential-ish name."""
    offenders = _key_literal_offenders(REPO_ROOT)
    assert offenders == [], (
        "64-hex literal on a line naming a credential:\n"
        + "\n".join(f"  {path}:{lineno}" for path, lineno in offenders)
        + "\nIf this is a genuinely fake fixture, give it a shape a real key cannot have "
        "(shorter, or non-hex) rather than allowlisting it."
    )


def test_detector_catches_a_planted_key(tmp_path):
    """The detector is pointed at a synthetic tree, so a silent no-op is visible."""
    (tmp_path / "scratch.py").write_text(f'api_key = "{_FAKE_API_KEY}"\n', encoding="utf-8")
    assert _key_literal_offenders(tmp_path) == [("scratch.py", 1)]


@pytest.mark.parametrize("parent", ["docs", "build", "dist", "venv"])
def test_detector_scans_a_checkout_under_a_skipped_directory_name(tmp_path, parent):
    """Skip rules apply inside the scanned tree, not to the directories above it."""
    root = tmp_path / parent / "aiXplain"
    root.mkdir(parents=True)
    (root / "scratch.py").write_text(f'api_key = "{_FAKE_API_KEY}"\n', encoding="utf-8")
    assert _key_literal_offenders(root) == [("scratch.py", 1)]


def test_detector_skips_only_the_generated_docs(tmp_path):
    """``docs/api-reference`` is generated; the rest of ``docs/`` is hand-written and scanned."""
    for relative in ("docs/api-reference/python/client.md", "docs/ci/notes.md"):
        (tmp_path / relative).parent.mkdir(parents=True)
        (tmp_path / relative).write_text(f"TEAM_API_KEY={_FAKE_API_KEY}\n", encoding="utf-8")
    assert _key_literal_offenders(tmp_path) == [("docs/ci/notes.md", 1)]


@pytest.mark.parametrize("name", [".env", ".env.local", "settings.env.example"])
def test_detector_reads_env_files(tmp_path, name):
    """``.env`` has no suffix as far as :mod:`pathlib` is concerned, so it is matched by name."""
    (tmp_path / name).write_text(f"TEAM_API_KEY={_FAKE_API_KEY}\n", encoding="utf-8")
    assert _key_literal_offenders(tmp_path) == [(name, 1)]


def test_detector_reads_a_file_that_is_not_valid_utf8(tmp_path):
    """One undecodable byte used to make the detector skip the file entirely."""
    (tmp_path / "notes.txt").write_bytes(b"caf\xe9\n" + f'api_key = "{_FAKE_API_KEY}"\n'.encode("ascii"))
    assert _key_literal_offenders(tmp_path) == [("notes.txt", 2)]


def test_detector_ignores_a_bare_digest(tmp_path):
    """A sha256 with no credential word on the line is not a finding."""
    (tmp_path / "checksums.json").write_text(
        f'{{"sha256": "{_SHA256_DIGEST}"}}\n',
        encoding="utf-8",
    )
    assert _key_literal_offenders(tmp_path) == []


def _assert_untracked_key_is_ignored(root: Path):
    """Plant a key in an ignored file under a fresh repository at ``root``, then track the same content."""
    _git("init", "-q", str(root))
    (root / ".gitignore").write_text(".cache/\n", encoding="utf-8")
    (root / ".cache").mkdir()
    planted = f'{{"api_key": "{_FAKE_API_KEY}"}}\n'
    (root / ".cache" / "model.json").write_text(planted, encoding="utf-8")
    _git("-C", str(root), "add", ".gitignore")

    assert _key_literal_offenders(root) == []

    # ...and tracking that same content is still a finding, so the scope
    # narrowing above did not simply turn the detector off.
    (root / "scratch.py").write_text(f"api_key = {planted!r}\n", encoding="utf-8")
    _git("-C", str(root), "add", "scratch.py")
    assert _key_literal_offenders(root) == [("scratch.py", 1)]


def test_detector_ignores_an_untracked_key(tmp_path):
    """An ignored file holding a key is out of scope: git will never accept it.

    This is the ``.cache/model.json`` case. The SDK writes a real ``api_key``
    there on every run and .gitignore excludes it, so a tree-wide walk reported
    a leak that no commit could ever contain.
    """
    _assert_untracked_key_is_ignored(tmp_path)


def test_git_calls_ignore_the_commit_hook_environment(tmp_path, monkeypatch):
    """Running from the ``pytest-check`` hook must not touch the repository being committed to.

    ``bystander`` stands in for the developer's checkout: ``GIT_DIR`` and
    ``GIT_INDEX_FILE`` point at it exactly as ``git commit`` would point them
    for a hook running in a linked worktree.
    """
    bystander = tmp_path / "bystander"
    _git("init", "-q", str(bystander))
    (bystander / "staged.txt").write_text("staged\n", encoding="utf-8")
    _git("-C", str(bystander), "add", "staged.txt")
    git_dir = bystander / ".git"
    before = {name: (git_dir / name).read_bytes() for name in ("index", "config")}

    monkeypatch.setenv("GIT_DIR", str(git_dir))
    monkeypatch.setenv("GIT_INDEX_FILE", str(git_dir / "index"))
    work = tmp_path / "work"
    work.mkdir()
    _assert_untracked_key_is_ignored(work)

    after = {name: (git_dir / name).read_bytes() for name in ("index", "config")}
    assert after == before, "a git call in this module inherited GIT_* and wrote to the enclosing repository"


def _gitleaks_hook():
    """Return the gitleaks repo entry and its hook from .pre-commit-config.yaml."""
    config = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        if repo.get("repo") == GITLEAKS_REPO:
            hooks = [hook for hook in repo["hooks"] if hook["id"] == "gitleaks"]
            assert hooks, "gitleaks repo is present but its hook is not enabled"
            return repo, hooks[0]
    pytest.fail(f"no {GITLEAKS_REPO} hook in .pre-commit-config.yaml; secrets would reach history unscanned")


def test_gitleaks_hook_is_configured():
    """pre-commit scans the staged diff, the last point a secret can be kept out of history."""
    repo, hook = _gitleaks_hook()
    assert repo["rev"].startswith("v"), "pin the hook to a tag, not a moving ref"
    # `stages: [manual]` keeps the hook listed but never runs it on commit.
    assert "stages" not in hook, f"the gitleaks hook must run at the default commit stage, not {hook['stages']!r}"


def _gitleaks_config():
    return tomllib.loads(GITLEAKS_CONFIG.read_text(encoding="utf-8"))


def test_gitleaks_config_extends_default_rules():
    """.gitleaks.toml must add to the curated rules, not replace them."""
    assert _gitleaks_config().get("extend", {}).get("useDefault") is True, (
        ".gitleaks.toml must keep `[extend] useDefault = true`: without it only the repo's own rules "
        "remain, and gitleaks reports the deleted leak files themselves as clean."
    )


def _custom_rules():
    rules = {rule["id"]: rule for rule in _gitleaks_config().get("rules", [])}
    missing = [rule_id for rule_id in CUSTOM_RULE_IDS if rule_id not in rules]
    assert not missing, f".gitleaks.toml lost {missing}; the default rules miss this repo's key shapes"
    return [rules[rule_id] for rule_id in CUSTOM_RULE_IDS]


@pytest.mark.parametrize("line", _LEAKED_SHAPES)
def test_custom_rules_catch_the_leaked_shapes(line):
    """Each shape this repo leaked is caught by a repo rule, with the key as the reported secret.

    The rules are RE2, but these patterns use nothing Python's ``re`` reads
    differently. Gitleaks only applies a rule when one of its keywords occurs
    in the text, so that is checked too.
    """
    caught = []
    for rule in _custom_rules():
        match = re.search(rule["regex"], line)
        if match and any(keyword in line.lower() for keyword in rule["keywords"]):
            caught.append(match.group(rule.get("secretGroup", 0)))
    assert _FAKE_API_KEY in caught, f"no rule in .gitleaks.toml reports the key in: {line}"


def test_custom_rules_ignore_a_bare_digest():
    """A checksum with no credential name nearby is not a key."""
    line = f'"sha256": "{_SHA256_DIGEST}",'
    assert not [rule["id"] for rule in _custom_rules() if re.search(rule["regex"], line)]


def _scan_step():
    """Return the pre-commit job and its full-tree gitleaks step."""
    workflow = yaml.safe_load(PRE_COMMIT_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["pre-commit"]
    scan_steps = [step for step in job["steps"] if "gitleaks" in str(step.get("run", ""))]
    assert scan_steps, "no full-tree gitleaks step in .github/workflows/pre-commit.yaml"
    return job, scan_steps[0]


def _logical_lines(script: str):
    """Return the non-comment lines of a ``run:`` script, with backslash continuations joined."""
    lines = (line.strip() for line in script.replace("\\\n", " ").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def _commands(script: str):
    """Tokenise each line of a ``run:`` script with :mod:`shlex`, dropping trailing comments."""
    return [tokens for tokens in (shlex.split(line, comments=True) for line in _logical_lines(script)) if tokens]


def test_ci_scans_the_whole_tree_at_the_pinned_version():
    """The staged-diff hook is a no-op under ``--all-files``; CI scans the tree itself.

    The CI step downloads a pinned release rather than reusing the hook's binary,
    so the two versions can drift apart silently. Assert they match.
    """
    _, scan = _scan_step()
    invocations = [tokens for tokens in _commands(scan["run"]) if tokens[0].endswith("/gitleaks")]
    assert len(invocations) == 1, f"expected one gitleaks invocation in the CI scan step, found {invocations}"
    tokens = invocations[0]
    assert tokens[1] == "dir", "the CI scan must use `gitleaks dir`: a commit range is empty on a first push"
    assert ".gitleaks.toml" in tokens and tokens[tokens.index(".gitleaks.toml") - 1] == "--config", (
        "the CI scan must use the repo's rules and allowlists via `--config .gitleaks.toml`"
    )
    assert "--redact" in tokens, "the repository is public; a finding must not print the secret into the CI log"

    ci_version = scan["env"]["GITLEAKS_VERSION"]
    hook_rev = _gitleaks_hook()[0]["rev"]
    assert f"v{ci_version}" == hook_rev, (
        f"CI pins gitleaks {ci_version} but .pre-commit-config.yaml pins {hook_rev}; "
        "a rule fixed in one version but not the other makes the two scans disagree."
    )


def test_ci_scan_failure_fails_the_job():
    """A finding has to fail the job; a scan whose result is ignored is the same as no scan."""
    job, scan = _scan_step()
    for where, mapping in (("job", job), ("scan step", scan)):
        assert "if" not in mapping, f"the {where} must not be conditional: `if: {mapping['if']}`"
        assert "continue-on-error" not in mapping, f"the {where} must not set `continue-on-error`"

    commands = _commands(scan["run"])
    assert ["set", "-euo", "pipefail"] in commands, "the scan script must stop on the first failing command"
    script = "\n".join(shlex.join(tokens) for tokens in commands)
    assert "||" not in script, "no `|| ...` fallback in the scan step: it swallows gitleaks' non-zero exit"
    assert not [token for tokens in commands for token in tokens if token.startswith("--exit-code")], (
        "do not override gitleaks' exit code; `--exit-code 0` reports leaks and passes"
    )


def test_ci_verifies_the_gitleaks_download():
    """The release tarball's sha256 is checked before anything is extracted from it."""
    _, scan = _scan_step()
    assert re.fullmatch(r"[0-9a-f]{64}", scan["env"].get("GITLEAKS_SHA256", "")), (
        "pin GITLEAKS_SHA256 to the linux_x64 line of the release's checksums.txt"
    )
    lines = _logical_lines(scan["run"])
    curl = next(tokens for tokens in _commands(scan["run"]) if tokens[0] == "curl")
    expected = f'echo "${{GITLEAKS_SHA256}}  {curl[curl.index("-o") + 1]}" | sha256sum -c -'
    assert expected in lines, f"verify the download with `{expected}`"
    extract = [i for i, line in enumerate(lines) if line.startswith("tar ")]
    assert extract and lines.index(expected) < extract[0], "verify the tarball's checksum before extracting it"
