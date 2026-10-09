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
(ENG-3544), and the 80% execution-ratio floor (ENG-3684) — is **advisory** until at least one context
is marked required. This document names the contexts and the order in which they can safely be turned
on.

## Contexts, in tiers

GitHub names a matrix job `<job-name> (<base matrix values>)`. Keys contributed only by `include`
(here `path`, `timeout`, `slack` and `prod_safe`) are **not** part of the name, so the `functional` legs appear as
`functional (agent)`, not `functional (agent, tests/functional/v2/test_agent.py, 30)`.

| Tier | Context | Workflow | Runs on a PR today? | Precondition to require |
| ---- | ------- | -------- | ------------------- | ----------------------- |
| 1 | `pre-commit` | `pre-commit.yaml` | Yes (`push: '**'`) | None — requireable as soon as it is green |
| 1 | `unit-coverage` | `main.yaml` | Yes | None — requireable as soon as it is green |
| 1 | `package-integrity` | `main.yaml` | Yes | None — requireable as soon as it is green |
| 1 | `functional-scope` | `main.yaml` | Yes | None — it is a decision, not a test; seconds long, no secrets |
| 2 | `functional-result` | `main.yaml` | Yes, always | Every leg consistently green |
| — | `production-backend` | `main.yaml` | No — production runs only | **Do not require** — skipped on every PR; it exists for the release gate |
| — | `functional (actions-inputs)` | `main.yaml` | Yes, when in scope | **Do not require** — informational, see below |
| — | `functional (agent)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (agent-duplicate)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (agent-lifecycle)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (agent-llm-persistence)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (agent-progress)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (agent-run-params)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (api-key)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (arabic-agent)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (debugger)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (eval)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (file)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (integration)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (issue)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (model)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (resource)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (rlm)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (session)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (skill)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (snake-case-e2e)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (team-agent)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (tool)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (trigger)` | `main.yaml` | Yes, when in scope | as above |
| — | `functional (utility)` | `main.yaml` | Yes, when in scope | as above |

The `file_asset`, `model`, `general_assets`, `apikey`, `agent`, `team_agent` and `benchmark` legs
exercised v1 exclusively and were deleted with it (PROD-2918). A v2 `team-agent` leg was later reintroduced for
the ported team-agent scenarios (ENG-3689).

The v2 functional suite runs one leg per `tests/functional/v2/test_*.py` file, so a failure names the
resource that broke. The per-leg contexts are what you read; `functional-result` is what you require.

**Why the legs themselves are not requireable.** "Yes, when in scope" means a leg runs when the
`functional-scope` job says it should. When it says no, the legs are not reported as one
skipped `functional (<leg>)` context each: a job-level `if:` is evaluated *before* the matrix expands,
so GitHub reports a single skipped context named `functional` instead (documented runner behaviour,
actions/runner#952). A required `functional (agent)` would then never report on a docs-only or fork
PR — a permanent "Expected — waiting for status to be reported", which is a merge deadlock rather
than a merge gate. Confirm this on a real docs-only PR before changing settings (step 3 below).

`functional-result` is a plain, non-matrix job with `if: always()`, so it reports under one fixed
name on every run. It **fails** when `functional-scope` did not succeed, and when the scope said the
matrix must run and the matrix finished as anything but `success`. It **passes** when the scope said
the matrix need not run. The decision still lives in a job rather than in `on.pull_request.paths`
for the same reason: a path filter suppresses the check itself.

The legs consume `TEAM_API_KEY` and hit live backend assets, so their redness is frequently a
backend-availability problem rather than an SDK regression. Since `functional-result` is red when
*any* leg is, require it only once every leg is reliably green; a chronically flaky leg has to be
fixed or parked first.

`tests/unit/test_ci_permissions.py` asserts that the `functional (...)` list above matches
`main.yaml`'s matrix exactly and that `functional-result` is listed, so adding, renaming, or deleting
a leg fails a unit test instead of silently leaving this table stale. The leg list still matters
after the aggregate: it is what `functional-result` stands for, and `release.yaml`'s gate checks
those per-leg names on the runs that actually ran.

## When each `main.yaml` context runs (ENG-3683)

`main.yaml` triggers on `push` to `main`/`test`, on `pull_request`, on a nightly `schedule`, and on
`workflow_dispatch`.

`unit-coverage` and `package-integrity` are credential-free and run on **every** PR. The
`functional (...)` legs hit a live backend with a real key, so a `functional-scope` job decides
per event whether they run, and `functional-result` reports the outcome under one name:

| Event | Functional legs run? |
| ----- | -------------------- |
| `push` to `main` / `test` | Always |
| `schedule` (nightly) | Always |
| `workflow_dispatch` | Always |
| PR from a fork, or from a deleted repository | Never — a fork PR receives no secrets, so every leg would be red for a reason that says nothing about the contribution |
| PR carrying the `functional-tests` label | Yes |
| PR touching `aixplain/**`, `tests/functional/**`, `tests/conftest.py`, `pyproject.toml` or `.github/workflows/main.yaml` | Yes |
| Any other PR | No (reported as skipped; `functional-result` passes) |

`pyproject.toml` is in the list because a dependency bump is the classic way functional behaviour
breaks; `tests/conftest.py` because every leg loads it; `main.yaml` because it builds the legs'
environment.

**The `issue` leg does not run on production.** Every test in `tests/functional/v2/test_issue.py`
files a real issue, and there is no API to delete one, so a run against production (a push to
`main`, a dispatch on `main` or a `v*` tag) would add two test reports to the production issue
system each time. The leg carries `prod_safe: false` in the matrix, and the "Run Tests" step skips
pytest for such a leg when IS_PROD is true, logs a `::notice::` saying why, and exits 0. It still
runs against the test backend on PRs, pushes to `test` and the nightly. On a production run
`functional (issue)` therefore reports **success without having run** — see the release gate below.

The `functional-tests` label is the manual override for a PR whose risk is not visible in its paths
— a backend migration, a change to a file the list above does not name. `labeled` is in the
trigger's `types`, so adding the label starts a run by itself rather than waiting for the next push.

Adding *any other* label starts a run too, and that run makes the normal path-based decision. It is
deliberately not short-circuited to "skip": a skipped run on the same commit would then be the latest
word on a PR whose previous run was red. What bounds the cost instead is the workflow's
`concurrency:` group — one group per PR with `cancel-in-progress`, so a burst of labels or pushes
leaves one run going rather than several matrices side by side. Push, schedule and dispatch runs
each get a group of their own and are never cancelled or dropped: GitHub keeps only one pending run
per group, and a dropped push run on `main` is a commit the release gate below cannot release.

Within one run, the `functional` job's `max-parallel: 4` runs four legs at a time. Every leg drives
agents on the same test tenant, which refuses runs past its concurrency cap with
`err.agent_concurrency_limit_reached`; with all legs at once, the first live run lost ~40 tests to it.
`tests/unit/test_ci_matrix_coverage.py` fails if the cap is removed or raised above four.

`pre-commit.yaml` triggers on `push` to `'**'`, so `pre-commit` also reports on a feature-branch
PR. It runs `tests/unit`, which includes the coverage-relevant suite and all the static CI guards,
and takes no secret, so unlike the functional legs its redness always means an SDK-side problem.

The `generator-drift` context is gone: the code generator it ran rendered v1 modules only, and both
went with v1 in 0.3.0 (PROD-2918).

### The nightly run

`schedule: '17 3 * * *'` runs the full matrix against the **test** backend every night. It exists
because the PR path filter is, by construction, blind to anything that changes outside this
repository: a backend deployment can break every functional suite while no PR touches
`aixplain/**`.

A scheduled run always executes on the default branch, which is `main`: the nightly tests `main`'s
code, and from the workflow's point of view its ref *is* `main`. That is why the `functional` job's
`IS_PROD` allow-lists events (`push` and `workflow_dispatch`) as well as refs. Keyed on the ref
alone, as it first was, the nightly ran every leg against production with `TEAM_API_KEY_PROD`.

The `nightly-report` job posts to Slack when the nightly is not green, via a plain incoming webhook
in the `SLACK_NIGHTLY_WEBHOOK_URL` secret (deliberately not the `SLACK_TOKEN` the Slack *integration
tests* consume — different audience, different rotation). **Until that secret is set, the job logs a
workflow warning and sends nothing**; it does not fail, since the nightly is already red and a second
red job saying so adds nothing.

### Secrets the functional legs read

Set per environment. The `_PROD` variant is used by a push to `main` and by a manual dispatch on
`main` or a `v*` tag; the plain one by everything else (a push to `test`, PRs, the nightly, a
dispatch on any other ref). Outside production the `_PROD` secrets are not merely unused: the step's
`env:` expands them to the empty string, so a PR job — which runs `pip install ".[test]"` on whatever
dependency changes the PR carries — never holds the production key.

| Secret | Used by | If unset |
| ------ | ------- | -------- |
| `TEAM_API_KEY` / `TEAM_API_KEY_PROD` | every functional leg | every leg fails |
| `SLACK_TOKEN` | the Slack tests in the `agent-lifecycle`, `model` and `tool` legs — the legs with `slack: true`; no other leg receives it | those tests skip |
| `SLACK_NIGHTLY_WEBHOOK_URL` | `nightly-report` | no alert is sent; the job logs a warning |

`SLACK_TOKEN` is gated like the `_PROD` secrets: the step's `env:` expands it only on a leg whose
`include` entry has `slack: true`, and `tests/unit/test_ci_pr_and_release_gates.py` fails if that set
drifts from the legs whose test file uses the `slack_token` fixture. `HF_TOKEN` is no longer exported
at all: no functional test reads it.

`AIXPLAIN_API_KEY` is **not** a separate secret. The workflow exports it with the same value as
`TEAM_API_KEY`, because every functional conftest accepts it as the canonical fallback while
`aixplain/utils/config.py` raises when the two are set and differ. Adding a second, different
credential under that name would fail every leg at import time.

These are repository secrets and have to be created by hand (Settings → Secrets and variables →
Actions). The two `TEST_…_ID` secrets name backend-resident objects — an integration and a connected
tool — so their values differ between the test and production backends, and their `_PROD` variants
are gated on IS_PROD exactly like `TEAM_API_KEY_PROD`. The tests used to skip themselves when they
were missing, so the event-trigger half of `test_trigger.py` had never run in CI and the leg still
reported green; they fail now instead (ENG-3684), which means both pairs have to exist before the
`trigger` leg can go green.

## Ordered procedure

1. **Merge the chain and let CI settle.** All nine ENG-34xx PRs in, `main.yaml` green on `main`.
2. ~~**Add a `pull_request` trigger to `main.yaml`**~~ — done in ENG-3683. Option (c) from the open
   question below was taken, with a path filter as the default and the `functional-tests` label as
   the override, so Tier 1 is requireable without paying for a functional run on every push and
   Tier 2 still reports on the PRs that can actually break it.
3. **Read the real check names off a PR.** Open any PR and copy the context strings verbatim from its
   checks list. Do not paste the table above into settings unverified: matrix naming depends on the
   matrix shape, and a context string that matches nothing is indistinguishable from a check that
   never reports. Use a docs-only PR as well as one that runs the legs: it is the one that shows the
   skipped matrix reporting as a single `functional` context, and `functional-result` passing.
4. **Require Tier 1.**
5. **Require Tier 2** (`functional-result`) only after every leg has been green on consecutive runs.
   Never require the per-leg `functional (...)` contexts — see "Why the legs themselves are not
   requireable" above.

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

`pull_request` runs from a fork receive **no secrets**, so any functional leg would fail on an
external contribution. Since ENG-3683 the `functional-scope` job detects this
(`github.event.pull_request.head.repo.full_name != github.repository`) and skips the legs, and
`functional-result` passes — so Tier 2 can be required without deadlocking fork PRs. An empty
`full_name`, which is what a PR from a deleted fork reports, is treated as a fork too: when the
origin cannot be told, the check fails closed.

The trade is explicit: an external contribution gets **no functional coverage** before merge. A
maintainer who wants it must run `main.yaml` by `workflow_dispatch` against a branch holding the
same code, inside this repository.

`pull_request_target` is **not** an acceptable substitute: it runs with the base repository's secrets
against the fork's code, which is precisely the wrong trade for a suite that executes untrusted test
code.

## The release's functional gate (ENG-3683)

`release.yaml` runs a `functional-gate` job before anything is built. It asks one question through
the Actions API: **did every `functional (...)` leg succeed, against the production backend, on the
exact commit this tag points at?**

- It keys on `github.sha`, not the tag name — a tag can be moved, and what was tested is a commit.
- It counts only **production runs**: a `push` to `main`, or a `workflow_dispatch` whose ref is this
  tag. A push to `test`, a PR run or the nightly may sit on the same commit, but their legs passed
  against the test backend, which proves nothing about what the wheel is published for. The dispatch
  has to be on the tag by name rather than on any ref starting with `v`, because branches such as
  `version_2` exist and a dispatch on a branch runs against the test backend.
- A run's `head_branch` is a bare name, so a dispatch on a *branch* named exactly like the tag would
  pass that filter. Each counted run must therefore also contain a successful `production-backend`
  job, which `main.yaml` runs only when IS_PROD is true (the same expression, repeated because a
  job-level `if:` cannot read another job's `env:`; a unit test fails if the two disagree). A run
  without it is logged as a warning and ignored.
- It reads the leg list out of `.github/workflows/main.yaml` **at the tagged commit**, so a leg added
  in the same release is not quietly optional on the release that first ships it.
- It takes the union of *all* completed production runs on that SHA, so "first run failed, failed
  legs re-run green" correctly counts as green.
- It holds `contents: read` and `actions: read`, nothing else. It decides; it never re-runs anything.

Under the normal flow (bump the version in a PR, merge, tag the merged commit) the push to `main`
has already produced that run, and the gate passes without any extra step.

`functional (issue)` is green on every production run because the leg is skipped there (see "When
each `main.yaml` context runs"), so the gate counts it without it having run against production. That
is deliberate: no production run can exercise it without filing issues that cannot be deleted, and
the gate would otherwise block every release. Its coverage comes from the test-backend runs.

**If the gate fails with "no completed production run of main.yaml on `<sha>`"**, first check
whether the `main` run on that commit is simply still going: a tag pushed right after the merge
finds it in progress, and an in-progress run does not count. Wait for it to finish, then re-run the
release.

Otherwise the tagged commit never had a production functional run — typically a tag on a commit
that was never pushed to `main`. A push to `test` does **not** fix this, nor does a PR run: both use
the test backend. Recover by running the workflow against the tag itself: Actions → *Run Tests* →
**Run workflow** → set the ref to the tag. A `v*` tag is treated as production there, so that
dispatch uses `TEAM_API_KEY_PROD` and the production backend — the environment the wheel is being
published for. Let it go green, then re-run the release.

**If the gate lists legs as `MISSING`**, a production run exists but those legs never succeeded in
it. Re-run the failed jobs of that run (or dispatch on the tag as above), then re-run the release.

There is deliberately no override input: `release.yaml` triggers on tag push alone (asserted by
`tests/unit/test_ci_permissions.py`), so there is nowhere for a "skip the gate" flag to live. That
is the intent — the way past this gate is a green functional run, not a checkbox.

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

1. ~~**How should `main.yaml` run on PRs?**~~ — settled in ENG-3683: credential-free jobs on every
   PR, functional legs on a path filter (`aixplain/**`, `tests/functional/**`, `tests/conftest.py`,
   `pyproject.toml`, `.github/workflows/main.yaml`) with a `functional-tests` label as the manual
   override. See "When each `main.yaml` context runs" above.
2. **Does the project accept external PRs?** If yes, note that fork PRs now skip the functional legs
   rather than failing them — see the fork-PR section above for what that costs.
3. **Should the `pypi` environment require a human approval**, or is the tag itself the intended gate?
4. **Who owns the PyPI trusted-publisher registration?** The pipeline is inert until a named person
   with PyPI owner rights does it.
