---
sidebar_label: agent
title: aixplain.v2.agent
---

Agent module for aiXplain v2 SDK.

### ConversationMessage Objects

```python
class ConversationMessage(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L35)

Type definition for a conversation message in agent history.

**Attributes**:

- `role` - The role of the message sender, either &#x27;user&#x27; or &#x27;assistant&#x27;
- `content` - The text content of the message

#### validate\_history

```python
def validate_history(history: List[Dict[str, Any]]) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L47)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L105)

Output format options for agent responses.

### AgentRunParams Objects

```python
class AgentRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L113)

Parameters for running an agent.

**Attributes**:

- `sessionId` - Session ID for conversation continuity
- `query` - The query to run
- `variables` - Variables to replace \{\{variable}} placeholders in instructions and description.
  The backend performs the actual substitution.
- `allowHistoryAndSessionId` - Allow both history and session ID
- `tasks` - List of tasks for the agent
- `prompt` - Custom prompt override
- `history` - Conversation history
- `executionParams` - Execution parameters (maxTokens, etc.)
- `criteria` - Criteria for evaluation
- `evolve` - Evolution parameters
- `query`0 - Inspector configurations
- `query`1 - Whether to run response generation. Defaults to True.
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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L155)

Data structure for agent response.

### AgentRunResult Objects

```python
@dataclass_json

@dataclass
class AgentRunResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L168)

Result from running an agent.

#### data

Override type from base class

#### debug

```python
def debug(prompt: Optional[str] = None,
          execution_id: Optional[str] = None,
          **kwargs: Any) -> "DebugResult"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L186)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L239)

A task definition for agent workflows.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L247)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L257)

Agent resource class.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L320)

Initialize agent after dataclass creation.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L361)

Mark the agent as deleted by setting status to DELETED and calling parent method.

#### before\_run

```python
def before_run(*args: Any,
               **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L368)

Hook called before running the agent to validate and prepare state.

#### on\_poll

```python
def on_poll(response: AgentRunResult,
            **kwargs: Unpack[AgentRunParams]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L409)

Hook called after each poll to update progress display.

**Arguments**:

- `response` - The poll response containing progress information
- `**kwargs` - Run parameters

#### after\_run

```python
def after_run(result: Union[AgentRunResult, Exception], *args: Any,
              **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L421)

Hook called after running the agent for result transformation.

#### run

```python
def run(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L440)

Run the agent with optional progress display.

**Arguments**:

- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `progress_format` - Display format - &quot;status&quot; or &quot;logs&quot;. If None (default),
  progress tracking is disabled.
- `progress_verbosity` - Detail level 1-3 (default: 1)
- `progress_truncate` - Truncate long text (default: True)
- `**kwargs` - Additional run parameters
- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `progress_format` - Display format - &quot;status&quot; or &quot;logs&quot;. If None (default),
  progress tracking is disabled.
- `progress_verbosity` - Detail level 1-3 (default: 1)
- `progress_truncate` - Truncate long text (default: True)
- `**kwargs` - Additional run parameters
  

**Returns**:

- `query`2 - The result of the agent execution

#### run\_async

```python
def run_async(*args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L472)

Run the agent asynchronously.

**Arguments**:

- `*args` - Positional arguments (first arg is treated as query)
- `query` - The query to run
- `**kwargs` - Additional run parameters
  

**Returns**:

- `AgentRunResult` - The result of the agent execution

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L520)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L636)

Callback to be called before the resource is saved.

Handles status transitions based on save type.

#### after\_clone

```python
def after_clone(result: Union["Agent", Exception],
                **kwargs: Any) -> Optional["Agent"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L651)

Callback called after the agent is cloned.

Sets the cloned agent&#x27;s status to DRAFT.

#### search

```python
@classmethod
def search(cls: type["Agent"],
           query: Optional[str] = None,
           **kwargs: Unpack[BaseSearchParams]) -> "Page[Agent]"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L661)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L681)

Build the payload for the save action.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[AgentRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L778)

Build the payload for the run action.

#### generate\_session\_id

```python
def generate_session_id(
        history: Optional[List[ConversationMessage]] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L851)

Generate a unique session ID for agent conversations.

This method creates a unique session identifier based on the agent ID and current timestamp.
If conversation history is provided, it attempts to initialize the session on the server
to enable context-aware conversations.

**Arguments**:

- `history` _Optional[List[Dict]], optional_ - Previous conversation history.
  Each dict should contain &#x27;role&#x27; (either &#x27;user&#x27; or &#x27;assistant&#x27;) and &#x27;content&#x27; keys.
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

