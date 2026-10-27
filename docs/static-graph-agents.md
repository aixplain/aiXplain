# Static Graph Agents (v2)

Static graphs let you choose the exact steps and routes an Agent can execute. Unlike dynamic planning, the graph is
defined before the run, saved with the Agent, and executed in a deterministic node order unless conditional edges
select a different route.

## Before you start

Set either `TEAM_API_KEY` or `AIXPLAIN_API_KEY`. You also need the platform model ID used by each `LLMNode`.

The current platform contract supports these nodes:

- `LLMNode`: make one model call.
- `ToolNode`: invoke a tool or model attached to the Agent.
- `AgentNode`: invoke a sub-agent registered on the Agent by its engine agent name.
- `ScriptNode`: run inline Python in the sandbox.
- `InspectorNode`: run a registered inspector. The Agent must declare that inspector (the node names it with
  `inspector_type`); an undeclared name fails the node and the error lists the inspectors that are registered.
- `ConditionalNode`: evaluate a sandboxed expression and store its result.

Values move through graph state using node-level `input_mapping`, `output_mapping`, `input_key`, `output_key`,
`arg_mapping`, and `result_key`. Edges only define order and conditional routing; they do not need data mappings.
See [How values move between nodes](#how-values-move-between-nodes) for the exact rules.

## Minimal save and run demo

```python
from aixplain import Aixplain, Graph, LLMNode

aix = Aixplain()  # reads TEAM_API_KEY or AIXPLAIN_API_KEY from the environment
MODEL_ID = "your-model-id"

answer = LLMNode(
    name="Answer the user",
    node_id="answer",
    model=MODEL_ID,
    input_key="input",
    output_key="answer",
    system_prompt="Answer clearly and briefly.",
    max_tokens=300,
)

graph = Graph(
    entry_point=answer,
    nodes=[answer],
)

agent = aix.Agent(
    name="Static answer demo",
    instructions="Execute the configured static graph.",
    llm=MODEL_ID,
    graph=graph,
)

# The SDK adds graphVersion="1" and strategy.type="static_graph".
agent.save()

result = agent.run("What is a static execution graph?")
print(result.data.output)
```

Node IDs are graph-local identifiers. Supply a stable `node_id` when you want predictable saved documents and trace
entries; otherwise, the SDK generates a readable unique ID from the node name.

## Connect multiple steps

Edges define the execution order. This example runs a sandboxed preparation step before the model call:

```python
from aixplain import Aixplain, Edge, Graph, LLMNode, ScriptNode

aix = Aixplain()
MODEL_ID = "your-model-id"

prepare = ScriptNode(
    name="Prepare input",
    node_id="prepare",
    script="result = input.strip()",
    script_input_vars=["input"],
    output_key="clean_input",
)

answer = LLMNode(
    name="Answer",
    node_id="answer",
    model=MODEL_ID,
    input_key="clean_input",
    output_key="answer",
)

graph = Graph(
    entry_point=prepare,
    nodes=[prepare, answer],
    edges=[Edge(source=prepare, target=answer)],
)

agent = aix.Agent(name="Prepared answer", llm=MODEL_ID, graph=graph)
agent.save()
result = agent.run("  Explain deterministic workflows.  ")
```

## How values move between nodes

All nodes read from and write to one shared state dict. The run input is available as `input`.

- **`input_key`** reads one state value as the node's input.
- **`input_mapping`** builds the input from templates. Reference state keys as `{key}` or `{state[key]}`; both work.
  For an `LLMNode`, the `prompt` entry becomes the user message:
  `input_mapping={"prompt": "Summarize: {clean_input}"}`. A template that names a missing key fails the node.
- **`output_key`** is the state key a node writes its result to. Without it, an `LLMNode` writes
  `<node_id>_output`.
- **`ScriptNode`** sets a variable named `result`. A dict is merged into state as-is, one entry per key. Any other value
  is written to `output_key`, or to `<node_id>_result` when `output_key` is not set.
- **`ToolNode`** passes state values to the tool with `arg_mapping={"tool_arg": "state_key"}` and writes the tool's
  result to `result_key` (default `<node_id>_output`).
- **`ConditionalNode`** writes its boolean result to `output_key` (default `<node_id>_result`), and to every
  `output_mapping` target, exactly like the other nodes, so an edge or a loop-back condition can route on the key you
  named. It also always writes `last_condition_result` and `last_condition_bool`.

### Naming the tool in a `ToolNode`

`tool_name` can be:

- the ID or name of a model or tool attached to the Agent, when that asset has a single action (for example a model);
- the action name, for a tool with several actions (for example `"search"` on a web-search tool).

### The run's final answer

The run returns the first non-empty of the `output`, `last_response` and `result` state keys. `last_response` is set by
every `LLMNode`, `ToolNode` and `AgentNode` to its latest result, so once any of those has run it takes precedence over
whatever a later script writes under another key. If none of the three is set, the run returns what the last node
wrote: its single value, or a JSON object when it wrote several keys.

To control the answer exactly, have the last node write `output`:

```python
publish = ScriptNode(name="Publish", node_id="publish", script="result = {'output': state['draft']}")
```

### When a node fails

A failing node fails the whole run. The error names the node, its type and the reason, both in the run's error and in
that node's step:

```text
Graph node 'answer' (llm) failed: LLMNode 'answer': input_mapping['prompt'] references state key 'clean', which is not set
Graph node 'prepare' (script) failed: ScriptNode 'prepare' script failed: KeyError: missing
Graph node 'answer' (llm) failed: Rate limit reached for model '...'. Retrying later may succeed.
```

Configuration, state and script errors use the code `GRAPH_NODE_FAILED`. Model and platform errors keep their own code
(for example `RATE_LIMITED` or `NO_CREDITS`).

## Conditional routing

Conditional edges use a state key, an operator, and a scalar comparison value. They are evaluated in declaration
order, and the first matching edge is followed. Every node with conditional edges must end with one unconditional
fallback edge:

```python
from aixplain import Condition, Edge, Graph

graph = Graph(
    entry_point=score_node,
    nodes=[score_node, high_node, medium_node, low_node],
    edges=[
        Edge(score_node, high_node, Condition.greater_than("score", 0.8)),
        Edge(score_node, medium_node, Condition.greater_than("score", 0.5)),
        Edge(score_node, low_node),  # Unconditional fallback must be last.
    ],
)
```

For a score of `0.9`, the first route wins. For `0.6`, the second route wins. Any other value follows the fallback.
The supported helpers are `equals`, `not_equals`, `greater_than`, `greater_than_or_equal`, `less_than`,
`less_than_or_equal`, `is_true`, and `is_false`. Comparison values must be strings, finite numbers, booleans, or
`None`; ordering comparisons accept only strings or numbers.

A `ConditionalNode`'s own `condition` is a single Python expression evaluated against the state. Every state key is
bound by name, so `score >= 0.5 and status == "ready"` works next to the `state["score"]` form; a key that is not a
valid identifier (for example `"class"`) is reachable only as `state["class"]`. The `state` name always refers to the
state dict itself, even if a key is also named `state`. Statements, imports and dunder access are rejected.

## Cycles

Cycles are rejected by default. To create a bounded loop, opt in and specify its maximum iterations:

```python
graph = Graph(
    entry_point=first_node,
    nodes=[first_node, retry_node],
    edges=[
        Edge(first_node, retry_node),
        Edge(retry_node, first_node),
    ],
    allow_cycles=True,
    max_loop_iterations=3,
)
```

## Fetch and update

Fetched graphs are reconstructed as typed SDK objects, so they can be inspected or changed and saved again. A node
type the SDK does not model comes back as a `RawNode` and is saved back unchanged:

```python
agent = aix.Agent.get("saved-agent-id")

print(agent.graph.entry_point_id)
print([node.id for node in agent.graph.nodes])

agent.graph.max_loop_iterations = 5
agent.save()
```

Local validation runs when the graph is serialized for `save()` (and when a graph is passed as a dict). It rejects
unknown edge endpoints, duplicate or unreachable nodes, invalid cycles, duplicate conditions, missing fallbacks, and
incorrectly ordered fallback edges before a network request is made. A fetched graph is not validated locally: the
backend and engine perform their own authoritative validation at save and run time.

## Plain data

Every graph type also accepts a dict: `Graph`, `Edge`, `Condition`, `RetryPolicy`, and `StaticGraphStrategy` (typed as
`GraphDict`, `EdgeDict`, `ConditionDict`, `RetryPolicyDict`, and `StaticGraphStrategyDict`). A node dict names its
`type` (`llm`, `tool`, `agent`, `script`, `inspector`, `conditional`) and takes that node class's fields. An unknown key
raises `ValidationError` naming the accepted fields:

```python
agent.graph = {
    "entry_point": "answer",
    "nodes": {"answer": {"type": "llm", "model": MODEL_ID, "output_key": "answer"}},
}
agent.strategy = {"max_iterations": 5}
```

Set a cost or duration cap in either `agent.budget` or `agent.strategy.budget`, not both. The SDK sends both and warns
when both are set.

Caps are checked before each node starts, and again once a node has finished, so a node that takes the run over a cost
or duration cap stops the graph there instead of being reported as a completed run. An iteration cap only limits which
nodes may start: a run that finishes on its own exactly at the cap is a success.
