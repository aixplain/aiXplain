# Migrating from aiXplain SDK v1 to v2

SDK v1 — the legacy factory API — **was removed in 0.3.0**. This guide maps every public v1 factory to its v2 equivalent, and says plainly where no equivalent exists.

- **v1 imports no longer resolve.** `aixplain.modules`, `aixplain.factories`, `aixplain.enums`, `aixplain.decorators`, `aixplain.base`, `aixplain.processes` and `aixplain.v1` were deleted. Importing one raises a `ModuleNotFoundError` naming the v2 replacement rather than a bare "No module named".
- **The last release that contained v1 is `0.2.48`.** It stays on PyPI and stays installable. Code pinned to it keeps running unchanged; upgrading past it requires v2.
- **v2 is the only supported surface.** Target `from aixplain import Aixplain`. See the [README](README.md) and the [v2 API reference](https://docs.aixplain.com/api-reference/python/aixplain/v2/agent).
- **v1 documentation** remains at <https://docs.aixplain.com/1.0/>.

## What you see now

```text
ModuleNotFoundError: 'aixplain.factories' was part of aiXplain SDK v1, which was removed in 0.3.0.
Construct a client and use its resources:
    from aixplain import Aixplain
    aix = Aixplain()
  AgentFactory       -> aix.Agent
  ModelFactory       -> aix.Model
  ...
The last release that shipped v1 is 0.2.48; pin it with "pip install 'aiXplain==0.2.48'" if you need more time.
Migration guide: https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md
```

### Finding your exposure

Before upgrading, find every legacy import:

```bash
grep -rnE '(from|import) +aixplain\.(modules|factories|enums|decorators|base|processes|v1)\b' .
```

Each hit maps to a row in the table below. If a hit lands in [the gaps](#no-v2-equivalent), stay on `0.2.48` until it is closed.

### If you are not ready

```bash
pip install 'aiXplain==0.2.48'
```

That release is unchanged and unaffected by the removal. It is a hold, not a fix: it receives no further releases, so treat it as a window to migrate in rather than a destination.


## `aixplain.aixplain_v2` is deprecated

The module-level `aixplain_v2` client is deprecated and will be removed in a future release. Construct a client explicitly instead:

```python
# deprecated
from aixplain import aixplain_v2
agent = aixplain_v2.Agent.get("...")

# use instead
from aixplain import Aixplain
aix = Aixplain()            # or Aixplain(api_key="...")
agent = aix.Agent.get("...")
```

It used to be built at import time with the failure swallowed, so a missing `TEAM_API_KEY` left the symbol bound to `None` and the first use failed with `AttributeError: 'NoneType' object has no attribute 'Agent'` rather than the actual cause. It is now constructed on first access and raises the real error (`API key is required. Pass api_key=... to Aixplain() or set TEAM_API_KEY or AIXPLAIN_API_KEY.`), and the first access emits a `DeprecationWarning`.

`from aixplain import aixplain_v2` still works. It is no longer part of `from aixplain import *`, so a star import no longer needs a credential.

## Factory map at a glance

| v1 factory | v2 equivalent | Status |
| --- | --- | --- |
| [`AgentFactory`](#agentfactory--aixagent) | `aix.Agent` | Direct |
| [`TeamAgentFactory`](#teamagentfactory--aixagent-with-subagents) | `aix.Agent(..., subagents=[...])` | Shape change — teams are agents in v2 |
| [`ModelFactory`](#modelfactory--aixmodel) | `aix.Model` | Direct |
| [`ToolFactory`](#toolfactory--aixtool) | `aix.Tool` | Direct |
| [`IntegrationFactory`](#integrationfactory--aixintegration) | `aix.Integration` | Direct |
| [`MetricFactory`](#metricfactory--aixmetric) | `aix.Metric` | Direct |
| [`APIKeyFactory`](#apikeyfactory--aixapikey) | `aix.APIKey` | Direct |
| [`FileFactory`](#filefactory--aixfile) | `aix.File` | Direct |
| [`ScriptFactory`](#scriptfactory--aixutility) | `aix.Utility` | Shape change — custom code becomes a utility |
| [`AssetFactory`](#assetfactory) | — | Internal abstract base, never user-facing |
| [`IndexFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`PipelineFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`BenchmarkFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`CorpusFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`DataFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`DatasetFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`FinetuneFactory`](#no-v2-equivalent) | **none** | Gap — see below |
| [`WalletFactory`](#no-v2-equivalent) | **none** | Gap — see below |

Across the board, v2 replaces module-level factory classmethods with resources hanging off an `Aixplain` instance. Construct one and reuse it:

```python
from aixplain import Aixplain

aix = Aixplain()  # reads AIXPLAIN_API_KEY from the environment
```

Unlike v1's global `TEAM_API_KEY`, an `Aixplain` instance carries its own credentials, so several can coexist in one process with different keys.

---

## Direct replacements

### `AgentFactory` → `aix.Agent`

Creation is construction plus `save()`; there is no separate `create` call.

```python
# v1 (removed in 0.3.0)
from aixplain.factories import AgentFactory

agent = AgentFactory.create(
    name="Research agent",
    description="Answers questions with concise web-grounded findings.",
    instructions="Use the search tool when needed.",
    tools=[...],
)
agent = AgentFactory.get("<agent-id>")
agents = AgentFactory.list()["results"]
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

agent = aix.Agent(
    name="Research agent",
    description="Answers questions with concise web-grounded findings.",
    instructions="Use the search tool when needed.",
    tools=[...],
)
agent.save()

agent = aix.Agent.get("<agent-id>")
agents = aix.Agent.search()
```

The v1 tool-builder classmethods are replaced by resources:

| v1 | v2 |
| --- | --- |
| `AgentFactory.create_model_tool(model=...)` | `aix.Model.get(...)`, passed directly in `tools=[...]` |
| `AgentFactory.create_custom_python_code_tool(code=...)` | `aix.Utility(code=...)` — see [`ScriptFactory`](#scriptfactory--aixutility) |
| `AgentFactory.create_python_interpreter_tool()` | `aix.Tool.get(...)` for the Python sandbox integration |
| `AgentFactory.create_pipeline_tool(pipeline=...)` | No v2 equivalent — see [the gaps](#no-v2-equivalent) |

Runs return typed objects in v2: read `result.data.output`, not `result["data"]`.

### `TeamAgentFactory` → `aix.Agent` with `subagents`

v2 has one agent type. A "team" is an agent that delegates to subagents, so `TeamAgentFactory` collapses into `aix.Agent`.

```python
# v1 (removed in 0.3.0)
from aixplain.factories import TeamAgentFactory

team = TeamAgentFactory.create(
    name="Research team",
    agents=[researcher, writer],
    description="Researches a topic and writes it up.",
)
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

team = aix.Agent(
    name="Research team",
    instructions="Research the topic and write it up.",
    subagents=[researcher, writer],
)
team.save(save_subcomponents=True)
```

Note `agents=` becomes `subagents=`, and `save(save_subcomponents=True)` persists the subagents along with the team.

### `ModelFactory` → `aix.Model`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import ModelFactory

model = ModelFactory.get("6414bd3cd09663e9225130e8")
models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

model = aix.Model.get("6414bd3cd09663e9225130e8")
models = aix.Model.search(function=aix.Function.TEXT_GENERATION)
```

`ModelFactory.create_utility_model(...)` becomes `aix.Utility(...)`. The model-onboarding helpers (`create_asset_repo`, `asset_repo_login`, `onboard_model`, `list_host_machines`, `list_gpus`, `deploy_huggingface_model`) have no v2 equivalent; they went with v1, along with the `aixplain` console script that exposed them. Use the web console, or stay on `0.2.48`.

### `ToolFactory` → `aix.Tool`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import ToolFactory

tool = ToolFactory.create(integration=..., name="My Slack tool")
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

tool = aix.Tool.get("tavily/tavily-web-search/tavily")
tool.allowed_actions = ["search"]
```

Per-action inputs are set through the actions object — `tool.actions.<action>.inputs.<name> = value`. Assigning to the tool directly (`tool.<name> = value`) does nothing.

### `IntegrationFactory` → `aix.Integration`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import IntegrationFactory

integration = IntegrationFactory.get("<integration-id>")
integrations = IntegrationFactory.list()
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

integration = aix.Integration.get("<integration-id>")
integrations = aix.Integration.search()
actions = integration.list_actions()
```

### `MetricFactory` → `aix.Metric`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import MetricFactory

metric = MetricFactory.get("<metric-id>")
metrics = MetricFactory.list(model_id="<model-id>")["results"]
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

metric = aix.Metric.get("<metric-id>")
metrics = aix.Metric.search()
```

### `APIKeyFactory` → `aix.APIKey`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import APIKeyFactory

key = APIKeyFactory.get("<access-key>")
keys = APIKeyFactory.list()
limits = APIKeyFactory.get_usage_limits()
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

key = aix.APIKey.get("<access-key>")   # also takes a key ID or a key name
keys = aix.APIKey.list()
limits = aix.APIKey.get_usage_limits()
```

`APIKeyFactory.get` took a key value; `aix.APIKey.get` takes a key ID, a key value **or** a key
name, so the rename needs no other change. `get_by_access_key` still exists for the key-value form
alone. Both match the full key value, not just its first and last four characters.

Rate limits take plain dicts on the user-facing field names. All four dimensions are still sent on
every write, with `0` for any you leave out — the backend does not yet accept a partial payload:

```python
key.asset_limits = [{"model": "openai/gpt-5", "token_per_minute": 10_000, "token_type": "output"}]
key.save()
```

`APIKeyLimits` and `TokenType` are unchanged and now import from the package root
(`from aixplain import APIKeyLimits, TokenType`).

### `FileFactory` → `aix.File`

```python
# v1 (removed in 0.3.0)
from aixplain.factories import FileFactory

link = FileFactory.upload("/path/to/local.csv")
storage_type = FileFactory.check_storage_type("/path/to/local.csv")
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

file = aix.File.create_from_file("/path/to/local.csv")
file.save()
link = file.source          # the uploaded link
```

`aix.File` is the resource: it also lists, downloads, and handles folders
(`aix.File.search()`, `file.download(dest)`, `aix.File.get(id)`).

For a one-line upload that just returns a link, `upload_file` is still exported
from the package root, and `FileUploader` is there when you need to target a
specific backend or key:

```python
from aixplain import upload_file, validate_file_for_upload

link = upload_file("/path/to/local.csv")
validate_file_for_upload("/path/to/local.csv")
```

### `ScriptFactory` → `aix.Utility`

`ScriptFactory.upload_script` uploaded a code file and returned an ID to wire in by hand. In v2, custom code is a first-class `Utility` resource.

```python
# v1 (removed in 0.3.0)
from aixplain.factories.script_factory import ScriptFactory

file_id, metadata = ScriptFactory.upload_script("/path/to/script.py")
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

utility = aix.Utility(name="add", code=add)
utility.save()
```

`ScriptFactory` was never exported from `aixplain.factories`; it was reachable only as `aixplain.factories.script_factory.ScriptFactory`.

### `AssetFactory`

An internal abstract base class that other v1 factories inherit `get` from. It has no v2 counterpart and never appeared in user code — nothing to migrate.

---

## No v2 equivalent

These eight factories have **no v2 replacement**, and the removal took them with it. There is no v2 spelling to port them to.

If you depend on any of them, stay on `0.2.48` (`pip install 'aiXplain==0.2.48'`) and [open an issue](https://github.com/aixplain/aiXplain/issues) saying which one — that is what prioritises the replacement.

| v1 factory | What it covered | Notes |
| --- | --- | --- |
| `IndexFactory` | Vector indexes / RAG collections | No v2 surface. |
| `PipelineFactory` | Legacy static pipelines | The v2 replacement is being designed as static-graph agents; see [`docs/rfcs/rfc-static-graph-agents.md`](docs/rfcs/rfc-static-graph-agents.md). |
| `BenchmarkFactory` | Benchmarks and benchmark jobs | v2 has `aix.Eval` for agent evaluation, which is not a replacement for model benchmarking. |
| `CorpusFactory` | Corpus assets | Data-asset onboarding has no v2 surface. |
| `DataFactory` | Individual data assets | Data-asset onboarding has no v2 surface. |
| `DatasetFactory` | Dataset assets | `aixplain.v2` has evaluation datasets, which are a different concept from v1 data assets. |
| `FinetuneFactory` | Fine-tuning jobs | No v2 surface. |
| `WalletFactory` | Wallet / credit balance | No v2 surface. |

## Enums, modules, and other legacy paths

Beyond the factories, four more legacy prefixes were removed:

| Legacy import | v2 |
| --- | --- |
| `from aixplain.enums import Function, Supplier, ...` | `from aixplain import Function, Supplier, ...`, or `aix.Function` / `aix.Supplier` on the client |
| `from aixplain.modules import Agent, Model, ...` | `aix.Agent`, `aix.Model`, … — v2 resources replace the v1 domain objects |
| `from aixplain.decorators import ...`, `aixplain.base` | Internal helpers with no public v2 counterpart |
| `from aixplain.processes import ...` | v1 data onboarding; no v2 counterpart |

## Polling behaviour changes

### `AgentProgressTracker.stream_progress` is bounded and raises on expiry

`stream_progress` used to be a `while True` loop with no `timeout` parameter at
all. It now takes `timeout` (default **300 seconds**) and raises
`TimeoutError` when that budget expires with the run still non-terminal.

This matches `sync_poll`, which has always raised `TimeoutError` in the same
situation — the two polling surfaces previously disagreed about whether an
expired budget was a result or an error.

```python
# previous behaviour: poll forever
tracker.stream_progress(url, timeout=None)

# a longer budget
tracker.stream_progress(url, timeout=1800)

# or handle the expiry
try:
    response = tracker.stream_progress(url)
except TimeoutError:
    ...
```

A terminal status (`SUCCESS`, `FAILED`, `ABORTED`, `CANCELLED`, `ERROR`) and the
`max_polls` cap still *return* the response as before; only the wall-clock
deadline raises.
## v2 behavior notes

### `search()` never reports more records than it returns

`search()` (and the `list()` wrappers built on it) used to log and drop any
record the SDK could not deserialize while `Page.total` still counted it, so
`len(page.results) < page.total` was a normal state and bulk loops skipped rows
with no error.

Records the SDK cannot model — a new backend enum value, say — are still
skipped rather than failing the whole listing, but the count no longer lies:

```python
page = aix.Model.search()

page.total    # never counts the records that were skipped
page.skipped  # how many were skipped on this page
```

Every skip is logged at `WARNING` with the reason. If you want the
`get()`-like contract instead, where any unparseable record raises
`ResourceError`, opt in per call with `aix.Model.search(strict=True)`, or set
`PAGINATE_STRICT = True` on a resource class whose records must all parse; a
per-call `strict=` always wins. `strict` is a client-side option and is never
sent to the backend.

A response that carries no readable item list at all — a renamed envelope, or
an error body served with HTTP 200 — always raises `ResourceError`, because
returning it as an empty page would be indistinguishable from a search that
genuinely matched nothing. A present-but-empty (or `null`) item list is still a
normal empty page.

### `save()` on a deleted resource always raises `ResourceError`

The guard that stops a deleted resource from being re-created raised
`ValidationError` from `Agent.save()` and `File.save()` but `ResourceError`
from every other resource's `save()`. Both derive from `AixplainV2Error`, so
`except ResourceError` around a save caught only some of the paths. All of them
now raise `ResourceError`.

### A streamed run only reports `SUCCESS` when it finished

`ModelResponseStreamer.status` used to become `SUCCESS` as soon as the
connection ended, so an error event mid-generation, or a stream cut before its
`[DONE]` marker, handed you a truncated answer that claimed to be complete. It
now stays `FAILED` unless the stream terminated cleanly (a `[DONE]` marker, a
terminal `finish_reason`, or a terminal `status` envelope), and an error event
yields one final chunk carrying the reason:

```python
with model.run_stream(text="Explain LLMs") as stream:
    for chunk in stream:
        print(chunk.data, end="", flush=True)

if stream.status != aix.ResponseStatus.SUCCESS:
    ...  # the text above is partial
```

Iteration itself does not raise, so existing `for chunk in stream` loops keep
working — but check `stream.status` (or `chunk.error_message`) before treating
the concatenated text as a full answer.

### `run(stream=True)` works even when the model record omits the flag

A backend record that does not report `supportsStreaming` leaves
`model.supports_streaming` at `None`, and such a model still takes the
streaming path. If it answers with a complete JSON body rather than an SSE
stream, the streamer detects that and yields the response as a single
`SUCCESS` chunk, instead of feeding the JSON text to the SSE parser and ending
at `FAILED`. Only an explicit `supports_streaming is False` refuses to stream.

### A polled falsy result keeps its value and type

`poll()` coerced any falsy `data` to `{}`, so a classifier that legitimately
answers `0`, or a model whose correct answer is `""`, came back as `{}` — and
`result.data.strip()` raised `AttributeError`. Falsy-but-present payloads
(`""`, `0`, `False`, `[]`) now pass through unchanged, matching what the same
model returns on the synchronous path. A genuinely absent (or `null`) `data`
still arrives as `{}`.

## Getting help

- Open an issue at <https://github.com/aixplain/aiXplain/issues> — especially if a gap above blocks you; that feedback shapes the removal timeline.
- Join the community on [Discord](https://discord.gg/aixplain).
