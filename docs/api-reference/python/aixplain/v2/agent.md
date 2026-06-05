---
sidebar_label: agent
title: aixplain.v2.agent
---

Agent module for aiXplain v2 SDK.

### ConversationMessage Objects

```python
class ConversationMessage(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L37)

Type definition for a conversation message in agent history.

**Attributes**:

- `role` - The role of the message sender, either &#x27;user&#x27; or &#x27;assistant&#x27;
- `content` - The text content of the message

#### validate\_history

```python
def validate_history(history: List[Dict[str, Any]]) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L49)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L107)

Output format options for agent responses.

### ContextOverflowStrategy Objects

```python
class ContextOverflowStrategy(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L115)

Strategy applied when input messages exceed the model&#x27;s context window.

**Attributes**:

- `TRUNCATE` - Remove the oldest chat-history messages until the context fits.
- `SUMMARIZE` - Replace the full chat history with an LLM-generated summary.

### AgentRunParams Objects

```python
class AgentRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L127)

Parameters for running an agent.

**Attributes**:

- `session_id` - Session ID for conversation continuity
- `query` - The query to run
- `variables` - Variables to replace \{\{variable}} placeholders in instructions and description.
  The backend performs the actual substitution.
- `allow_history_and_session_id` - Allow both history and session ID
- `tasks` - List of tasks for the agent
- `prompt` - Custom prompt override
- `history` - Conversation history
- `execution_params` - Execution parameters (maxTokens, etc.)
- `criteria` - Criteria for evaluation
- `evolve` - Evolution parameters
- `query`0 - Inspector configurations
- `query`1 - Whether to run response generation. Defaults to False.
- `query`2 - Display format - &quot;status&quot; (single line) or &quot;logs&quot; (timeline).
  If None (default), progress tracking is disabled.
- `query`3 - Detail level - 1 (minimal), 2 (thoughts), 3 (full I/O)
- `query`4 - Whether to truncate long text in progress display

### AgentResponseData Objects

```python
@dataclass_json

@dataclass
class AgentResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L169)

Data structure for agent response.

### AgentRunResult Objects

```python
@dataclass_json

@dataclass
class AgentRunResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L182)

Result from running an agent.

#### data

Override type from base class

#### execution\_id

```python
@property
def execution_id() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L201)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L221)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L274)

A task definition for agent workflows.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L282)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L292)

Agent resource class.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L369)

Initialize agent after dataclass creation.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L422)

Mark the agent as deleted by setting status to DELETED and calling parent method.

#### before\_run

```python
def before_run(*args: Any,
               **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L429)

Hook called before running the agent to validate and prepare state.

#### on\_poll

```python
def on_poll(response: AgentRunResult,
            **kwargs: Unpack[AgentRunParams]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L470)

Hook called after each poll to update progress display.

**Arguments**:

- `response` - The poll response containing progress information
- `**kwargs` - Run parameters

#### after\_run

```python
def after_run(result: Union[AgentRunResult, Exception], *args: Any,
              **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L482)

Hook called after running the agent for result transformation.

#### run

```python
def run(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L517)

Run the agent with optional progress display.

**Arguments**:

- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `progress_format` - Display format - &quot;status&quot; or &quot;logs&quot;. If None (default),
  progress tracking is disabled.
- `progress_verbosity` - Detail level 1-3 (default: 1)
- `progress_truncate` - Truncate long text (default: True)
- `**kwargs` - Additional run parameters
  

**Returns**:

- `AgentRunResult` - The result of the agent execution

#### run\_async

```python
def run_async(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L538)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L579)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L597)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L639)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L755)

Callback to be called before the resource is saved.

Handles status transitions based on save type.

#### after\_duplicate

```python
def after_duplicate(result: Union["Agent", Exception],
                    **kwargs: Any) -> Optional["Agent"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L770)

Callback called after the agent is duplicated.

Sets the duplicated agent&#x27;s status to DRAFT.

#### duplicate

```python
@with_hooks
def duplicate(duplicate_subagents: bool = False,
              name: Optional[str] = None) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L780)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L819)

Search agents with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (ownership, status, etc.)
  

**Returns**:

  Page of agents matching the search criteria

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L879)

Build the payload for the save action.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[AgentRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L972)

Build the payload for the run action.

#### generate\_session\_id

```python
def generate_session_id(
        history: Optional[List[ConversationMessage]] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L1050)

Generate a unique session ID for agent conversations.

Creates a unique session identifier based on the agent ID and current timestamp.
If conversation history is provided, it attempts to initialize the session on the
server to enable context-aware conversations.

**Arguments**:

- `history` - Previous conversation history. Each message should contain
  &#x27;role&#x27; (either &#x27;user&#x27; or &#x27;assistant&#x27;) and &#x27;content&#x27; keys.
  Defaults to None.
  

**Returns**:

- `str` - A unique session identifier in the format &quot;\{agent_id}_\{timestamp}&quot;.
  

**Raises**:

- `ValueError` - If the history format is invalid.
  

**Example**:

  &gt;&gt;&gt; agent = Agent.get(&quot;my_agent_id&quot;)
  &gt;&gt;&gt; session_id = agent.generate_session_id()
  &gt;&gt;&gt; # Or with history
  &gt;&gt;&gt; history = [
  ...     \{&quot;role&quot;: &quot;user&quot;, &quot;content&quot;: &quot;Hello&quot;},
  ...     \{&quot;role&quot;: &quot;assistant&quot;, &quot;content&quot;: &quot;Hi there!&quot;}
  ... ]
  &gt;&gt;&gt; session_id = agent.generate_session_id(history=history)

