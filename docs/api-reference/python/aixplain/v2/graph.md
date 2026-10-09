---
sidebar_label: graph
title: aixplain.v2.graph
---

`from aixplain import AgentNode, Condition, ConditionDict, ConditionalNode, Edge, EdgeDict, Graph, GraphDict, InspectorNode, LLMNode, Node, RawNode, RetryPolicy, RetryPolicyDict, ScriptNode, StaticGraphStrategy, StaticGraphStrategyDict, ToolNode`


Portable static graph definitions for aiXplain v2 agents.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### RetryPolicyDict Objects

```python
class RetryPolicyDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L59)

The dict form of `RetryPolicy`.

### ConditionDict Objects

```python
class ConditionDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L68)

The dict form of `Condition`.

### EdgeDict Objects

```python
class EdgeDict(_EdgeRequired)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L81)

The dict form of `Edge`.

### StaticGraphStrategyDict Objects

```python
class StaticGraphStrategyDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L89)

The dict form of `StaticGraphStrategy`.

### GraphDict Objects

```python
class GraphDict(_GraphRequired)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L102)

The dict form of `Graph`; ``nodes`` is a list of nodes or the wire map of id to node dict.

### RetryPolicy Objects

```python
@dataclass
class RetryPolicy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L112)

Retry settings applied by the static graph executor.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L120)

Validate retry limits accepted by the backend.

#### to\_dict

```python
def to_dict(validate: bool = True) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L135)

Serialize using the engine's canonical snake_case contract.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Union["RetryPolicy", RetryPolicyDict],
              strict: bool = True) -> "RetryPolicy"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L147)

Deserialize a retry policy; ``strict=False`` ignores unknown keys.

### Condition Objects

```python
@dataclass(frozen=True)
class Condition()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L155)

A portable edge condition evaluated against graph state.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L165)

Validate the backend's structured edge-condition contract.

#### equals

```python
@classmethod
def equals(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L186)

Match when a state value equals ``value``.

#### not\_equals

```python
@classmethod
def not_equals(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L191)

Match when a state value does not equal ``value``.

#### greater\_than

```python
@classmethod
def greater_than(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L196)

Match when a state value is greater than ``value``.

#### greater\_than\_or\_equal

```python
@classmethod
def greater_than_or_equal(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L201)

Match when a state value is greater than or equal to ``value``.

#### less\_than

```python
@classmethod
def less_than(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L206)

Match when a state value is less than ``value``.

#### less\_than\_or\_equal

```python
@classmethod
def less_than_or_equal(cls, key: str, value: Any) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L211)

Match when a state value is less than or equal to ``value``.

#### is\_true

```python
@classmethod
def is_true(cls, key: str) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L216)

Match a boolean true state value.

#### is\_false

```python
@classmethod
def is_false(cls, key: str) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L221)

Match a boolean false state value.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L225)

Serialize the condition to the backend/engine contract.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Union["Condition", ConditionDict],
              strict: bool = True) -> "Condition"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L230)

Deserialize a structured edge condition; ``strict=False`` keeps one the SDK cannot validate.

### Node Objects

```python
@dataclass
class Node()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L256)

Common configuration shared by all portable graph nodes.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L272)

Assign and validate the graph-local identifier.

#### id

```python
@property
def id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L284)

Return the graph-local node ID.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L291)

Validate node-specific configuration.

#### to\_dict

```python
def to_dict(validate: bool = True) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L294)

Serialize the node to the engine's canonical contract.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Mapping[str, Any],
              node_id: Optional[str] = None,
              strict: bool = True) -> "Node"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L315)

Build the typed node named by ``value["type"]``.

With ``strict=False`` a node the SDK cannot model or validate comes back as a `RawNode`.

### LLMNode Objects

```python
@dataclass
class LLMNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L345)

A single model call in a static graph.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L356)

Validate model generation settings.

### ToolNode Objects

```python
@dataclass
class ToolNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L378)

A registered tool invocation.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L388)

Require the engine registry name for the tool.

### AgentNode Objects

```python
@dataclass
class AgentNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L403)

A registered sub-agent invocation.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L412)

Require the engine registry name for the sub-agent.

### ScriptNode Objects

```python
@dataclass
class ScriptNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L422)

Sandboxed Python source executed as a graph step.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L431)

Require source and sandboxing for backend-authored graphs.

### InspectorNode Objects

```python
@dataclass
class InspectorNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L443)

A registered inspector check.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L452)

Validate inspector configuration.

### ConditionalNode Objects

```python
@dataclass
class ConditionalNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L468)

A sandboxed expression that writes a boolean routing value.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L476)

Require a sandboxed expression.

### RawNode Objects

```python
@dataclass
class RawNode(Node)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L488)

A fetched node the SDK does not model, kept verbatim so the graph saves back unchanged.

#### to\_dict

```python
def to_dict(validate: bool = True) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L494)

Return the node exactly as the backend sent it.

### Edge Objects

```python
@dataclass
class Edge()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L506)

A directed graph edge with an optional portable condition.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L515)

Coerce a dict condition and check the endpoints.

#### source\_id

```python
@property
def source_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L525)

Return the source node ID.

#### target\_id

```python
@property
def target_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L530)

Return the target node ID.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L534)

Serialize the edge.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Union["Edge", EdgeDict],
              strict: bool = True) -> "Edge"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L546)

Deserialize an edge; ``strict=False`` ignores unknown keys and keeps unvalidated conditions.

### StaticGraphStrategy Objects

```python
@dataclass
class StaticGraphStrategy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L556)

Execution settings stored alongside an agent graph.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L563)

Validate strategy settings accepted by the platform backend.

#### to\_dict

```python
def to_dict(validate: bool = True) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L588)

Serialize static graph strategy settings.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Union["StaticGraphStrategy", StaticGraphStrategyDict],
              strict: bool = True) -> "StaticGraphStrategy"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L602)

Deserialize strategy settings; ``strict=False`` ignores unknown keys and skips validation.

### Graph Objects

```python
@dataclass
class Graph()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L622)

A validated, portable static execution graph.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L632)

Coerce dict nodes and edges into their typed forms.

#### entry\_point\_id

```python
@property
def entry_point_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L642)

Return the entry-point node ID.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L646)

Validate graph structure before it is sent to the platform.

#### to\_dict

```python
def to_dict(validate: bool = True) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L726)

Serialize the graph to the backend/engine wire contract.

#### from\_dict

```python
@classmethod
def from_dict(cls,
              value: Union["Graph", GraphDict],
              strict: bool = True) -> "Graph"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/graph.py#L742)

Build a graph from its dict form.

``strict=True`` (caller input) rejects unknown keys and validates. ``strict=False`` (a backend
response) ignores unknown keys, keeps unmodeled nodes as `RawNode`, and skips validation:
the backend is authoritative for what it already stored.

