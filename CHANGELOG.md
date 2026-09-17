# Changelog

## 0.3.0

### Removed: SDK v1

SDK v1 — the legacy factory API — is gone. `aixplain/v1/` no longer ships, and the
`aixplain/_compat.py` redirects that made `aixplain.factories`, `aixplain.modules`,
`aixplain.enums`, `aixplain.decorators`, `aixplain.base` and `aixplain.processes`
resolve into it were removed with it. v2 is the only supported surface.

Importing a legacy path now raises a `ModuleNotFoundError` naming its v2
replacement, the release you can pin, and the guide — not a bare "No module named":

```text
'aixplain.factories' was part of aiXplain SDK v1, which was removed in 0.3.0.
Construct a client and use its resources:
    from aixplain import Aixplain
    aix = Aixplain()
  AgentFactory       -> aix.Agent
  ModelFactory       -> aix.Model
  ...
The last release that shipped v1 is 0.2.48; pin it with "pip install 'aiXplain==0.2.48'" if you need more time.
Migration guide: https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md
```

**The last release that contained v1 is `0.2.48`.** It stays on PyPI and stays
installable; code pinned to it keeps running unchanged.

Eight v1 factories — `IndexFactory`, `PipelineFactory`, `BenchmarkFactory`,
`CorpusFactory`, `DataFactory`, `DatasetFactory`, `FinetuneFactory`,
`WalletFactory` — had no v2 equivalent and were removed without one. If you depend
on any of them, stay on `0.2.48` and
[open an issue](https://github.com/aixplain/aiXplain/issues) naming it.

Also removed, because they existed only to serve v1:

- The `aixplain` console script (`aixplain list`, `aixplain onboard`, …), which
  wrapped the v1 model-onboarding factory. Use the web console.
- `aixplain.utils.file_utils`, `request_utils`, `asset_cache`, `cache_utils`,
  `llm_utils`, `evolve_utils`, `validation_utils` and `convert_datatype_utils`.
  `aixplain.utils.config`, `url_safety` and `user_info_utils` stay.
- `aixplain/v2/enums_include.py`, a re-export shim over the v1 enums that nothing
  imported, and the `generate.py` code generator that rendered it.

See [MIGRATION.md](MIGRATION.md) for the factory-by-factory map.
