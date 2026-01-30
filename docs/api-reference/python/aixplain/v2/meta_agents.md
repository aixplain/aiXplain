---
sidebar_label: meta_agents
title: aixplain.v2.meta_agents
---

Meta agents module - Debugger and other meta-agent utilities.

This module provides meta-agents that operate on top of other agents,
such as the Debugger for analyzing agent responses.

Example usage:
    from aixplain import Aixplain

    # Initialize the client
    aix = Aixplain(&quot;&lt;api_key&gt;&quot;)

    # Standalone usage
    debugger = aix.Debugger()
    result = debugger.run(&quot;Analyze this agent output: ...&quot;)

    # Or with custom prompt
    result = debugger.run(content=&quot;...&quot;, prompt=&quot;Focus on error handling&quot;)

    # From agent response (chained)
    agent = aix.Agent.get(&quot;my_agent_id&quot;)
    response = agent.run(&quot;Hello!&quot;)
    debug_result = response.debug()  # Uses default prompt
    debug_result = response.debug(&quot;Why did it take so long?&quot;)  # Custom prompt

### DebugResult Objects

```python
@dataclass_json

@dataclass
class DebugResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L42)

Result from running the Debugger meta-agent.

**Attributes**:

- `data` - The debugging analysis output.
- `session_id` - Session ID for conversation continuity.
- `request_id` - Request ID for tracking.
- `used_credits` - Credits consumed by the debugging operation.
- `run_time` - Time taken to run the debugging analysis.
- `analysis` - The main debugging analysis text (extracted from data output).

#### analysis

```python
@property
def analysis() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L61)

Extract the debugging analysis text from the result data.

**Returns**:

  The analysis text if available, None otherwise.

### Debugger Objects

```python
class Debugger()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L82)

Meta-agent for debugging and analyzing agent responses.

The Debugger uses a pre-configured aiXplain agent to provide insights into
agent runs, errors, and potential improvements.

**Attributes**:

- `context` - The Aixplain client context for API access.
  

**Example**:

  # Create a debugger through the client
  aix = Aixplain(&quot;&lt;api_key&gt;&quot;)
  debugger = aix.Debugger()
  
  # Analyze content directly
  result = debugger.run(&quot;Agent returned: &#x27;Error 500&#x27;&quot;)
  
  # Debug an agent response
  agent_result = agent.run(&quot;Hello!&quot;)
  debug_result = debugger.debug_response(agent_result)

#### \_\_init\_\_

```python
def __init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L106)

Initialize the Debugger.

The context is set as a class attribute by the Aixplain client
when creating the Debugger class dynamically.

#### run

```python
def run(content: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs: Any) -> DebugResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L130)

Run the debugger on provided content.

This is the standalone usage mode where you can analyze any content
or agent output directly.

**Arguments**:

- `content` - The content to analyze/debug. Can be agent output,
  error messages, or any text requiring analysis.
- `prompt` - Optional custom prompt to guide the debugging analysis.
  If not provided, uses a default debugging prompt.
- `**kwargs` - Additional parameters to pass to the underlying agent.
  

**Returns**:

- `DebugResult` - The debugging analysis result.
  

**Example**:

  debugger = aix.Debugger()
  result = debugger.run(&quot;Agent returned: &#x27;Error 500&#x27;&quot;)
  print(result.analysis)

#### debug\_response

```python
def debug_response(response: "AgentRunResult",
                   prompt: Optional[str] = None,
                   execution_id: Optional[str] = None,
                   **kwargs: Any) -> DebugResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/meta_agents.py#L166)

Debug an agent response.

This method is designed to analyze AgentRunResult objects to provide
insights into what happened during the agent execution.

**Arguments**:

- `response` - The AgentRunResult to analyze.
- `prompt` - Optional custom prompt to guide the debugging analysis.
- `execution_id` - Optional execution ID override. If not provided, will be
  extracted from the response&#x27;s request_id or poll URL.
  The execution_id allows the debugger to fetch additional
  information like logs from the backend.
- `**kwargs` - Additional parameters to pass to the underlying agent.
  

**Returns**:

- `DebugResult` - The debugging analysis result.
  

**Example**:

  agent_result = agent.run(&quot;Hello!&quot;)
  debug_result = debugger.debug_response(agent_result, prompt=&quot;Why is it slow?&quot;)
  
  # Or with explicit execution ID
  debug_result = debugger.debug_response(agent_result, execution_id=&quot;abc-123&quot;)

