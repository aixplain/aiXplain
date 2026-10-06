# Secret scanning

Tracks the committed-credential cleanup from ENG-3686 and the scanner that
prevents a repeat.

## What happened

Live platform API keys were committed in plaintext in scratch files that sat
outside `testpaths`, so no suite ever executed or reviewed them. In one case the
saved notebook output replayed the key many more times than the assignment
itself, so redacting the assignment alone would not have been enough. ENG-3686
removed those files from the tree; nothing that runs depended on them.

**The credentials are still in git history, and the repository is public.**
Deleting the files ends nothing: every exposed credential has to be rotated.
Rotation is urgent and independent of any PR, including the one that added this
scanner. Which credentials, their owners and the rotation status are tracked
privately in the ENG-3686 ticket, not here.

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
`Aixplain("...")`. A leaked assignment line went unreported by the defaults,
which caught only saved notebook output, so the same notebook saved without
outputs would have passed. `.gitleaks.toml` therefore adds two rules:
`aixplain-platform-key` (64 hex characters shortly after a credential name on
the same line) and `aixplain-client-positional-key` (the positional client
argument).

### Why gitleaks and not detect-secrets

Both were run against the tree. detect-secrets reported ~350 findings, almost
all of them 24-hex MongoDB asset IDs matched by its `HexHighEntropyString`
plugin. A baseline that large hides a real leak and needs regenerating every
time a test gains an asset ID. Gitleaks matches credential *shapes* rather than
raw entropy, and what it reports on the current tree is only the obvious
placeholders and hand-written fake keys in unit tests. Each is allowlisted by its
exact value, as is the planted fake key in `tests/unit/test_secret_scanning.py`,
so a real key added to any of those files is still reported.

### Allowlist policy

Keep exemptions narrow, and say why in the `description`. In particular, do not
allowlist a test directory wholesale — `tests/` is exactly where a real key gets
pasted "just to try something". Prefer the exact value over a path: a path
exemption hides whatever else is later committed to that file. Remove an entry
once nothing matches it, since a dead exemption can only hide something later.

## Open: rotation and history

These require platform access and a team decision. Their status lives in the
ENG-3686 ticket.

1. **Rotate** every credential that was ever committed, and confirm a request
   carrying it is refused. This is what actually ends the exposure, and it must
   not wait on any PR.
2. **Decide on history.** Rewriting with `git filter-repo` invalidates every
   open PR and every local clone, so it is a team call, not a per-ticket one. It
   cannot reach forks or anything already cloned, so on a public repository it
   only reduces the residue after rotation. Record the outcome on ENG-3686 either
   way: a rewrite that was discussed and declined and a rewrite nobody got round
   to look identical a year later.
3. **Audit the rest of history.** This cleanup covered the tree, not history.
   Run `gitleaks git --log-opts=--all --config .gitleaks.toml --redact` over
   every branch, and rotate anything it finds that is still live.
