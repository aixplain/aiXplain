# Migrating from aiXplain SDK v1 to v2

SDK v1 — the legacy factory API — is **deprecated and will be removed on February 1, 2027**. This guide maps every public v1 factory to its v2 equivalent, and says plainly where no equivalent exists yet.

- **Nothing is broken today.** Every legacy import path (`aixplain.modules`, `aixplain.factories`, `aixplain.enums`, `aixplain.decorators`, `aixplain.base`, `aixplain.processes`) still resolves to the same objects it always did. The only change is a one-time `DeprecationWarning`.
- **v2 is the default surface.** New work should target `from aixplain import Aixplain`. See the [README](README.md) and the [v2 API reference](https://docs.aixplain.com/api-reference/python/aixplain/v2/agent).
- **v1 documentation** remains at <https://docs.aixplain.com/1.0/>.

## The deprecation warning

Importing any v1 code emits one `aixplain._compat.AixplainV1DeprecationWarning` (a `DeprecationWarning` subclass) per process:

```text
'aixplain.factories' is part of the deprecated aiXplain SDK v1 and will be removed on
February 1, 2027 (2027-02-01). Migrate to the v2 API ('from aixplain import Aixplain').
Migration guide: https://github.com/aixplain/aiXplain/blob/main/MIGRATION.md.
Set AIXPLAIN_SUPPRESS_V1_DEPRECATION=1 to silence this notice.
```

It fires once for the whole v1 surface, not once per module — a single `import aixplain.modules` pulls in roughly 160 submodules, and v1 imports itself through the legacy paths.

### Finding your exposure

```bash
# Every legacy import in your codebase
grep -rnE '(from|import) +aixplain\.(modules|factories|enums|decorators|base|processes|v1)\b' .

# Or let Python tell you, with the notice promoted to an error
python -W error::DeprecationWarning -c 'import your_app'
```

### Silencing it

Three options, in order of preference:

```bash
export AIXPLAIN_SUPPRESS_V1_DEPRECATION=1          # the documented off switch
python -W ignore::DeprecationWarning your_app.py   # any -W/PYTHONWARNINGS setting also wins
```

```python
# or, scoped to your own process
import warnings
from aixplain._compat import AixplainV1DeprecationWarning
warnings.filterwarnings("ignore", category=AixplainV1DeprecationWarning)
```

A `filterwarnings` entry in your `pytest.ini` or `pyproject.toml` works too.

One ordering caveat: to make the notice visible at all, the SDK inserts a `default` filter for its own category while `aixplain` is being imported — but only when `sys.warnoptions` is empty, i.e. when you passed no `-W` and set no `PYTHONWARNINGS`. A bare `warnings.simplefilter("ignore")` issued *before* `import aixplain` is therefore overridden. Use the environment variable, use `-W`/`PYTHONWARNINGS`, or register your filter after the import — all three win.

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
| [`FileFactory`](#filefactory--aixplainv2upload_file) | `aixplain.v2.upload_file` / `FileUploader` | Direct |
| [`ScriptFactory`](#scriptfactory--aixutility) | `aix.Utility` | Shape change — custom code becomes a utility |
| [`AssetFactory`](#assetfactory) | — | Internal abstract base, never user-facing |
| [`IndexFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`PipelineFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`BenchmarkFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`CorpusFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`DataFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`DatasetFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`FinetuneFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |
| [`WalletFactory`](#no-v2-equivalent-yet) | **none yet** | Gap |

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
# v1 (deprecated)
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
| `AgentFactory.create_pipeline_tool(pipeline=...)` | No v2 equivalent — see [the gaps](#no-v2-equivalent-yet) |

Runs return typed objects in v2: read `result.data.output`, not `result["data"]`.

### `TeamAgentFactory` → `aix.Agent` with `subagents`

v2 has one agent type. A "team" is an agent that delegates to subagents, so `TeamAgentFactory` collapses into `aix.Agent`.

```python
# v1 (deprecated)
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
# v1 (deprecated)
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

`ModelFactory.create_utility_model(...)` becomes `aix.Utility(...)`. The model-onboarding helpers (`create_asset_repo`, `asset_repo_login`, `onboard_model`, `list_host_machines`, `list_gpus`, `deploy_huggingface_model`) have no v2 equivalent yet; use the console or keep the v1 call until they land.

### `ToolFactory` → `aix.Tool`

```python
# v1 (deprecated)
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
# v1 (deprecated)
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
# v1 (deprecated)
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
# v1 (deprecated)
from aixplain.factories import APIKeyFactory

key = APIKeyFactory.get("<access-key>")
keys = APIKeyFactory.list()
limits = APIKeyFactory.get_usage_limits()
```

```python
# v2
from aixplain import Aixplain

aix = Aixplain()

key = aix.APIKey.get_by_access_key("<access-key>")
keys = aix.APIKey.list()
limits = aix.APIKey.get_usage_limits()
```

### `FileFactory` → `aixplain.v2.upload_file`

```python
# v1 (deprecated)
from aixplain.factories import FileFactory

link = FileFactory.upload("/path/to/local.csv")
storage_type = FileFactory.check_storage_type("/path/to/local.csv")
```

```python
# v2
from aixplain.v2 import FileUploader, upload_file, validate_file_for_upload

link = upload_file("/path/to/local.csv")
validate_file_for_upload("/path/to/local.csv")
```

Use `FileUploader` directly when you need to target a specific backend or key.

### `ScriptFactory` → `aix.Utility`

`ScriptFactory.upload_script` uploaded a code file and returned an ID to wire in by hand. In v2, custom code is a first-class `Utility` resource.

```python
# v1 (deprecated)
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

## No v2 equivalent yet

These eight factories have **no v2 replacement today**. They remain fully supported in v1, and the removal date above is contingent on closing these gaps first — we will not remove a capability that has nowhere to go.

If you depend on any of them, keep using the v1 import and suppress the notice with `AIXPLAIN_SUPPRESS_V1_DEPRECATION=1` for now.

| v1 factory | What it covers | Notes |
| --- | --- | --- |
| `IndexFactory` | Vector indexes / RAG collections | No v2 surface. Keep `from aixplain.factories import IndexFactory`. |
| `PipelineFactory` | Legacy static pipelines | The v2 replacement is being designed as static-graph agents; see [`docs/rfcs/rfc-static-graph-agents.md`](docs/rfcs/rfc-static-graph-agents.md). |
| `BenchmarkFactory` | Benchmarks and benchmark jobs | v2 has `aix.Eval` for agent evaluation, which is not a replacement for model benchmarking. |
| `CorpusFactory` | Corpus assets | Data-asset onboarding has no v2 surface. |
| `DataFactory` | Individual data assets | Data-asset onboarding has no v2 surface. |
| `DatasetFactory` | Dataset assets | `aixplain.v2` has evaluation datasets, which are a different concept from v1 data assets. |
| `FinetuneFactory` | Fine-tuning jobs | No v2 surface. |
| `WalletFactory` | Wallet / credit balance | No v2 surface. |

## Enums, modules, and other legacy paths

Beyond the factories, three more legacy prefixes redirect into v1:

| Legacy import | v2 |
| --- | --- |
| `from aixplain.enums import Function, Supplier, ...` | `aix.Function`, `aix.Supplier`, … on the `Aixplain` instance, or `from aixplain.v2 import enums` |
| `from aixplain.modules import Agent, Model, ...` | `aix.Agent`, `aix.Model`, … — v2 resources replace the v1 domain objects |
| `from aixplain.decorators import ...`, `aixplain.base`, `aixplain.processes` | Internal helpers with no public v2 counterpart |

## Polling behaviour changes

Two polling defaults changed. Both bound a loop that was previously unbounded or
effectively unbounded; both are opt-out-able through the same parameter you
already pass.

### `Pipeline.run` / `Pipeline.poll` stop polling after 30 minutes

The default `timeout` on `aixplain.modules.pipeline.Pipeline.run()` (and the
private polling loop behind it) dropped from **20,000 seconds (5h 33m) to 1,800
seconds (30 minutes)**.

A pipeline that legitimately runs longer than 30 minutes will now stop being
polled and be reported as a failure, even though the run itself continues on the
platform. If you have such a pipeline, raise the budget explicitly:

```python
pipeline.run(data, timeout=20000.0)   # the previous default
```

The old default meant a pipeline that never completed pinned a thread for over
five hours; 30 minutes is the bound for the common case, and the parameter is
there for the rest.

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
