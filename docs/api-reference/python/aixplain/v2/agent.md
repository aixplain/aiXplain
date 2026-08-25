---
sidebar_label: agent
title: aixplain.v2.agent
---

Agent module for aiXplain v2 SDK.

### ConversationMessage Objects

```python
class ConversationMessage(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L45)

Type definition for a conversation message in agent history.

**Attributes**:

- `role` - The role of the message sender, either &#x27;user&#x27; or &#x27;assistant&#x27;
- `content` - The text content of the message
- `attachments` - Optional attachments — hosted-URL/local-path strings or dicts
  with ``url`` or ``path`` (plus optional type/name/mimeType).
- `files` - Deprecated. Local file paths to upload — pass through ``attachments``.

#### validate\_history

```python
def validate_history(history: List[Dict[str, Any]]) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L62)

Validates conversation history for agent sessions.

This function ensures that the history is properly formatted for agent conversations,
with each message containing the required &#x27;role&#x27; and &#x27;content&#x27; fields and proper types.

**Arguments**:

- `history` - List of message dictionaries to validate
  

**Returns**:

- `bool` - True if validation passes
  

**Raises**:

- `ValueError` - If validation fails with detailed error messages
  

**Example**:

  &gt;&gt;&gt; history = [
  ...     \{&quot;role&quot;: &quot;user&quot;, &quot;content&quot;: &quot;Hello&quot;},
  ...     \{&quot;role&quot;: &quot;assistant&quot;, &quot;content&quot;: &quot;Hi there!&quot;}
  ... ]
  &gt;&gt;&gt; validate_history(history)  # Returns True

### OutputFormat Objects

```python
class OutputFormat(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L120)

Output format options for agent responses.

### ContextOverflowStrategy Objects

```python
class ContextOverflowStrategy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L128)

Strategy for condensing the working context when a run exceeds the model&#x27;s context window.

Context condensation shapes only the working context sent to the model on a given run. It does not modify Shared Memory or the stored session history — the complete session history is always retained.

**Attributes**:

- `TRUNCATE` - Default. Remove the oldest unprotected turns until the context fits.
- `SUMMARIZE` - Summarize older context into a shorter form the model can still use. Retains more of the conversation&#x27;s meaning than truncation, but adds latency and model cost.

**Notes**:

Available in SDK 0.2.46+ (use the current 0.2.47). Set it as the agent&#x27;s saved default (`agent.context_overflow_strategy`) or override it per run via the `execution_params` argument (`context_overflow_strategy`). Precedence, highest first: per-run override, then the saved agent setting, then the Agent Engine default (`truncate`).

### AgentRunParams Objects

```python
class AgentRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L230)

Parameters for running an agent.

**Attributes**:

- `session` - Conversation thread to run within. A
  :class:`~aixplain.v2.session.Session` instance or a session id
  string. Omit for a one-shot, stateless run. Replaces the removed
  ``via_session`` flag and id-only ``session_id``.
- `query` - The query to run
- `variables` - Variables to replace \{\{variable}} placeholders in instructions and description.
  The backend performs the actual substitution.
- `tasks` - List of tasks for the agent
- `prompt` - Custom prompt override
- `~aixplain.v2.session.Session`0 - Conversation history
- `~aixplain.v2.session.Session`1 - Execution parameters (maxTokens, etc.). Passing
  ``max_iterations`` here is deprecated; set ``agent.budget.max_iterations``
  instead. A deprecated value is folded into ``budget.max_iterations``
  (the agent&#x27;s budget wins on conflict) and the standalone key is not
  emitted.
- `~aixplain.v2.session.Session`8 - Criteria for evaluation
- `~aixplain.v2.session.Session`9 - Evolution parameters
- ``0 - Inspector configurations
- ``1 - Whether to run response generation. Defaults to False.
- ``2 - Multimodal attachments for the turn.
  Each entry is a hosted-URL/local-path string or a dict with ``url`` or
  ``path`` (plus optional ``type``/``name``/``mimeType``). Local paths are
  uploaded to aiXplain storage automatically.
- ``3 - Deprecated. Local file paths to upload — pass through ``attachments`` instead.
- ``6 - Display format - &quot;status&quot; (single line) or &quot;logs&quot; (timeline).
  If None (default), progress tracking is disabled.
- ``7 - Detail level - 1 (minimal), 2 (thoughts), 3 (full I/O)
- ``8 - Whether to truncate long text in progress display

### Budget Objects

```python
@dataclass_json

@dataclass
class Budget()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L285)

Budget caps governing an agent run (cost / duration / iterations).

Every :class:`Agent` owns a ``budget`` (defaulting to an empty ``Budget()``),
mutated in place via attribute access — mirroring ``model.inputs``::

    agent.budget.max_cost = 0.5
    agent.budget.max_iterations = 10

The same object serves two roles: ``agent.save()`` persists it as the agent&#x27;s
default budget, and ``agent.run(...)`` sends its current state as the run-time
budget (the backend merges the run-time budget field-by-field over the
persisted default). The Python API is snake_case; serialization produces the
agreed camelCase wire keys (``maxCost`` / ``maxDurationSeconds`` /
``maxIterations``). All fields are optional and ``None`` fields are dropped
from ``to_dict()``.

### AgentResponseData Objects

```python
@dataclass_json

@dataclass
class AgentResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L319)

Data structure for agent response.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L340)

Assemble the nested ``governance`` dict from the flat wire fields.

### AgentRunResult Objects

```python
@dataclass_json

@dataclass
class AgentRunResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L352)

Result from running an agent.

#### data

Override type from base class

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L362)

Promote diagnostic codes the backend nests under ``data``.

The poll body carries them at ``data.diagnosticErrorCodes`` (or only
inside ``executionStats`` on older builds), never top-level.

#### execution\_id

```python
@property
def execution_id() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L401)

Extract the execution ID from the poll URL or request_id.

The execution ID can be used with ``Agent.poll()`` and
``Agent.sync_poll()`` to resume polling a previously started run
without persisting the full URL.

**Returns**:

  The execution ID if available, None otherwise.

#### debug

```python
def debug(prompt: Optional[str] = None,
          execution_id: Optional[str] = None,
          **kwargs: Any) -> "DebugResult"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L421)

Debug this agent response using the Debugger meta-agent.

This is a convenience method for quickly analyzing agent responses
to identify issues, errors, or areas for improvement.

Note: This method requires the AgentRunResult to have been created
through an Aixplain client context. If you have a standalone result,
use the Debugger directly: aix.Debugger().debug_response(result)

**Arguments**:

- `prompt` - Optional custom prompt to guide the debugging analysis.
- `Examples` - &quot;Why did it take so long?&quot;, &quot;Focus on error handling&quot;
- `execution_id` - Optional execution ID (poll ID) for the run. If not provided,
  it will be extracted from the response&#x27;s request_id or poll URL.
  This allows the debugger to fetch additional logs and information.
- `**kwargs` - Additional parameters to pass to the debugger.
  

**Returns**:

- `DebugResult` - The debugging analysis result.
  

**Raises**:

- `ValueError` - If no client context is available for debugging.
  

**Example**:

  agent = aix.Agent.get(&quot;my_agent_id&quot;)
  response = agent.run(&quot;Hello!&quot;)
  debug_result = response.debug()  # Uses default prompt
  debug_result = response.debug(&quot;Why did it take so long?&quot;)  # Custom prompt
  debug_result = response.debug(execution_id=&quot;abc-123&quot;)  # With explicit ID
  print(debug_result.analysis)

### Task Objects

```python
@dataclass_json

@dataclass
class Task()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L474)

A task definition for agent workflows.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L482)

Initialize task dependencies after dataclass creation.

### Agent Objects

```python
@dataclass_json

@dataclass(repr=False)
class Agent(BaseResource, SearchResourceMixin[BaseSearchParams, "Agent"],
            GetResourceMixin[BaseGetParams,
                             "Agent"], DeleteResourceMixin[BaseDeleteParams,
                                                           "Agent"],
            RunnableResourceMixin[AgentRunParams, AgentRunResult])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L492)

Agent resource class.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L596)

Initialize agent after dataclass creation.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L682)

Keep ``self.budget`` a (never-None) ``Budget`` instance.

Assigning ``agent.budget`` a dict / ``Budget`` / ``None`` is coerced into
a ``Budget`` so attribute access (``agent.budget.max_cost = ...``) always
works and the invariant &quot;budget is never None&quot; holds (mirrors how
``Model.__setattr__`` coerces bulk ``inputs`` assignment). This runs for
the generated ``__init__`` assignment too, so the field is a ``Budget``
by the time ``__post_init__`` executes.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L723)

Mark the agent as deleted by setting status to DELETED and calling parent method.

#### before\_run

```python
def before_run(*args: Any,
               **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L788)

Hook called before running the agent to validate and prepare state.

#### on\_poll

```python
def on_poll(response: AgentRunResult,
            **kwargs: Unpack[AgentRunParams]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L806)

Hook called after each poll to update progress display.

**Arguments**:

- `response` - The poll response containing progress information
- `**kwargs` - Run parameters

#### after\_run

```python
def after_run(result: Union[AgentRunResult, Exception], *args: Any,
              **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L818)

Hook called after running the agent for result transformation.

#### run

```python
def run(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L921)

Run the agent with optional progress display.

**Arguments**:

- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `session` - Run within a conversation thread. Accepts a
  :class:`~aixplain.v2.session.Session` instance or a session id
  string. When supplied, the run routes through the session path:
  the user message is posted to
  ``POST /v1/sessions/\{id}/messages`` (carrying the session&#x27;s
  ``executionConfig`` plus any per-run execution overrides) and the
  triggered agent run is awaited. Omit ``session`` for a one-shot,
  stateless run over ``POST /v2/agents/\{id}/run``. There is no
  ``via_session`` flag and no id-only ``session_id`` — manage
  threads through ``aix.Session`` and pass them here.
- `query`8 - Display format - &quot;status&quot; or &quot;logs&quot;. If None (default),
  progress tracking is disabled.
- `query`9 - Detail level 1-3 (default: 1)
- `session`0 - Truncate long text (default: True)
- `session`1 - Additional run parameters
  

**Returns**:

- `session`2 - The result of the agent execution

#### run\_async

```python
def run_async(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L956)

Run the agent asynchronously.

**Arguments**:

- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `**kwargs` - Additional run parameters
  

**Returns**:

- `AgentRunResult` - The result of the agent execution. Use ``result.url``
  to poll for completion via ``sync_poll(result.url)`` or
  ``client.get(result.url)``. Do not construct
  ``/sdk/runs/\{execution_id}`` — that endpoint is not supported
  for agent runs.

#### poll

```python
def poll(poll_url: str) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1003)

Poll for the result of an asynchronous agent execution.

Unlike the base implementation, *poll_url* may be either a full URL
(as returned in ``AgentRunResult.url``) **or** a bare execution ID.
When an execution ID is provided the correct
``/sdk/agents/\{id}/result`` endpoint is used automatically, avoiding
the common mistake of calling the unsupported
``/sdk/runs/\{id}`` endpoint.

**Arguments**:

- `poll_url` - Full poll URL or execution ID.
  

**Returns**:

  AgentRunResult with current execution status.

#### sync\_poll

```python
def sync_poll(poll_url: str,
              **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1021)

Poll until an asynchronous agent execution completes.

Accepts either a full URL or a bare execution ID (see
:meth:`poll` for details).

**Arguments**:

- `poll_url` - Full poll URL or execution ID.
- `**kwargs` - Run parameters including ``timeout`` and ``wait_time``.
  

**Returns**:

  AgentRunResult with final execution status.

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1068)

Save the agent with dependency management.

This method extends the base save functionality to handle saving of dependent
child components before the agent itself is saved.

**Arguments**:

- `*args` - Positional arguments passed to parent save method.
- `save_subcomponents` - bool - If True, recursively save all unsaved child components (default: False)
- `as_draft` - bool - If True, save agent as draft status (default: False)
- `**kwargs` - Other attributes to set before saving
  

**Returns**:

- `Agent` - The saved agent instance
  

**Raises**:

- `ValueError` - If child components are not saved and save_subcomponents is False

#### before\_save

```python
def before_save(*args: Any, **kwargs: Any) -> Optional[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1270)

Callback to be called before the resource is saved.

Handles status transitions based on save type.

#### after\_duplicate

```python
def after_duplicate(result: Union["Agent", Exception],
                    **kwargs: Any) -> Optional["Agent"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1285)

Callback called after the agent is duplicated.

Sets the duplicated agent&#x27;s status to DRAFT.

#### duplicate

```python
@with_hooks
def duplicate(duplicate_subagents: bool = False,
              name: Optional[str] = None) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1295)

Duplicate this agent on the aiXplain platform (server-side).

Creates a server-side copy of this agent with a clean usage baseline.
The duplicate inherits the original&#x27;s ownership, team, and permissions
but resets all usage and cost metrics.

**Arguments**:

- `duplicate_subagents` - If True, recursively duplicates referenced subagents
  so the duplicate has independent copies. If False, the duplicate
  keeps references to the original subagents. Defaults to False.
- `name` - Custom name for the duplicate. If None, a unique name is
  auto-generated by the platform. Defaults to None.
  

**Returns**:

- `Agent` - The newly created duplicate agent.
  

**Raises**:

- `ResourceError` - If the duplication request fails.

#### search

```python
@classmethod
def search(cls: type["Agent"],
           query: Optional[str] = None,
           **kwargs: Unpack[BaseSearchParams]) -> "Page[Agent]"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1334)

Search agents with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (ownership, status, etc.)
  

**Returns**:

  Page of agents matching the search criteria

#### llm\_id

```python
@property
def llm_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1722)

Return main LLM id whether llm is a string or Model.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1730)

Build the payload for the save action.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[AgentRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1847)

Build the payload for the run action.

