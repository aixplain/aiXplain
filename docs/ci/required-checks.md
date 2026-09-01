# Required status checks on `main`

> **This document describes repository *settings* changes. Nothing here is applied by merging a PR.**
> ENG-3428 deliberately ships the workflows and this document; the settings flip is a one-time manual
> follow-up, because requiring contexts while CI is red would block every merge — including the PRs
> that make CI green.

## The problem this exists to close

`main` is branch-protected, but `required_status_checks.contexts` is **empty**, and
`GET /repos/aixplain/aixplain/rulesets` returns `[]`, so there is no ruleset backstop either. The
practical effect: a PR with red CI merges. PR #999 merged with 8 failing checks, and most of the last
dozen `main.yaml` runs were failures.

Every gate added by the surrounding work — the 62% coverage floor (ENG-3431), the `.git`-less
package-integrity build (ENG-3543), the zero-executed-test guard and the matrix/filesystem drift check
(ENG-3544) — is **advisory** until at least one context is marked required. This document names the
contexts and the order in which they can safely be turned on.

## Contexts, in tiers

GitHub names a matrix job `<job-name> (<base matrix values>)`. Keys contributed only by `include`
(here `path` and `timeout`) are **not** part of the name, so the `setup-and-test` legs appear as
`setup-and-test (agent)`, not `setup-and-test (agent, tests/functional/agent, 45)`.

| Tier | Context | Workflow | Runs on a PR today? | Precondition to require |
| ---- | ------- | -------- | ------------------- | ----------------------- |
| 1 | `pre-commit` | `pre-commit.yaml` | Yes (`push: '**'`) | None — requireable as soon as it is green |
| 1 | `unit-coverage` | `main.yaml` | **No** | `main.yaml` gains a `pull_request` trigger |
| 1 | `package-integrity` | `main.yaml` | **No** | `main.yaml` gains a `pull_request` trigger |
| 2 | `setup-and-test (file_asset)` | `main.yaml` | **No** | `pull_request` trigger **and** consistently green |
| 2 | `setup-and-test (data_asset)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (model)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (pipeline_2.0_v1)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (general_assets)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (apikey)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (agent)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (team_agent)` | `main.yaml` | **No** | as above |
| 2 | `setup-and-test (v2)` | `main.yaml` | **No** | as above |

Tier 2 legs consume `TEAM_API_KEY` and hit live backend assets, so their redness is frequently a
backend-availability problem rather than an SDK regression. Require them only once that is no longer
true.

`tests/unit/test_ci_permissions.py` asserts that the `setup-and-test (...)` list above matches
`main.yaml`'s matrix exactly, so adding, renaming, or deleting a leg fails a unit test instead of
silently leaving a stale required-context list here.

## Why `main.yaml` contexts cannot be required today

`main.yaml` triggers only on `push` to `main` and `test`, plus `workflow_dispatch`. A PR from a
feature branch therefore never produces a `unit-coverage`, `package-integrity`, or
`setup-and-test (...)` check. Marking those contexts required **right now** would leave every PR
permanently "Expected — Waiting for status to be reported": a merge deadlock, not a merge gate.

`pre-commit.yaml` triggers on `push` to `'**'`, so `pre-commit` is the only context that reports on a
feature-branch PR today — and it runs `tests/unit`, which includes the coverage-relevant suite and all
the static CI guards.

## Ordered procedure

1. **Merge the chain and let CI settle.** All nine ENG-34xx PRs in, `main.yaml` green on `main`.
2. **Add a `pull_request` trigger to `main.yaml`** in its own PR. The recommended shape is to run the
   two credential-free jobs (`unit-coverage`, `package-integrity`) on `pull_request` and leave the
   functional matrix on `push` / `workflow_dispatch`; that makes Tier 1 requireable without paying for
   a full functional run on every push. (Open question — see below.)
3. **Read the real check names off a PR.** Open any PR and copy the context strings verbatim from its
   checks list. Do not paste the table above into settings unverified: matrix naming depends on the
   matrix shape, and a context string that matches nothing is indistinguishable from a check that
   never reports.
4. **Require Tier 1.**
5. **Require Tier 2** only after those legs have been green on consecutive runs.

### Setting the contexts

Requires admin on the repository. This replaces the whole list, so include every context you want
required in one call:

```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  repos/aixplain/aixplain/branches/main/protection/required_status_checks \
  -F strict=true \
  -f 'contexts[]=pre-commit' \
  -f 'contexts[]=unit-coverage' \
  -f 'contexts[]=package-integrity'
```

`-F` (typed), not `-f` (raw string), for `strict`: `gh api -f strict=true` sends the JSON string
`"true"` and the endpoint rejects it with a 422 (`"true" is not a boolean`). The context strings do
want `-f`, so the two flags are deliberately mixed above.

`strict=true` additionally requires the branch to be up to date with `main` before merging. Verify:

```bash
gh api repos/aixplain/aixplain/branches/main/protection/required_status_checks --jq '.contexts'
```

### Fork PRs

`pull_request` runs from a fork receive **no secrets**, so any Tier 2 leg would fail or skip on an
external contribution. If the project accepts external PRs, Tier 2 required contexts and fork PRs are
mutually exclusive without a maintainer-triggered re-run.

`pull_request_target` is **not** an acceptable substitute: it runs with the base repository's secrets
against the fork's code, which is precisely the wrong trade for a suite that executes untrusted test
code.

## Manual one-time setup for the release pipeline

`.github/workflows/release.yaml` is inert until these are done. Merging it is safe in the meantime:
the `build` job passes and the `publish` job fails at the OIDC exchange with a clear PyPI error, so
nothing is published and nothing else breaks.

1. **Create the `pypi` environment** (Settings → Environments → New environment → `pypi`). Optionally
   add required reviewers or a wait timer: a wrong PyPI upload is unrecoverable, since filenames are
   immutable and can only be yanked.

   Also set **Deployment branches and tags → Selected** with a `v*` tag rule. Nothing in
   `release.yaml` can enforce which ref a tag points at — anyone who can push a tag can otherwise
   publish an arbitrary tree to PyPI under the project's name. The environment protection rule is the
   only place that restriction can live.
2. **Register the trusted publisher on PyPI.** Needs owner rights on the `aiXplain` PyPI project — the
   account that currently holds the upload token. On <https://pypi.org/manage/project/aixplain/settings/publishing/>:

   | Field | Value |
   | ----- | ----- |
   | Owner | `aixplain` |
   | Repository name | `aiXplain` |
   | Workflow name | `release.yaml` |
   | Environment name | `pypi` |

3. **Do one TestPyPI dry run** before the first real tag, to validate the OIDC exchange rather than
   discovering a misconfiguration on an immutable upload. Register the same publisher on TestPyPI and
   temporarily point the publish step at `repository-url: https://test.pypi.org/legacy/`.
4. **Revoke the long-lived PyPI API token** once the first trusted-publishing release succeeds. That
   token is the credential this pipeline exists to retire.
5. **Set the repository default workflow permissions to read-only** (Settings → Actions → General →
   Workflow permissions). Every workflow in the repo now declares its own `permissions:` block, so
   this is safe here — but check other branches first, since the default applies to workflow files on
   any ref.

### Releasing, once the above is done

```bash
# 1. bump [project].version in pyproject.toml, open a PR, merge it
# 2. tag the merged commit
git tag v0.2.48
git push origin v0.2.48
```

The `build` job refuses to proceed if the tag disagrees with `[project].version`, so a forgotten bump
surfaces as a red release run rather than a mislabelled file on PyPI. No local `twine upload`.

### Keeping the publish action's pin current

The publish step is pinned to a commit SHA, not `@release/v1`: it is the only step that holds a
credential able to upload as aiXplain, and a branch ref lets whoever can move it choose the code that
runs there. `tests/unit/test_ci_permissions.py` fails if the pin ever becomes a branch or tag ref.

To bump it, resolve the new commit and update both the ref and the trailing version comment:

```bash
gh api repos/pypa/gh-action-pypi-publish/git/ref/heads/release/v1 --jq '.object.sha'
```

### Follow-ups recorded here rather than done in ENG-3428

- **Extract `package-integrity` into a `workflow_call` reusable workflow** shared by `main.yaml` and
  `release.yaml`, so the release runs the full module census rather than the unit suite plus an
  install/import smoke.
- **Drop `twine` and `pre-commit` from `[project].dependencies`** — release tooling that every SDK
  consumer currently installs, a direct artifact of releasing from a laptop.

## Open questions

1. **How should `main.yaml` run on PRs?** (a) everything on `pull_request` — full functional spend on
   every push; (b) credential-free jobs only — recommended; (c) label-gated functional runs
   (`ci:full`). This decision determines whether Tier 2 is ever realistically requireable.
2. **Does the project accept external PRs?** If yes, see the fork-PR caveat above.
3. **Should the `pypi` environment require a human approval**, or is the tag itself the intended gate?
4. **Who owns the PyPI trusted-publisher registration?** The pipeline is inert until a named person
   with PyPI owner rights does it.
