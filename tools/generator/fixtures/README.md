# Generator fixtures

Snapshots of the four backend catalog endpoints that `generate.py` renders from:

| File | Endpoint |
| ---- | -------- |
| `functions.json` | `GET {BACKEND_URL}/sdk/functions` (the `items` array) |
| `suppliers.json` | `GET {BACKEND_URL}/sdk/suppliers` |
| `languages.json` | `GET {BACKEND_URL}/sdk/languages` |
| `licenses.json` | `GET {BACKEND_URL}/sdk/licenses` |

## Why they are committed

`python generate.py render` reads only these files. That is what lets the `generator-drift` CI job
re-render the generated modules and compare them with the committed ones with **no credential and no
backend** — a drift check whose input moved under it would just be a flake generator, and putting
`TEAM_API_KEY` in an ordinary CI job is exactly what BUG-947 moved the functional suite away from.

## Provenance

`provenance.json`, written by `fetch` next to the fixtures, records the backend host, the capture
time and a SHA-256 digest of each fixture. `tests/unit/test_generator.py` asserts that the host is
production and that the digests match the committed files, so neither a refresh from the wrong
backend nor a hand edit can land without the provenance moving with it.

Production is not an arbitrary choice: supplier ids are environment-specific, and the committed
`Supplier` members carry the production ids (`google` is `1769` on production, `195` on dev and `212`
on test). A fixture captured against dev or test would silently rewrite every
`Supplier.*.value["id"]` in the shipped SDK. `fetch` therefore refuses any host other than
production unless `--allow-nonprod` is passed, and even then it records that host, so committing
such a snapshot fails the test.

## Refreshing them

```bash
BACKEND_URL=https://platform-api.aixplain.com AIXPLAIN_API_KEY=... python generate.py fetch
python generate.py render
```

`fetch` is the only networked step and is run by hand. It reads the repo-root `.env` (never a
parent directory's; importing the SDK also loads the working directory's `.env`, and the host and
key are resolved once, after that), requires `https` for `BACKEND_URL` like every other SDK request,
and refuses to run when `TEAM_API_KEY` and `AIXPLAIN_API_KEY` are both set but differ. It fetches
all four endpoints before writing any of them, so a failure part-way leaves the committed set
untouched rather than half-refreshed. It keeps each item in the order of the existing fixture and
appends new items at the end, because the backend does not return a stable order and a reshuffled
fixture buries the actual change under thousands of moved lines.

Review the regenerated modules as a diff before committing. **Additions are fine; a removed enum
member is a breaking API change** for every user holding a reference to it, and belongs in a
deliberate deprecation rather than in a data refresh.
