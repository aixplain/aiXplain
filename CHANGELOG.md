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

### Added: API key limits as plain data

`asset_limits` and `global_limits` take dicts on the user-facing field names, so
configuring a key no longer depends on the SDK's module layout:

```python
key = aix.APIKey.get("Production")     # a key ID, a key value, or a name
key.asset_limits = [{"model": "openai/gpt-5", "token_per_minute": 10_000, "token_type": "output"}]
key.save()
```

The dict is typed as `APIKeyLimitsDict`, so a misspelled field is a type error;
at runtime an unknown key raises and names the accepted fields, rather than
being dropped (which used to mean "no limit"). `token_type` takes `"input"`,
`"output"` or `"total"` as well as `TokenType`. Reading limits back still gives
`APIKeyLimits` objects.

`APIKeyLimits` and `TokenType` remain the internal representation, behave exactly
as before, and now import from the package root:
`from aixplain import APIKeyLimits, TokenType`.

Two correctness fixes ride along:

- **An unset limit is no longer a zero.** Every dimension defaults to `None` and
  is left out of the save payload, so setting `token_per_minute` alone leaves the
  other three unrestricted. Previously all four were sent, with `0` for the ones
  the caller never mentioned — which silently blocked them if the backend reads
  `0` as blocked. A deliberate `0` is still sent as `0`.
- **Key values are matched in full.** `get_by_access_key()` compared only the
  first and last four characters, so two keys sharing both resolved to whichever
  the backend listed first, and limits were written to a key the caller never
  named. Both it and `get()` now compare the whole value; if the backend returns
  masked keys and more than one is consistent with the value, they raise instead
  of guessing.

`APIKey.get()` resolves a key ID, a key value or a name — v1's `APIKeyFactory.get`
took a key value and v2's inherited `get` took an ID, so a renamed call used to
fail with "not found". An argument matching none of the three now says so.

### Added: plain data in place of imports, across v2

Every v2 enum and non-resource dataclass was audited and classified as **input**,
**output** or **internal**; the classification is recorded in
[docs/v2-plain-data.md](docs/v2-plain-data.md) so the next person does not repeat
it. Input types now accept plain data; output and internal types are unchanged
and still return objects.

Config structs take a dict on their user-facing field names, typed as a
`TypedDict`, with an unknown key raising an error naming the accepted fields:

```python
session = aix.Session(
    agent=agent,
    execution_config={"execution_params": {"output_format": "json"}, "criteria": "be terse"},
)
agent.budget = {"max_cost": 0.5, "max_iterations": 10}
agent.tasks = [{"name": "collect", "instructions": "...", "expected_output": "..."}]
trigger.configuration = {"type": "recurring", "time": "09:00", "repeat": {"every": 2, "unit": "hour"}}
```

covering `ExecutionConfig`, `Budget`, `Task`, `TriggerConfiguration`,
`TriggerRepeatRule` and `UtilityModelInput` (plus `APIKeyLimits`, above).

Input enums accept their string values — `agent.context_overflow_strategy =
"summarize"` — and each has a `Literal` alias (`ContextOverflowStrategyValue`,
`PrivacyValue`, `SupplierValue`, …) so a type checker accepts the string and
rejects a typo. These enums already subclassed `str`, so only the annotation was
missing.

**Everything importable is importable from `aixplain`, with no version segment.**
`aixplain/__init__.py` re-exports the whole `aixplain.v2` surface, so
`from aixplain import Budget, Privacy, ExecutionConfig` works. Existing imports
from `aixplain.v2` are unchanged, and so is every class and enum behind them.

Two fixes fall out of the audit:

- `Agent(tasks=[Task(...)])` raised `AttributeError` — the constructor assumed
  every task was a dict and called `Task.from_dict` on it.
- A misspelled key in a `budget` or `execution_config` dict was silently dropped,
  so `{"max_iteration": 10}` meant "no cap" rather than an error.

### Breaking, beyond the v1 removal

- **`APIKeyLimits` defaults changed from `0` to `None`.** This is a *read*-path
  break as well as a write one: `limits.token_per_minute > 0` now raises
  `TypeError` on an unset dimension. Compare against `None` first, or use
  `(limits.token_per_minute or 0)`.
- **`aixplain.TimeoutError` now also subclasses `builtins.TimeoutError`.** It is
  re-exported from the package root, so `from aixplain import *` rebinds the
  name; inheriting both means the name catches strictly more than before, never
  less. Code that distinguishes the two with `type(e) is TimeoutError` is
  unaffected; code relying on `issubclass(aixplain.TimeoutError, OSError)` being
  `False` is not.
