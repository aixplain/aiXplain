#!/usr/bin/env python3
"""
refresh_skill.py — keep the aixplain-builder skill in sync with the upstream SDK + docs.

Pipeline (deterministic parts always run; the rewrite step needs an LLM backend):

  1. Pull the latest aiXplain documentation (git) and diff it against the SHA recorded
     in the skill's manifest.json — reports which doc files changed and which skill
     reference file each maps to.
  2. Upgrade + introspect the installed `aixplain` SDK and diff its public API against
     the baseline snapshot — catches renamed/removed methods, params, enums, IDs.
  3. Validate every code snippet in the skill (imports + enum references) against the
     installed SDK — catches snippets that the SDK has broken.
  4. (apply mode) Hand the doc diff + current skill files to Claude to patch only the
     changed reference files, re-translate the changed files to Arabic, re-package the
     .skill, and update manifest.json. Gated behind a review/diff unless --yes.

USAGE
  python3 tooling/refresh_skill.py check          # report only, never writes (default)
  python3 tooling/refresh_skill.py snapshot-sdk   # (re)write the SDK baseline from the installed SDK
  python3 tooling/refresh_skill.py apply [--yes]  # check + LLM patch + translate + package + bump manifest

KEY FLAGS
  --skill PATH        skill root (default: parent of this tooling/ dir)
  --docs-repo URL     docs git repo (default: aixplain/sdk-documentation)
  --work-dir PATH     scratch dir for the docs clone (default: <skill>/tooling/.work)
  --no-translate      skip Arabic re-translation in apply mode
  --no-package        skip re-packaging the .skill in apply mode
  --yes               apply changes without the interactive confirmation

LLM BACKEND (apply mode) is auto-detected, in order:
  1. `claude` CLI on PATH        -> runs `claude -p`
  2. ANTHROPIC_API_KEY + `anthropic` package installed
  3. none -> apply falls back to writing a detailed report; you (or a Claude session) edit by hand.

The SDK introspection + snippet validation need only `pip install aixplain` (no API key, no credits).
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, shutil, tempfile, inspect, datetime
from pathlib import Path

DOCS_REPO_DEFAULT = "https://github.com/aixplain/sdk-documentation.git"
DOCS_SUBDIR = "docs"  # only this subtree feeds the skill; excludes versioned_docs/versioned_sidebars

# Map a changed doc path (relative to repo root) to the skill reference file it feeds.
DOC_TO_REF = [
    (r"assets/models/", "models.md"),
    (r"api-reference/python/aixplain/v2/model", "models.md"),
    (r"assets/agents/(agents|team-agents)", "agents.md"),
    (r"core-concepts/(agents|micro-agents)", "agents.md"),
    (r"api-reference/python/aixplain/v2/(agent|meta_agents|agent_progress)", "agents.md"),
    (r"assets/agents/inspectors", "governance.md"),
    (r"core-concepts/(debugger|evolver)", "governance.md"),
    (r"api-reference/python/aixplain/v2/inspector", "governance.md"),
    (r"assets/tools-and-integrations/(knowledge-base|shared-memory)", "knowledge-memory.md"),
    (r"tutorials/.*rag", "knowledge-memory.md"),
    (r"assets/tools-and-integrations/", "tools-integrations.md"),
    (r"api-reference/python/aixplain/v2/(tool|integration|utility|file|upload_utils)", "tools-integrations.md"),
    (r"api-reference/mcp-servers", "deployment-access.md"),
    (r"getting-started/(api-requests|migration)", "deployment-access.md"),
    (r"core-concepts/deployment", "deployment-access.md"),
    (r"deployment/", "deployment-access.md"),
    (r"platform-overview/teams-and-governance/(api-keys|rate-limiting|credits)", "deployment-access.md"),
    (r"tutorials/", "patterns.md"),
    (r"patterns/", "patterns.md"),
]

def ref_for_doc(path: str) -> str:
    for pat, ref in DOC_TO_REF:
        if re.search(pat, path):
            return ref
    return "(unmapped — review manually)"

# ----------------------------------------------------------------------------- SDK introspection

def introspect_sdk() -> dict:
    """Snapshot the public API the skill depends on. Pure introspection — no network/key."""
    out = {"version": None, "client_attrs": [], "signatures": {}, "enums": {}, "constants": {}, "errors": []}
    try:
        import importlib.metadata as md
        out["version"] = md.version("aixplain")
    except Exception as e:
        out["errors"].append(f"version: {e}")
    try:
        from aixplain import Aixplain
        out["client_attrs"] = sorted(a for a in dir(Aixplain) if not a.startswith("_"))
    except Exception as e:
        out["errors"].append(f"Aixplain import: {e}")
        return out

    def sig(obj, key):
        try:
            out["signatures"][key] = str(inspect.signature(obj))
        except Exception as e:
            out["signatures"][key] = f"<ERR {e}>"

    try:
        from aixplain import Aixplain
        sig(Aixplain.__init__, "Aixplain.__init__")
        from aixplain.v2.agent import Agent
        for m in ["__init__", "run", "run_async", "poll", "sync_poll", "save", "delete",
                  "generate_session_id", "get", "search", "to_dict"]:
            f = getattr(Agent, m, None)
            sig(f, f"Agent.{m}") if f else out["errors"].append(f"Agent.{m} MISSING")
        if hasattr(Agent, "Task"):
            sig(Agent.Task.__init__, "Agent.Task.__init__")
        if hasattr(Agent, "OutputFormat"):
            out["enums"]["Agent.OutputFormat"] = sorted(
                m for m in dir(Agent.OutputFormat) if m.isupper())
        from aixplain.v2.model import Model
        for m in ["get", "run", "run_async", "poll", "sync_poll", "run_stream", "as_tool"]:
            out["signatures"].setdefault(f"Model.{m}", "present" if hasattr(Model, m) else "MISSING")
        from aixplain.v2.tool import Tool
        for m in ["__init__", "run", "save", "get", "search", "list_actions"]:
            f = getattr(Tool, m, None)
            sig(f, f"Tool.{m}") if f else out["errors"].append(f"Tool.{m} MISSING")
        from aixplain.v2.integration import Integration
        out["signatures"]["Integration.methods"] = sorted(
            m for m in dir(Integration) if not m.startswith("_") and callable(getattr(Integration, m)))
        sig(Aixplain(api_key="DUMMY").Resource.__init__, "Resource.__init__")
    except Exception as e:
        out["errors"].append(f"core introspection: {e}")

    try:
        import aixplain.v2.inspector as insp
        out["enums"]["inspector_exports"] = sorted(m for m in dir(insp) if not m.startswith("_"))
        for name in ["InspectorAction", "InspectorOnExhaust", "InspectorSeverity",
                     "EvaluatorType", "InspectorTarget"]:
            cls = getattr(insp, name, None)
            if cls:
                out["enums"][name] = sorted(m for m in dir(cls) if m.isupper())
        if hasattr(insp, "AUTO_DEFAULT_MODEL_ID"):
            out["constants"]["AUTO_DEFAULT_MODEL_ID"] = str(insp.AUTO_DEFAULT_MODEL_ID)
        from aixplain.v2.inspector import Inspector, InspectorActionConfig, EvaluatorConfig, EditorConfig
        for c in [Inspector, InspectorActionConfig, EvaluatorConfig, EditorConfig]:
            sig(c.__init__, f"{c.__name__}.__init__")
    except Exception as e:
        out["errors"].append(f"inspector introspection: {e}")

    try:
        from aixplain.v2 import APIKey, APIKeyLimits, TokenType
        sig(APIKeyLimits.__init__, "APIKeyLimits.__init__")
        out["enums"]["TokenType"] = sorted(m for m in dir(TokenType) if m.isupper())
        from aixplain.v2.file import FileUploader
        sig(FileUploader.upload, "FileUploader.upload")
    except Exception as e:
        out["errors"].append(f"apikey/file introspection: {e}")
    return out

def diff_sdk(baseline: dict, current: dict) -> list[str]:
    diffs = []
    if baseline.get("version") != current.get("version"):
        diffs.append(f"SDK version: {baseline.get('version')} -> {current.get('version')}")
    b_attrs, c_attrs = set(baseline.get("client_attrs", [])), set(current.get("client_attrs", []))
    if b_attrs - c_attrs:
        diffs.append(f"client attrs REMOVED: {sorted(b_attrs - c_attrs)}")
    if c_attrs - b_attrs:
        diffs.append(f"client attrs ADDED: {sorted(c_attrs - b_attrs)}")
    for key in sorted(set(baseline.get("signatures", {})) | set(current.get("signatures", {}))):
        bv, cv = baseline["signatures"].get(key), current["signatures"].get(key)
        if bv != cv:
            diffs.append(f"signature {key}: {bv!r} -> {cv!r}")
    for key in sorted(set(baseline.get("enums", {})) | set(current.get("enums", {}))):
        bv, cv = baseline["enums"].get(key), current["enums"].get(key)
        if bv != cv:
            diffs.append(f"enum {key}: {bv} -> {cv}")
    for key in sorted(set(baseline.get("constants", {})) | set(current.get("constants", {}))):
        bv, cv = baseline["constants"].get(key), current["constants"].get(key)
        if bv != cv:
            diffs.append(f"constant {key}: {bv} -> {cv}")
    return diffs

# ----------------------------------------------------------------------------- snippet validation

CODE_FENCE = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
ENUM_REF = re.compile(r"\b(InspectorAction|InspectorOnExhaust|InspectorSeverity|EvaluatorType|"
                      r"InspectorTarget|TokenType)\.([A-Z_]+)\b")

def _aixplain_imports(block: str) -> list[str]:
    """Extract complete `import aixplain*` / `from aixplain* import ...` statements,
    correctly joining multi-line parenthesized or backslash-continued imports."""
    lines, stmts, i = block.splitlines(), [], 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("from aixplain") or s.startswith("import aixplain"):
            stmt = lines[i]
            while (stmt.count("(") > stmt.count(")") or stmt.rstrip().endswith("\\")) and i + 1 < len(lines):
                i += 1
                stmt += "\n" + lines[i]
            stmts.append(stmt)
        i += 1
    return stmts

def validate_snippets(skill: Path, sdk: dict) -> list[str]:
    """Check that every `from aixplain ... import` resolves and every enum member exists."""
    problems = []
    enums = sdk.get("enums", {})
    for md_file in sorted((skill / "references").glob("*.md")):
        if md_file.name.endswith(".ar.md"):
            continue  # Arabic files mirror the same code; validate English only
        text = md_file.read_text(encoding="utf-8")
        for lang, block in [(m.group(1), m.group(2)) for m in CODE_FENCE.finditer(text)]:
            if lang not in (None, "python", "py"):
                continue
            for stmt in _aixplain_imports(block):
                try:
                    exec(compile(stmt, "<snippet>", "exec"), {})
                except Exception as e:
                    first = stmt.strip().splitlines()[0]
                    problems.append(f"{md_file.name}: import failed `{first} …` -> {type(e).__name__}: {e}")
            for enum_name, member in ENUM_REF.findall(block):
                members = enums.get(enum_name)
                if members is not None and member not in members:
                    problems.append(f"{md_file.name}: {enum_name}.{member} no longer exists (have {members})")
    # also validate the SKILL.md body
    return problems

# ----------------------------------------------------------------------------- git docs diff

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def sync_docs(repo: str, work_dir: Path) -> Path:
    clone = work_dir / "sdk-documentation"
    if clone.exists() and (clone / ".git").exists():
        run(["git", "-C", str(clone), "fetch", "--quiet", "origin"])
    else:
        work_dir.mkdir(parents=True, exist_ok=True)
        r = run(["git", "clone", "--quiet", repo, str(clone)])
        if r.returncode != 0:
            raise RuntimeError(f"git clone failed: {r.stderr.strip()}")
    return clone

def docs_head(clone: Path) -> str:
    return run(["git", "-C", str(clone), "rev-parse", "origin/HEAD"]).stdout.strip() or \
           run(["git", "-C", str(clone), "rev-parse", "origin/main"]).stdout.strip()

def docs_diff(clone: Path, old_sha: str, new_sha: str) -> list[tuple[str, str]]:
    if not old_sha or old_sha == new_sha:
        return []
    r = run(["git", "-C", str(clone), "diff", "--name-status", f"{old_sha}..{new_sha}", "--", DOCS_SUBDIR])
    if r.returncode != 0:  # old sha not in history (shallow); fall back to listing tracked docs
        return [("?", p) for p in run(["git", "-C", str(clone), "ls-files", DOCS_SUBDIR]).stdout.split()]
    changes = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changes.append((parts[0], parts[-1]))
    return changes

# ----------------------------------------------------------------------------- LLM backend

def detect_backend() -> str:
    if shutil.which("claude"):
        return "claude-cli"
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa
            return "anthropic-api"
        except Exception:
            pass
    return "none"

def llm_complete(prompt: str, backend: str, model: str = "claude-opus-4-8") -> str | None:
    if backend == "claude-cli":
        r = run(["claude", "-p", prompt])
        return r.stdout if r.returncode == 0 else None
    if backend == "anthropic-api":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(model=model, max_tokens=8000,
                                     messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    return None

PATCH_PROMPT = """You maintain a Claude skill that documents the aiXplain Python SDK. Below is the CURRENT
skill reference file, followed by the NEW upstream documentation that feeds it (and the git diff).
Rewrite the reference file so it reflects the new docs, changing ONLY what the docs changed.

Hard rules:
- Keep the exact Markdown structure, headings, and house style of the current file.
- Every code snippet must use the v2 client (`from aixplain import Aixplain`; `aix.Agent/Model/Tool`).
- Do NOT invent APIs. If the docs are ambiguous, keep the current text.
- Preserve all the "gotcha" notes already in the file unless the docs contradict them.
- Output ONLY the full updated Markdown file content, nothing else.

=== CURRENT REFERENCE FILE ({ref_name}) ===
{ref_content}

=== NEW UPSTREAM DOC(S) ===
{doc_content}
"""

TRANSLATE_PROMPT = """Translate this Markdown file to Modern Standard Arabic (technical register).
Do NOT translate anything inside ``` code fences, inline `code`, API/method/param names, asset IDs,
URLs, file paths, or enum values — leave them in English. Keep Markdown structure identical and keep
relative links unchanged. If there is YAML frontmatter (between leading --- lines), keep it EXACTLY in
English. Output ONLY the translated Markdown.

{content}
"""

# ----------------------------------------------------------------------------- report + package

def write_report(skill: Path, doc_changes, ref_targets, sdk_diffs, snippet_problems, old_sha, new_sha, manifest):
    lines = ["# aixplain-builder refresh report", "",
             f"- Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
             f"- Docs baseline: `{old_sha or '(none)'}`  ->  latest: `{new_sha}`",
             f"- SDK baseline: `{manifest.get('sdk_version')}`  ->  installed: `{introspect_sdk().get('version')}`",
             "", "## Documentation changes", ""]
    if not doc_changes:
        lines.append("_No documentation changes since the recorded baseline._")
    else:
        lines.append("| Status | Doc file | Skill ref to review |")
        lines.append("|---|---|---|")
        for status, path in doc_changes:
            lines.append(f"| {status} | `{path}` | `{ref_for_doc(path)}` |")
    lines += ["", "## SDK API changes", ""]
    lines += ["_No SDK API changes detected._"] if not sdk_diffs else [f"- {d}" for d in sdk_diffs]
    lines += ["", "## Snippet validation", ""]
    lines += ["_All snippets valid against the installed SDK._"] if not snippet_problems else [f"- ⚠ {p}" for p in snippet_problems]
    lines += ["", "## Reference files to update", ""]
    lines += ["_None._"] if not ref_targets else [f"- `references/{r}`" for r in sorted(ref_targets)]
    report = skill / "tooling" / "refresh-report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report

PUBLISH_EXCLUDE_DIRS = {".work", "__pycache__", ".git"}
PUBLISH_EXCLUDE_FILES = {"refresh-report.md", "refresh.log"}

def _publishable_files(skill: Path):
    """Every file of the skill source worth publishing (skips caches + generated reports)."""
    for p in sorted(skill.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(skill)
        if set(rel.parts) & PUBLISH_EXCLUDE_DIRS:
            continue
        if p.name in PUBLISH_EXCLUDE_FILES:
            continue
        yield rel

def publish_skill(skill: Path, repo: str, path: str, branch: str, work_dir: Path,
                  do_pr: bool, dry_run: bool):
    """Sync the skill source into <repo>/<path> on <branch> and push (or open a PR)."""
    work_dir.mkdir(parents=True, exist_ok=True)
    clone = work_dir / f"publish-{repo.replace('/', '_')}"
    if clone.exists():
        shutil.rmtree(clone)
    print(f"Cloning {repo}@{branch} ...")
    r = run(["git", "clone", "--depth", "1", "-b", branch, f"https://github.com/{repo}.git", str(clone)])
    if r.returncode != 0:
        raise RuntimeError(f"clone failed: {r.stderr.strip()}")
    target = clone / path
    if target.exists():
        shutil.rmtree(target)          # replace wholesale so deletions propagate
    count = 0
    for rel in _publishable_files(skill):
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill / rel, dest)
        count += 1
    run(["git", "-C", str(clone), "add", "-A", path])
    if run(["git", "-C", str(clone), "diff", "--cached", "--quiet"]).returncode == 0:
        print("No changes to publish — target already up to date.")
        return
    msg = (f"Publish aixplain-builder skill to {path}\n\n"
           f"Synced {count} files from the skill source (SKILL.md + references/ EN&AR, "
           f"tooling/ refresh pipeline, manifest, evals).\n\n"
           f"Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    run(["git", "-C", str(clone), "-c", "user.name=elbadrashiny",
         "-c", "user.email=mohamed@aixplain.com", "commit", "-q", "-m", msg])
    if dry_run:
        print(f"[dry-run] committed locally in {clone}; NOT pushing.\n")
        print(run(["git", "-C", str(clone), "show", "--stat", "--oneline", "HEAD"]).stdout[:3000])
        return
    if do_pr:
        pbranch = "publish-aixplain-builder"
        run(["git", "-C", str(clone), "branch", "-M", pbranch])
        push = run(["git", "-C", str(clone), "push", "-u", "origin", pbranch, "--force"])
        if push.returncode != 0:
            raise RuntimeError(f"push failed: {push.stderr.strip()}")
        pr = run(["gh", "pr", "create", "--repo", repo, "--base", branch, "--head", pbranch,
                  "--title", "Add/update aixplain-builder skill",
                  "--body", "Publishes the aixplain-builder skill (and its refresh pipeline).\n\n"
                            "🤖 Generated with [Claude Code](https://claude.com/claude-code)"])
        print(pr.stdout.strip() or pr.stderr.strip())
    else:
        push = run(["git", "-C", str(clone), "push", "origin", f"HEAD:{branch}"])
        if push.returncode != 0:
            raise RuntimeError(f"push failed: {push.stderr.strip()}")
        print(push.stderr.strip() or push.stdout.strip())
    print(f"\nPublished {count} files -> {repo}:{path} on {branch}.")

def repackage(skill: Path) -> Path | None:
    """Zip SKILL.md + references/*.md into <skill-name>.skill (matches the packager's contents)."""
    import zipfile
    skill = skill.resolve()
    name = skill.name
    out = skill.parent / f"{name}.skill"
    files = [skill / "SKILL.md"] + sorted((skill / "references").glob("*.md"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, arcname=f"{name}/{f.relative_to(skill)}")
    return out

# ----------------------------------------------------------------------------- main

def load_manifest(skill: Path) -> dict:
    mf = skill / "manifest.json"
    return json.loads(mf.read_text()) if mf.exists() else {}

def save_manifest(skill: Path, manifest: dict):
    (skill / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Refresh the aixplain-builder skill from upstream docs + SDK.")
    ap.add_argument("mode", choices=["check", "apply", "snapshot-sdk", "publish"], nargs="?", default="check")
    ap.add_argument("--skill", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--docs-repo", default=DOCS_REPO_DEFAULT)
    ap.add_argument("--work-dir", type=Path, default=None)
    ap.add_argument("--no-translate", action="store_true")
    ap.add_argument("--no-package", action="store_true")
    ap.add_argument("--no-upgrade", action="store_true", help="skip the automatic `pip install --upgrade aixplain`")
    ap.add_argument("--yes", action="store_true")
    # publish mode
    ap.add_argument("--publish-repo", default="aixplain/aiXplain", help="target repo owner/name")
    ap.add_argument("--publish-path", default="skills/aixplain-builder", help="path within the target repo")
    ap.add_argument("--publish-branch", default="main", help="target branch")
    ap.add_argument("--pr", action="store_true", help="publish via a PR instead of pushing to the branch")
    ap.add_argument("--dry-run", action="store_true", help="publish: clone+sync+commit locally but do not push")
    args = ap.parse_args()

    skill = args.skill.resolve()
    work_dir = (args.work_dir or skill / "tooling" / ".work").resolve()
    baseline_path = skill / "tooling" / "baseline_sdk_signatures.json"

    if args.mode == "snapshot-sdk":
        snap = introspect_sdk()
        baseline_path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote SDK baseline ({snap.get('version')}) -> {baseline_path}")
        if snap["errors"]:
            print("Introspection warnings:", *snap["errors"], sep="\n  ")
        return

    if args.mode == "publish":
        publish_skill(skill, args.publish_repo, args.publish_path, args.publish_branch,
                      work_dir, args.pr, args.dry_run)
        return

    manifest = load_manifest(skill)
    baseline_sdk = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
    if not args.no_upgrade:
        print("Upgrading aixplain SDK (use --no-upgrade to skip) ...")
        run([sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "aixplain"])
    current_sdk = introspect_sdk()

    print("Syncing docs ...")
    clone = sync_docs(args.docs_repo, work_dir)
    new_sha = docs_head(clone)
    old_sha = manifest.get("docs_git_sha", "")
    doc_changes = docs_diff(clone, old_sha, new_sha)
    ref_targets = {ref_for_doc(p) for _, p in doc_changes}
    ref_targets.discard("(unmapped — review manually)")

    sdk_diffs = diff_sdk(baseline_sdk, current_sdk) if baseline_sdk else ["(no SDK baseline — run snapshot-sdk)"]
    snippet_problems = validate_snippets(skill, current_sdk)

    report = write_report(skill, doc_changes, ref_targets, sdk_diffs, snippet_problems, old_sha, new_sha, manifest)
    print(f"\n=== Summary ===")
    print(f"Doc changes: {len(doc_changes)} | SDK diffs: {len(sdk_diffs)} | snippet problems: {len(snippet_problems)}")
    print(f"Refs to review: {sorted(ref_targets) or 'none'}")
    print(f"Full report: {report}")

    if args.mode == "check":
        if doc_changes or snippet_problems or (sdk_diffs and baseline_sdk):
            print("\nChanges detected. Re-run with `apply` to patch (needs an LLM backend).")
        else:
            print("\nSkill is up to date.")
        return

    # ---- apply mode ----
    backend = detect_backend()
    print(f"\nLLM backend: {backend}")
    if backend == "none":
        print("No LLM backend available (no `claude` CLI, no ANTHROPIC_API_KEY). "
              "Report written; edit the flagged reference files by hand, then re-run snapshot-sdk and bump manifest.")
        return
    if not (doc_changes or snippet_problems):
        print("Nothing to patch. Updating manifest baseline only.")
    else:
        if not args.yes:
            ans = input(f"\nPatch {sorted(ref_targets)} via {backend}? Proposals written as *.proposed for review. [y/N] ")
            if ans.strip().lower() != "y":
                print("Aborted."); return
        # Build a quick lookup of changed doc contents
        changed_docs_by_ref: dict[str, list[str]] = {}
        for status, path in doc_changes:
            ref = ref_for_doc(path)
            if status == "D":
                snippet = f"[DELETED] {path}"
            else:
                fp = clone / path
                snippet = f"### {path}\n\n" + (fp.read_text(encoding='utf-8')[:12000] if fp.exists() else "(unreadable)")
            changed_docs_by_ref.setdefault(ref, []).append(snippet)
        for ref in sorted(ref_targets):
            ref_path = skill / "references" / ref
            if not ref_path.exists():
                print(f"  skip {ref} (not found)"); continue
            prompt = PATCH_PROMPT.format(ref_name=ref, ref_content=ref_path.read_text(encoding="utf-8"),
                                         doc_content="\n\n".join(changed_docs_by_ref.get(ref, [])))
            print(f"  patching {ref} ...")
            updated = llm_complete(prompt, backend)
            if updated and updated.strip():
                (ref_path.with_suffix(".md.proposed")).write_text(updated.strip() + "\n", encoding="utf-8")
                print(f"    wrote {ref}.proposed — review the diff, then move it over {ref}")
            else:
                print(f"    LLM returned nothing for {ref}")
        print("\nReview the *.proposed files and replace the originals you accept. "
              "Then, for accepted English changes, re-translate and re-package:")
        if args.no_translate:
            print("  (translation skipped per --no-translate)")
        if not args.no_package:
            pkg = repackage(skill)
            print(f"  (re-packaged current files -> {pkg}; re-run after applying proposals)")

    # Bump baselines so the next run diffs from here. Only do this when the user confirms in non-proposal flows.
    if args.yes:
        manifest["docs_git_sha"] = new_sha
        manifest["sdk_version"] = current_sdk.get("version")
        manifest["last_refreshed"] = datetime.date.today().isoformat()
        save_manifest(skill, manifest)
        baseline_path.write_text(json.dumps(current_sdk, indent=2) + "\n", encoding="utf-8")
        print("Manifest + SDK baseline updated.")

if __name__ == "__main__":
    main()
