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

The notebook is the worse of the two: executing a cell and saving the output
re-emitted the key a further sixteen times, including inside signed webhook
JWTs, so redacting the assignment alone would not have been enough.

Both files were removed. `test_agent_eval.py` was an ad-hoc driver for the v2
evaluator whose behaviour is already covered by
`tests/unit/v2/test_agent_evaluator.py`; the notebook exercised the deprecated
v1 `PipelineFactory`.

A third finding, the Zapier MCP share URL in
`tests/functional/model/run_connect_model_test.py`, is deliberately **not**
addressed here. It lives in a v1 test, and v1 is being removed under a separate
deprecation PR. The endpoint is dead and the test is skipped, so leaving it
until that PR lands costs nothing. Gitleaks does not flag it, so it will not
block CI in the meantime.

## What runs now

Gitleaks, pinned to one version in two places that a unit test keeps in step.

* **`.pre-commit-config.yaml`** runs `gitleaks` over the **staged diff**. This
  is the only point at which a credential can still be kept out of history.
* **`.github/workflows/pre-commit.yaml`** runs `gitleaks dir .` over the **whole
  tree** on every push to every branch. This step exists because the pre-commit
  hook is `--staged`-only and therefore scans nothing under
  `pre-commit run --all-files` — without it, CI would report a clean tree while
  checking none of it.
* **`.gitleaks.toml`** holds the rules and allowlists.
* **`tests/unit/test_secret_scanning.py`** re-states the specific defect and
  fails if the hook, the CI step or `useDefault = true` is dropped. It runs in
  the credential-free `unit-coverage` job, so it needs neither network nor a Go
  toolchain.

### Why gitleaks and not detect-secrets

Both were run against the tree. detect-secrets reported ~350 findings, almost
all of them 24-hex MongoDB asset IDs matched by its `HexHighEntropyString`
plugin. A baseline that large hides a real leak and needs regenerating every
time a test gains an asset ID. Gitleaks matches credential *shapes* rather than
raw entropy and reported 8, all obvious placeholders, each now allowlisted by
its literal value.

### Allowlist policy

Keep exemptions narrow, and say why in the `description`. In particular, do not
allowlist a test directory wholesale — `tests/` is exactly where a real key gets
pasted "just to try something". The SSRF fixtures in the v2 URL-guard tests
(`169.254.169.254`, RFC1918 and loopback addresses, which those tests must name
literally to assert the key is never sent to them) are exempted with
`condition = "AND"`, so the exemption covers those addresses in those files and
a real secret committed alongside them is still reported.

## Open: key rotation and history rewrite

These require platform access and a team decision, and are **not** done.

1. **Rotate.** Identify the owner of the `dev-platform-api` key
   (`c43c6f6a…7672a`) and of the `test-platform-api` key (`500842da…4f356`),
   revoke both, and confirm a request carrying either returns 401. Neither key
   appears anywhere else in the tree: `git grep` finds the first only in the
   deleted `test_agent_eval.py` and the second only in the deleted notebook. No
   workflow, no `.env.example` entry and no CI secret references either, so
   revoking them should break nothing.

2. **Decide on history.** Removing the files clears the working tree; both keys
   remain reachable in history, as does the Zapier token. Rewriting with
   `git filter-repo` invalidates every open PR and every local clone, so it is a
   team call, not a per-ticket one. Rotation is what actually ends the exposure;
   a rewrite only reduces the residue afterwards, and cannot reach forks or
   anything already cloned. **Recommendation:** rotate first, and skip the
   rewrite unless the repository is about to be made public.

   Record the outcome on ENG-3686 either way. A rewrite that was discussed and
   declined and a rewrite nobody got round to look identical a year later.
