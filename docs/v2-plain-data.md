# Plain data in `aixplain/v2`

**Written for: SDK maintainers.** This is the recorded outcome of the PROD-2921
audit. It exists so the next person does not repeat it.

## The rule

> Anything a caller has to construct or pass in accepts plain data.
> Anything that only ever comes back from the SDK stays an object.

Concretely, for an **input** type:

- a config dataclass is paired with a `TypedDict` on the **user-facing field
  names**, and accepts a dict anywhere it accepts an instance;
- an unknown key **raises**, naming the accepted fields — it is not dropped;
- an enum is paired with a `Literal` alias named `<Enum>Value`, and accepts its
  string values.

**Output** and **internal** types are left alone: they still return objects, and
nothing about them changed.

Everything still importable is importable from `aixplain` directly, with no
version segment — `aixplain/__init__.py` re-exports `aixplain.v2.__all__`.

## Why a `TypedDict` and not just `Dict[str, Any]`

The point of taking a dict is that the caller needs no import. The point of
typing it is that they still get autocomplete and a type error on a typo. A
`TypedDict` gives both; `Dict[str, Any]` gives neither, and a misspelled key then
has to be caught at runtime by the writer of the call rather than by their
editor. `ConversationMessage` (`aixplain/v2/agent.py`) was the pattern already in
the repo; the rest follows it.

The runtime check is not redundant with the type checker: plenty of callers are
agents, notebooks, or scripts nobody type-checks.

**Totality mirrors the dataclass.** A `TypedDict` is `total=False` only when every
field of the struct it describes has a default. `TaskDict` and
`UtilityModelInputDict` are `total=True` with `NotRequired` on the fields that do
default, because `Task` and `UtilityModelInput` genuinely require the rest. A
`TypedDict` that disagrees with its dataclass in either direction is the defect:
it either accepts a dict the runtime rejects, or rejects one the runtime accepts.

**Strictness is for input only.** Rejecting an unknown key is right for what a
caller writes and wrong for what the backend sends: a field added to a backend
object must not break reads of data the SDK only ever passes through. Most
structs get this for free, because `dataclasses_json` decodes them before any
coercion runs. `Budget` does not — `ExecutionConfig.budget` is typed `Any`, so the
raw wire dict survives to `__post_init__` — so `Agent._coerce_budget` takes a
`strict` flag that is **off by default** and turned on only by the two entry
points that know they hold caller input (`Agent.__setattr__`,
`ExecutionConfig.coerce`).

## Enums

`TokenType` is a plain `Enum`; every other enum in `v2` subclasses `str`, so the
string form already worked at runtime and only the *annotation* was missing.

An alias only earns its place by being **attached** to something: the runtime
already accepted the string, so the annotation is the entire point. Five have no
annotation site yet, because the SDK exports the enum but never takes it as a
typed parameter — `AttachmentTypeValue` and `StorageTypeValue` (both inferred,
never passed), `AuthenticationSchemeValue` (integration connect takes untyped
`**kwargs`), `LicenseValue` (documented but not a parameter) and
`SplittingOptionsValue` (index chunking has no v2 surface). They are listed in
`UNATTACHED_ALIASES` in the test module, so the gap stays a decision rather than
an oversight, and the rest are guarded by
`test_literal_alias_is_used_in_an_annotation`.

| Enum | Class | Notes |
| --- | --- | --- |
| `AssetStatus` | input + output | `agent.status`, and a search filter. `AssetStatusValue`. |
| `AttachmentType` | input | Session message attachments. `AttachmentTypeValue`. |
| `AuthenticationScheme` | input | Integration connect. `AuthenticationSchemeValue`. |
| `ContextOverflowStrategy` | input | `agent.context_overflow_strategy`. `ContextOverflowStrategyValue`. |
| `DataType` | input | `UtilityModelInput.type`. `DataTypeValue`. |
| `FileType` | input | `File.file_type`. `FileTypeValue`. |
| `Function` | input | Model/tool search filter. `FunctionValue`. |
| `IssueSeverity` | input | `aix.issue.report(severity=...)`. `IssueSeverityValue`. |
| `Language` | input | Search filter. `LanguageValue`. |
| `License` | input | Asset licence. `LicenseValue`. |
| `OutputFormat` | input | `agent.output_format`. `OutputFormatValue`. |
| `OwnershipType` | input | Search filter. `OwnershipTypeValue`. |
| `Privacy` | input | `File.privacy`. `PrivacyValue`. |
| `ProgressFormat` | input | `agent.run(progress_format=...)`. `ProgressFormatValue`. |
| `SortBy`, `SortOrder` | input | Search params. `SortByValue`, `SortOrderValue`. |
| `SplittingOptions` | input | Index chunking. `SplittingOptionsValue`. |
| `StorageType` | input | File storage. `StorageTypeValue`. |
| `Supplier` | input | Search filter. `SupplierValue`. |
| `TokenType` | input | API key limits (PROD-2917). `TokenTypeValue`. |
| `OnboardStatus` | output | Backend-reported onboarding progress. |
| `ResponseStatus` | output | Run result status. |
| `RunStatus` | output | Session run status. |
| `SessionStatus` | output | Session status. |
| `CodeInterpreterModel` | internal | Exported; no call site in the SDK. |
| `ErrorHandler` | internal | Exported; no call site in the SDK. |
| `EvolveType` | internal | Exported; no call site in the SDK. |
| `FileContentType` | internal | Exported; no call site in the SDK. |
| `FunctionType` | internal | Exported; no call site in the SDK. |
| `MessageRole` | internal | Exported; `SessionMessage.role` is a plain `str`. |
| `Reaction` | internal | Exported; the reaction field is a plain `str`. |

The six **internal** enums are exported but referenced nowhere in `aixplain/v2`.
They are left as they are rather than given an alias: an alias is another thing
to keep in sync, and nothing passes these in today. If a call site appears,
promote the enum to *input* here and add its alias.

## Dataclasses

### Input — take a dict

| Struct | Dict form | Where it is accepted |
| --- | --- | --- |
| `APIKeyLimits` | `APIKeyLimitsDict` | `key.global_limits`, `key.asset_limits[*]` (PROD-2917) |
| `Budget` | `BudgetDict` | `agent.budget`, `ExecutionConfig.budget` |
| `ExecutionConfig` | `ExecutionConfigDict` | `aix.Session(execution_config=...)` |
| `Task` | `TaskDict` | `agent.tasks[*]` |
| `TriggerConfiguration` | `TriggerConfigurationDict` | `trigger.configuration` |
| `TriggerRepeatRule` | `TriggerRepeatRuleDict` | `TriggerConfiguration.repeat` |
| `UtilityModelInput` | `UtilityModelInputDict` | *no consumer* — `aix.Utility` was removed in 0.3.0. Both types are still exported and still pass the drift guards; whether they stay is ENG-3720 |
| `SessionMessageAttachment` | — | Already accepts a plain dict or a URL string through `Session.add_message(attachments=...)` |

Every one of these coerces in `__setattr__` where a caller can assign the field
after construction — `Agent.budget`, `Agent.tasks`, `Session.execution_config`,
`Trigger.configuration`, `TriggerConfiguration.repeat`, `APIKey.global_limits`,
`APIKey.asset_limits`, `APIKeyLimits.token_type`, `UtilityModelInput.type`.
Coercing only in `__post_init__` is a bug, and a quiet one: the assignment path
skips validation, and `dataclasses_json` serializes an unrecognised dict
*untouched*, so the user-facing field names reach the backend instead of the wire
names.

`aixplain/v2/plain_data.py` holds the shared coercion (`coerce_struct`,
`coerce_struct_list`). It reads the accepted field names off the dataclass, so
adding a field needs no second edit.

### Output — returned, never passed

`AgentResponseData`, `AgentRunResult`, `AgentEvaluationResultsChatbot`,
`AgentEvaluationRow`, `AgentEvaluationRun`, `APIKeyUsageLimit`, `Artifact`,
`BaseResult`, `DebugResult`, `DeleteResult`, `Detail`, `Experiment`,
`ExperimentRun`, `ExperimentRunDiff`, `ExperimentRunDiffCase`,
`IntegrationResult`, `Message`, `ModelResult`, `MetricResponse`, `Parameter`,
`Pricing`, `Result`, `RLMResult`, `SessionMessage`, `StreamChunk`, `ToolResult`,
`Usage`, `VendorInfo`, `Version`.

`ActionInputSpec`, `ActionSpec`, `ToolId` and `TriggerTypeSpec` describe what an
integration offers; they are read off a fetched `Integration`, never constructed.

### Input, but constructed through a resource

`Dataset` and `EvalCase` (`aixplain/v2/agent_evaluator.py`) are caller-supplied,
but evaluators are pending reimplementation and are out of scope for PROD-2921.
So are the inspector structs (`_ActionConfig`, `_Judge`) and `Inspector` itself.

### Internal

`_RoleSpec`, `AgentResponseDataFields`, `ActionMixin`, `BaseResource`.

### Resources

The 15 resource classes bound on an `Aixplain` client (`Agent`, `Model`, `Tool`,
`Skill`, `Utility`, `File`, `Trigger`, `Session`, `APIKey`, `Integration`,
`Inspector`, `Debugger`, `RLM`, `Metric`, `Resource`) are not config structs.
They are constructed through the client and are out of scope for this rule.

## Keeping this honest

`tests/unit/v2/test_plain_data_inputs.py` asserts:

- every `<Enum>Value` alias lists exactly the values of the enum it names, so
  adding a member without extending the alias fails there rather than in a
  caller's editor;
- every input `TypedDict` declares exactly the fields of the dataclass it
  describes, so the type checker and the runtime cannot disagree;
- `aixplain.__all__` matches `aixplain.v2.__all__`, and every name in it
  resolves;
- each `Literal` alias is referenced by an annotation, not merely exported;
- `TimeoutError` is the only exported name that shadows a builtin, and it
  subclasses the builtin it shadows, so `except TimeoutError:` after
  `from aixplain import *` still catches socket and asyncio timeouts. A new
  collision fails the guard rather than silently narrowing an `except` clause.

If you add an enum or a non-resource dataclass to `aixplain/v2`, add a row above.
