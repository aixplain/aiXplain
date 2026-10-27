# Testing layers: where a new test belongs

ENG-3761 reviewed the fixes shipped to this SDK and to aixplain-agents between
2026-07-07 and 2026-10-08. Nearly every fix came with a test, but bugs still
reached users. Almost every test mocked `client.request` or
`session.request` and returned a dict the author typed. That dict encoded
the author's belief about the platform, the model or the network, and the
belief was often the bug:

* #983 read diagnostic codes from the top level of the poll body. The
  platform nests them under `data`.
* BUG-1092 and #1146 sent sort and filter keys that the backend accepts and
  then ignores.
* BUG-1090 re-sent a billed POST after a read timeout. The mocked session
  could not show that urllib3 retries below the SDK.

ENG-3782 added the layers below. Before writing a test, find the row that
matches what can go wrong. A unit test with a hand-built response is the
right answer only when nothing on this list applies.

| If the change touches... | the test belongs in | it runs | CI job (schedule) |
|---|---|---|---|
| A field the SDK reads from, or sends to, the platform: asset detail, search and paginate bodies, run and poll envelopes, error bodies | `tests/contract/` | recorded platform responses, through the real `Aixplain` client and `requests` session | `test-layers.yaml` → `contract` (every PR and push) |
| How a streamed model answer is parsed: content, reasoning, tool calls, finish_reason, usage, errors in the stream | `tests/stream_replay/` | recorded SSE bodies, served on the wire to `Model.run_stream` | `test-layers.yaml` → `stream-replay` (every PR and push) |
| Timeouts, retries, backoff, Retry-After, resubmission, poll budgets | `tests/fault/` | local HTTP servers behind toxiproxy (stall, slow body, reset, 503/429, close without response) | `test-layers.yaml` → `fault-injection` (every PR and push) |
| Where the API key goes: headers, logs, errors, redirects, poll URLs, the environment, the RLM sandbox | `tests/security/` | a canary key through every client flow; the real sandbox guard | `test-layers.yaml` → `security` (every PR and push) |
| Pure logic with no platform, model, network or credential in the path | `tests/unit/` | — | `main.yaml` → `unit-coverage` (every PR) |
| Behaviour only the real backend can show (does the platform honour this field?) | `tests/functional/` | the real test/prod backend | `main.yaml` → `functional (<leg>)` |

All four new layers are hermetic. Every host is a `*.test` name that never
resolves, or a server on 127.0.0.1, so a request that escapes the stub fails
on DNS and never reaches a real backend. They need no credential and run on
Python 3.9 like the unit suite.

## Contract (`tests/contract/`)

Every response comes from a JSON recording under `tests/contract/recordings`,
never from a dict typed into the test. `tests/support/platform_replay.py`
patches `requests.adapters.HTTPAdapter.send`. The SDK's own session,
retry adapter and trusted-origin checks therefore run for real, and only the
bytes come from the recording.

* `platform.serve("backend/agent-detail")` answers the recording's endpoint.
  Pass `then=[...]` for later answers (the last one repeats) and `where=` to
  match a path parameter.
* A request that no recording answers raises `ConnectionError`, and
  `platform.unmatched` lists it.
* `platform.sent("POST", "/execute")` returns the requests the SDK sent,
  for asserting on what reached the wire.

A recording has `contract` (one line on what it pins), `endpoint`,
`response` and `provenance`. `provenance.source` is one of:

* `live`: recorded from a real backend and scrubbed.
* `reconstructed`: built from platform-backend source; `derived_from` names
  the DTO and line range.
* `generated`: produced by a tool in `tests/contract/tools/`.

Replace a `reconstructed` recording with a live one when you can.
`test_recordings.py` fails on a recording no test replays and on one that
carries a credential.

`platform_request_readers.py` lists the request keys platform-backend reads
for search and paginate. A key the SDK sends that is not on that list is
ignored by the backend, which is the BUG-1092 class of bug. Update the list
from platform-backend, not from the SDK.

## Stream replay (`tests/stream_replay/`)

Each file under `streams/<family>/` holds an SSE body and what it means:
`expected.content`, `reasoning`, `tool_call_names`, `finish_reason`, `usage`
and `status`. Write the expected block from what the stream means, not from
what the SDK returns today. A new model family or a new stream quirk gets a
file. The SSE bodies are shared with aixplain-agents'
`tests/stream_replay/streams`, so copy a new one across.

## Fault injection (`tests/fault/`)

The `faulty` fixture starts local servers that answer from the same
recordings, puts a fault proxy in front of them, and points an `Aixplain`
client at the proxy. Use `FaultResponse` for server-side faults: stall after
headers, cut the body, close without a response, or delay. Use
`faulty.toxic(...)` for network faults: latency, bandwidth, timeout,
reset_peer, limit_data.

Assert what a user sees: the exception or status, the number of POSTs that
reached the server (billing), and the wall-clock bound. Do not assert that a
mock was called with `timeout=`.

Locally the fixture uses an in-process socket proxy. CI runs real toxiproxy
with `FAULT_INJECTION_REQUIRE=1`, so a missing toxiproxy fails the job instead
of passing it silently. To use toxiproxy locally, run
`docker run --rm --network host ghcr.io/shopify/toxiproxy:2.12.0` and export
`TOXIPROXY_URL=http://127.0.0.1:8474`.

## Security (`tests/security/`)

`test_canary_key.py` sends a canary key through every client flow and asserts
where it may appear: only the `x-api-key` header to a trusted origin. It must
never appear in URLs, bodies, logs (even with `AIXPLAIN_LOG_BODIES=1`),
errors, cross-origin redirects or the process environment.

A new place that stores, logs or sends data gets an assertion there.
`test_rlm_sandbox_secrets.py` drives the RLM sandbox guard (BUG-936).
`test_fixture_secrets.py` scans every recording for credential-shaped
values. pre-commit.yaml's gitleaks run covers the same files.

## Known failures are strict xfails

When a layer exposes a bug that is not fixed in the same PR, mark the test
`@pytest.mark.xfail(strict=True, reason="ENG-xxxx finding: ...")`. For a
stream file, set `known_failure`. The reason says what is wrong and where.
Once the bug is fixed, the test passes, strict mode turns that into a
failure, and that failure is the cue to delete the marker. Never `skip` a
known bug.

## A fix PR must include a test that fails on the pre-fix code

A test that passes with the fix reverted proves nothing about the fix.

* Write the test first. Run it on the unfixed code and see it fail on an
  assertion, not on an import of a name the fix adds.
* Reach the behaviour through an API that existed before the fix where you
  can. A test that imports the new helper fails on reverted code for the
  wrong reason. #1014's and BUG-936's tests are like this.
* `.github/workflows/revert-check.yaml` runs `.github/tools/fix_revert_check.py`
  on every PR whose title starts with `fix`, or that is labelled `bug` or
  `fix`. It reverts the PR's files under `aixplain/`, reruns the PR's new and
  changed tests, and posts a verdict:
  * `CATCHES` is the goal.
  * `CATCHES_ONLY_VIA_IMPORT` and `DOES_NOT_CATCH` mean the test does not
    observe the bug yet.

  The check only reports for now. It will block once its false-positive rate
  is known, by setting the repository variable `REVERT_CHECK_ENFORCE=true`.

Run it locally before opening the PR:

```bash
python .github/tools/fix_revert_check.py --base origin/development --head HEAD \
    --source-dir aixplain --package aixplain --python .venv/bin/python
```

The script drops every credential from the test environment. To check an
older revision that refuses to import without a key, add
`--env TEAM_API_KEY=dummy`.

## Checking that the layers still catch what they were built for

`.github/tools/backtest_layers.py` re-introduces the fixes catalogued in ENG-3782
on a scratch worktree of `HEAD`, one at a time, and records which tests
fail. Each layer also gets an unmutated baseline run, which must be green.
Run it after changing a layer's harness, on a committed tree:

```bash
python .github/tools/backtest_layers.py --all --markdown backtest.md
```
