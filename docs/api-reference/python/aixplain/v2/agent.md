---
sidebar_label: agent
title: aixplain.v2.agent
---

### ConversationMessage Objects

```python
class ConversationMessage(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L32)

Type definition for a conversation message in agent history.

**Attributes**:

- `role` - The role of the message sender, either &#x27;user&#x27; or &#x27;assistant&#x27;
- `content` - The text content of the message

#### validate\_history

```python
def validate_history(history: List[Dict[str, Any]]) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L44)

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

### AgentRunParams Objects

```python
class AgentRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L109)

Parameters for running an agent.

### AgentResponseData Objects

```python
@dataclass_json

@dataclass
class AgentResponseData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L127)

Data structure for agent response.

### AgentRunResult Objects

```python
@dataclass_json

@dataclass
class AgentRunResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L139)

Result from running an agent.

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L172)

Agent resource class.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L294)

Mark the agent as deleted by setting status to DELETED and calling parent method.

#### on\_poll

```python
def on_poll(response: AgentRunResult,
            **kwargs: Unpack[AgentRunParams]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L371)

Hook called after each poll to display agent execution progress.

This method displays real-time progress updates during agent execution,
including tool usage, execution stages, and runtime information.

**Arguments**:

- `response` - The poll response containing progress information
- `**kwargs` - Run parameters including show_progress flag

#### save

```python
def save(*args: Any, **kwargs: Any) -> "Agent"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L447)

Save the agent with dependency management.

This method extends the base save functionality to handle saving of dependent
child components before the agent itself is saved.

**Arguments**:

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L587)

Callback to be called before the resource is saved.
Handles status transitions based on save type.

#### after\_clone

```python
def after_clone(result: Union["Agent", Exception],
                **kwargs: Any) -> Optional["Agent"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L602)

Callback called after the agent is cloned.
Sets the cloned agent&#x27;s status to DRAFT.

#### search

```python
@classmethod
def search(cls: type["Agent"],
           query: Optional[str] = None,
           **kwargs: Unpack[BaseSearchParams]) -> "Page[Agent]"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L614)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L635)

Build the payload for the save action.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[AgentRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L711)

Build the payload for the run action.

#### generate\_session\_id

```python
def generate_session_id(
        history: Optional[List[ConversationMessage]] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent.py#L762)

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

