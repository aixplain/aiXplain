# Secret scanning

Tracks the committed-credential cleanup from ENG-3686 and the scanner that
prevents a repeat.

## What leaked

Two live-shaped credentials were committed in plaintext, both in root-level
scratch files that sat outside `testpaths` and so were never executed or
reviewed by any suite.

| File | Secret | Pointed at |
| --- | --- | --- |
| `test_agent_eval.py` (line 23) | 64-hex platform API key, passed as a literal `api_key=` argument | `https://dev-platform-api.aixplain.com` |
| `pipeline_test2.ipynb` | 64-hex `TEAM_API_KEY`, plus committed cell output replaying it inside request logs, webhook JWTs and pipeline payloads | `https://test-platform-api.aixplain.com` |

The notebook is the worse of the two. The key appears twice in its cell
sources and 22 more times in the saved cell output, so redacting the assignment
alone would not have been enough.

Both files were removed. `test_agent_eval.py` was an ad-hoc driver for the v2
evaluator. Only its `Eval().evaluate(...)` call is covered by
`tests/unit/v2/test_agent_evaluator.py`; the `Dataset.from_queries`,
`Metric.AgentResponseDataFields` and `additional_input_prompt` paths it touched
have no tests. No coverage was lost, since the script sat outside `testpaths`
and never ran. The notebook exercised the removed v1 `PipelineFactory`.

A third finding, a Zapier MCP share URL in the v1 test
`tests/functional/model/run_connect_model_test.py`, left the tree when that file
was deleted with v1 in #1136. The token remains only in history, and is covered
by the rotation and history decision below.

## What runs now

Gitleaks, pinned to one version in two places that a unit test keeps in step.

* **`.pre-commit-config.yaml`** runs `gitleaks` over the **staged diff**. This
  is the only point at which a credential can still be kept out of history.
* **`.github/workflows/pre-commit.yaml`** runs `gitleaks dir .` over the **whole
  tree** on every push to every branch. This step exists because the pre-commit
  hook is `--staged`-only and therefore scans nothing under
  `pre-commit run --all-files` — without it, CI would report a clean tree while
  checking none of it.
  The step checks the release tarball's sha256 before extracting it, and the
  `pre-commit run --all-files` step sets `SKIP: gitleaks`, because the hook
  would build Go from source only to scan an empty staged diff.
* **`.gitleaks.toml`** holds the rules and allowlists.
* **`tests/unit/test_secret_scanning.py`** re-states the specific defect. It
  fails if the hook is dropped or moved to a manual stage, if `useDefault = true`
  or a repo rule is removed, if the repo rules stop matching the leaked key
  shapes, or if the CI step is removed, made conditional, allowed to fail or left
  without its checksum check. It runs in the credential-free `unit-coverage`
  job, so it needs neither network nor a Go toolchain.

### Repo rules

The curated rules miss the shapes this repository actually leaked: a 64-hex
key in `os.environ["TEAM_API_KEY"] = "..."`, in
`{"Authorization": "Token ..."}`, and passed positionally as
`Aixplain("...")`. The deleted notebook's assignment line went unreported; the
default rules caught only its saved cell output, so the same notebook saved
without outputs would have passed. `.gitleaks.toml` therefore adds two rules:
`aixplain-platform-key` (64 hex characters shortly after a credential name on
the same line) and `aixplain-client-positional-key` (the positional client
argument). Both deleted files are still reported by them.

### Why gitleaks and not detect-secrets

Both were run against the tree. detect-secrets reported ~350 findings, almost
all of them 24-hex MongoDB asset IDs matched by its `HexHighEntropyString`
plugin. A baseline that large hides a real leak and needs regenerating every
time a test gains an asset ID. Gitleaks matches credential *shapes* rather than
raw entropy and reported 8 on the remaining tree: seven obvious placeholders and
the expired ECR password in `tests/mock_responses/login_response.json`. Each is
allowlisted by its exact value, as is the planted fake key in
`tests/unit/test_secret_scanning.py`, so a real key added to any of those files
is still reported.

### Allowlist policy

Keep exemptions narrow, and say why in the `description`. In particular, do not
allowlist a test directory wholesale — `tests/` is exactly where a real key gets
pasted "just to try something". Prefer the exact value over a path: a path
exemption hides whatever else is later committed to that file. Remove an entry
once nothing matches it, since a dead exemption can only hide something later.

## Open: key rotation and history rewrite

These require platform access and a team decision, and are **not** done.

1. **Rotate.** Identify the owner of the `dev-platform-api` key
   (`c43c6f6a…7672a`) and of the `test-platform-api` key (`500842da…4f356`),
   revoke both, and confirm a request carrying either returns 401. Neither key
   appears anywhere else in the tree: `git grep` finds the first only in the
   deleted `test_agent_eval.py` and the second only in the deleted notebook. No
   workflow, no `.env.example` entry and no CI secret references either, so
   revoking them should break nothing.

   **This is urgent and must not wait on this PR.** The repository is public,
   so both keys have been readable by anyone since they were committed, and
   deleting the files does not change that.

2. **Decide on history.** Removing the files clears the working tree; both keys
   remain reachable in history, as does the Zapier token. Rewriting with
   `git filter-repo` invalidates every open PR and every local clone, so it is a
   team call, not a per-ticket one. Rotation is what actually ends the exposure;
   a rewrite only reduces the residue afterwards, and cannot reach forks or
   anything already cloned. Because the repository is already public, a rewrite
   cannot undo the exposure. **Recommendation:** rotate first, regardless of
   whether a rewrite follows.

   Record the outcome on ENG-3686 either way. A rewrite that was discussed and
   declined and a rewrite nobody got round to look identical a year later.

3. **Audit the rest of history.** This cleanup covered the tree, not history.
   Run `gitleaks git --log-opts=--all --config .gitleaks.toml --redact` over
   every branch, and rotate anything it finds that is still live.
