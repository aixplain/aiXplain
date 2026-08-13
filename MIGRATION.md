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

## Getting help

- Open an issue at <https://github.com/aixplain/aiXplain/issues> — especially if a gap above blocks you; that feedback shapes the removal timeline.
- Join the community on [Discord](https://discord.gg/aixplain).
