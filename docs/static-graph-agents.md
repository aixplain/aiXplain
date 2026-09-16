# Static Graph Agents (v2)

Static graphs let you choose the exact steps and routes an Agent can execute. Unlike dynamic planning, the graph is
defined before the run, saved with the Agent, and executed in a deterministic node order unless conditional edges
select a different route.

## Before you start

Set either `TEAM_API_KEY` or `AIXPLAIN_API_KEY`. You also need the platform model ID used by each `LLMNode`.

The current platform contract supports these nodes:

- `LLMNode`: make one model call.
- `ToolNode`: invoke a tool registered on the Agent by its engine tool name.
- `AgentNode`: invoke a sub-agent registered on the Agent by its engine agent name.
- `ScriptNode`: run inline Python in the sandbox.
- `InspectorNode`: run a registered inspector.
- `ConditionalNode`: evaluate a sandboxed expression and store its result.

Values move through graph state using node-level `input_mapping`, `output_mapping`, `input_key`, `output_key`,
`arg_mapping`, and `result_key`. Edges only define order and conditional routing; they do not need data mappings.

## Minimal save and run demo

```python
from aixplain.v2 import Agent, Graph, LLMNode

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

agent = Agent(
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
from aixplain.v2 import Agent, Edge, Graph, LLMNode, ScriptNode

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

agent = Agent(name="Prepared answer", llm=MODEL_ID, graph=graph)
agent.save()
result = agent.run("  Explain deterministic workflows.  ")
```

## Conditional routing

Conditional edges use a state key, an operator, and a scalar comparison value. They are evaluated in declaration
order, and the first matching edge is followed. Every node with conditional edges must end with one unconditional
fallback edge:

```python
from aixplain.v2 import Condition, Edge, Graph

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

Fetched graphs are reconstructed as typed SDK objects, so they can be inspected or changed and saved again:

```python
agent = Agent.get("saved-agent-id")

print(agent.graph.entry_point_id)
print([node.id for node in agent.graph.nodes])

agent.graph.max_loop_iterations = 5
agent.save()
```

Local validation runs when an Agent is constructed and again before graph serialization. It rejects unknown edge
endpoints, duplicate or unreachable nodes, invalid cycles, duplicate conditions, missing fallbacks, and incorrectly
ordered fallback edges before a network request is made. The backend and engine perform their own authoritative
validation at save and run time.
