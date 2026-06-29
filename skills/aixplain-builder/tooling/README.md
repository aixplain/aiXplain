# Skill maintenance tooling

`refresh_skill.py` keeps `aixplain-builder` in sync with the upstream aiXplain **docs** and **SDK**. It is maintenance tooling for the skill source tree — it is **not** part of the packaged `.skill` (the packager only ships `SKILL.md` + `references/*.md`).

## Quick start

```bash
# Report what changed upstream since the recorded baseline — never writes. Run this anytime.
python3 tooling/refresh_skill.py check

# Apply: patch the flagged reference files via an LLM, write proposals for review.
python3 tooling/refresh_skill.py apply           # interactive
python3 tooling/refresh_skill.py apply --yes      # also bump the baselines after

# Re-record the SDK baseline from the currently installed SDK (after you accept SDK-driven edits).
python3 tooling/refresh_skill.py snapshot-sdk

# Publish the skill to the SDK repo (aixplain/aiXplain : skills/aixplain-builder).
python3 tooling/refresh_skill.py publish --dry-run   # clone+sync+commit locally, no push
python3 tooling/refresh_skill.py publish --pr        # open a PR (main is protected — PR required)
```

`check`/`apply` auto-run `pip install --upgrade aixplain` first (pass `--no-upgrade` to skip), so a single `check` truly reflects the latest SDK.

## Publishing (`publish`)

Syncs the skill source into a target repo/path and opens a PR (or pushes, if the branch allows it):

- Defaults: `--publish-repo aixplain/aiXplain`, `--publish-path skills/aixplain-builder`, `--publish-branch main`.
- `--pr` pushes a `publish-aixplain-builder` branch and opens a PR (required when the target branch is protected — `aixplain/aiXplain:main` is). Without `--pr` it tries a direct push to the branch.
- `--dry-run` clones, syncs, and commits locally but does not push — use it to preview the file set.
- It replaces the target path wholesale (so deleted files propagate) and skips caches/generated reports. Uses `gh`/git auth.

## What each step does

1. **Docs sync + diff** — clones/fetches `sdk-documentation` and diffs `docs/` against `manifest.json`'s `docs_git_sha` (this automatically ignores `versioned_docs/` and `versioned_sidebars/`, which live outside `docs/`). Maps each changed doc file to the skill reference it feeds.
2. **SDK introspection diff** — `pip install --upgrade aixplain` first, then compares the live public API (client attrs, constructor/method signatures, enums, `AUTO_DEFAULT_MODEL_ID`, etc.) against `baseline_sdk_signatures.json`. Catches renamed/removed methods, params, and enum members. **No API key or credits needed** — pure introspection.
3. **Snippet validation** — extracts every Python code block from the reference files and (a) executes each `from aixplain … import …` so a removed/renamed symbol fails loudly, and (b) checks every `InspectorAction.X` / `EvaluatorType.X` / `TokenType.X` etc. against the live enum members.
4. **Report** — writes `tooling/refresh-report.md`: doc changes → refs to review, SDK API diffs, and any broken snippets.
5. **apply mode** — for each flagged reference, sends the current file + the changed upstream doc(s) to Claude and writes an updated `<ref>.md.proposed` for you to diff and accept. With an LLM backend it can also re-translate changed files to Arabic and re-package the `.skill`. With `--yes` it bumps `manifest.json` + the SDK baseline so the next run diffs from the new point.

## LLM backend (apply mode only)

Auto-detected in order: (1) `claude` CLI on PATH → `claude -p`; (2) `ANTHROPIC_API_KEY` + the `anthropic` package; (3) none → `apply` just writes the report and you edit the flagged files by hand. `check` never needs a backend.

## Files

- `manifest.json` (skill root) — the baseline: docs commit SHA + SDK version the references were built/validated against.
- `tooling/baseline_sdk_signatures.json` — snapshot of the SDK public API for drift detection.
- `tooling/refresh-report.md` — last report (regenerated each run).
- `tooling/.work/` — cached docs clone (gitignore-able; recreated automatically).

## Typical workflow

```bash
python3 tooling/refresh_skill.py check                 # see what moved upstream
python3 tooling/refresh_skill.py apply                 # get *.proposed patches
#  ... review each references/*.md.proposed, move the ones you accept over the originals ...
python3 tooling/refresh_skill.py check                 # confirm snippets still valid
python3 tooling/refresh_skill.py snapshot-sdk          # re-baseline the SDK
#  ... bump docs_git_sha in manifest.json to the latest, re-translate + re-package ...
```
