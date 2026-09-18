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
| 1 | `generator-drift` | `generator-drift.yaml` | Yes (`push: '**'`) | None — requireable as soon as it is green |
| 1 | `unit-coverage` | `main.yaml` | Yes | None — requireable as soon as it is green |
| 1 | `package-integrity` | `main.yaml` | Yes | None — requireable as soon as it is green |
| 1 | `functional-scope` | `main.yaml` | Yes | None — it is a decision, not a test; seconds long, no secrets |
| 2 | `setup-and-test (file_asset)` | `main.yaml` | Yes, when in scope | Consistently green |
| 2 | `setup-and-test (model)` | `main.yaml` | Yes, when in scope | as above |
| 2 | `setup-and-test (general_assets)` | `main.yaml` | Yes, when in scope | as above |
| 2 | `setup-and-test (apikey)` | `main.yaml` | Yes, when in scope | as above |
| 2 | `setup-and-test (agent)` | `main.yaml` | Yes, when in scope | as above |
| 2 | `setup-and-test (team_agent)` | `main.yaml` | Yes, when in scope | as above |
| 2 | `setup-and-test (v2)` | `main.yaml` | Yes, when in scope | as above |

Tier 2 legs consume `TEAM_API_KEY` and hit live backend assets, so their redness is frequently a
backend-availability problem rather than an SDK regression. Require them only once that is no longer
true.

"Yes, when in scope" means the leg runs when the `functional-scope` job says it should, and is
reported as **skipped** otherwise. GitHub counts a skipped job as satisfying a required status
check, so requiring these contexts does not block a docs-only or fork PR. That is the whole reason
the decision lives in a job's `if:` rather than in `on.pull_request.paths` — a path filter suppresses
the check itself, and a required context that never reports is a permanent "Expected — waiting for
status to be reported".

`tests/unit/test_ci_permissions.py` asserts that the `setup-and-test (...)` list above matches
`main.yaml`'s matrix exactly, so adding, renaming, or deleting a leg fails a unit test instead of
silently leaving a stale required-context list here.

## When each `main.yaml` context runs (ENG-3683)

`main.yaml` triggers on `push` to `main`/`test`, on `pull_request`, on a nightly `schedule`, and on
`workflow_dispatch`.

`unit-coverage` and `package-integrity` are credential-free and run on **every** PR. The seven
`setup-and-test (...)` legs hit a live backend with a real key, so a `functional-scope` job decides
per event whether they run:

| Event | Functional legs run? |
| ----- | -------------------- |
| `push` to `main` / `test` | Always |
| `schedule` (nightly) | Always |
| `workflow_dispatch` | Always |
| PR from a fork | Never — a fork PR receives no secrets, so every leg would be red for a reason that says nothing about the contribution |
| PR touching `aixplain/**` or `tests/functional/**` | Yes |
| PR carrying the `functional-tests` label | Yes |
| Any other PR | No (reported as skipped) |

The `functional-tests` label is the manual override for a PR whose risk is not visible in its paths
— a dependency bump, a CI change, a backend migration. `labeled` is in the trigger's `types`, so
adding the label starts a run by itself rather than waiting for the next push.

`pre-commit.yaml` and `generator-drift.yaml` trigger on `push` to `'**'`, so `pre-commit` and
`generator-drift` also report on a feature-branch PR. `pre-commit` runs `tests/unit`, which includes
the coverage-relevant suite and all the static CI guards; `generator-drift` runs
`python generate.py render --check`, which re-renders the generated modules from the committed
fixtures into a scratch directory and fails if the committed ones differ (ENG-3435). It takes no
secret: the render step is offline by construction, so unlike the Tier 2 legs its redness always
means an SDK-side problem.

### The nightly run

`schedule: '17 3 * * *'` runs the full matrix against the **test** backend every night. It exists
because the PR path filter is, by construction, blind to anything that changes outside this
repository: a backend deployment can break every functional suite while no PR touches
`aixplain/**`.

The `nightly-report` job posts to Slack when the nightly is not green, via a plain incoming webhook
in the `SLACK_NIGHTLY_WEBHOOK_URL` secret (deliberately not the `SLACK_TOKEN` the Slack *integration
tests* consume — different audience, different rotation). **Until that secret is set, the job logs a
workflow warning and sends nothing**; it does not fail, since the nightly is already red and a second
red job saying so adds nothing.

### Secrets the functional legs read

Set per environment: the `_PROD` variant is used on `main` and on a `v*` tag, the plain one on
everything else (the `test` branch, PRs, the nightly).

| Secret | Used by | If unset |
| ------ | ------- | -------- |
| `TEAM_API_KEY` / `TEAM_API_KEY_PROD` | every functional leg | every leg fails |
| `TEST_COMPOSIO_INTEGRATION_ID` / `…_PROD` | `TestEventTriggerDiscovery` in `tests/functional/v2/test_trigger.py` | **the class skips and the leg is still green** |
| `TEST_CONNECTION_ID` / `…_PROD` | `TestEventTriggerLifecycle` in the same file | **as above** |
| `SLACK_TOKEN` | the Slack integration tests | those tests skip |
| `HF_TOKEN` | Hugging Face model tests | those tests skip |
| `SLACK_NIGHTLY_WEBHOOK_URL` | `nightly-report` | no alert is sent; the job logs a warning |

`AIXPLAIN_API_KEY` is **not** a separate secret. The workflow exports it with the same value as
`TEAM_API_KEY`, because every functional conftest accepts it as the canonical fallback while
`aixplain/utils/config.py` raises when the two are set and differ. Adding a second, different
credential under that name would fail every leg at import time.

The two `TEST_…_ID` rows are the reason this table exists: nothing fails when they are missing. The
event-trigger classes skip, the leg reports green, and the coverage is absent without a single red
check to say so (ENG-3683). Both name backend-resident objects, so the values differ between the
test and production backends.

## Ordered procedure

1. **Merge the chain and let CI settle.** All nine ENG-34xx PRs in, `main.yaml` green on `main`.
2. ~~**Add a `pull_request` trigger to `main.yaml`**~~ — done in ENG-3683. Option (c) from the open
   question below was taken, with a path filter as the default and the `functional-tests` label as
   the override, so Tier 1 is requireable without paying for a functional run on every push and
   Tier 2 still reports on the PRs that can actually break it.
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

`pull_request` runs from a fork receive **no secrets**, so any Tier 2 leg would fail on an external
contribution. Since ENG-3683 the `functional-scope` job detects this
(`github.event.pull_request.head.repo.full_name != github.repository`) and skips the legs, which
counts as satisfying a required context — so Tier 2 can be required without deadlocking fork PRs.

The trade is explicit: an external contribution gets **no functional coverage** before merge. A
maintainer who wants it must run `main.yaml` by `workflow_dispatch` against a branch holding the
same code, inside this repository.

`pull_request_target` is **not** an acceptable substitute: it runs with the base repository's secrets
against the fork's code, which is precisely the wrong trade for a suite that executes untrusted test
code.

## The release's functional gate (ENG-3683)

`release.yaml` runs a `functional-gate` job before anything is built. It asks one question through
the Actions API: **did every `setup-and-test (...)` leg succeed on the exact commit this tag points
at?**

- It keys on `github.sha`, not the tag name — a tag can be moved, and what was tested is a commit.
- It reads the leg list out of `.github/workflows/main.yaml` **at the tagged commit**, so a leg added
  in the same release is not quietly optional on the release that first ships it.
- It takes the union of *all* completed runs on that SHA, so "first run failed, failed legs re-run
  green" correctly counts as green.
- It holds `contents: read` and `actions: read`, nothing else. It decides; it never re-runs anything.

Under the normal flow (bump the version in a PR, merge, tag the merged commit) the push to `main`
has already produced that run, and the gate passes without any extra step.

**If the gate fails with "no completed run of main.yaml on `<sha>`"**, the tagged commit never had a
functional run — typically a tag on a commit that was never pushed to `main` or `test`. Recover by
running the workflow against the tag itself: Actions → *Run Tests* → **Run workflow** → set the ref
to the tag. A `v*` tag is treated as production there, so that dispatch uses `TEAM_API_KEY_PROD` and
the production backend — the environment the wheel is being published for. Let it go green, then
re-run the release.

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
   PR, functional legs on a path filter (`aixplain/**`, `tests/functional/**`) with a
   `functional-tests` label as the manual override. See "When each `main.yaml` context runs" above.
2. **Does the project accept external PRs?** If yes, note that fork PRs now skip the functional legs
   rather than failing them — see the fork-PR section above for what that costs.
3. **Should the `pypi` environment require a human approval**, or is the tag itself the intended gate?
4. **Who owns the PyPI trusted-publisher registration?** The pipeline is inert until a named person
   with PyPI owner rights does it.
