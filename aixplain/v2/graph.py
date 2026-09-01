"""Portable static graph definitions for aiXplain v2 agents.

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
"""

from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Type, Union

from .exceptions import ValidationError


def _node_id(name: str) -> str:
    """Build a readable, unique graph node identifier."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "node"
    return f"{slug}-{uuid.uuid4().hex[:8]}"


def _is_finite_number(value: Any) -> bool:
    """Return whether a value is a finite JSON number, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


@dataclass
class RetryPolicy:
    """Retry settings applied by the static graph executor."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0

    def validate(self) -> None:
        """Validate retry limits accepted by the backend."""
        if (
            not isinstance(self.max_retries, int)
            or isinstance(self.max_retries, bool)
            or not 0 <= self.max_retries <= 10
        ):
            raise ValidationError("retry_policy.max_retries must be an integer from 0 through 10.")
        if not _is_finite_number(self.initial_delay) or not _is_finite_number(self.max_delay):
            raise ValidationError("retry_policy delays must be finite numbers.")
        if self.initial_delay < 0 or self.max_delay < 0:
            raise ValidationError("retry_policy delays must be non-negative.")
        if not _is_finite_number(self.exponential_base) or self.exponential_base < 1:
            raise ValidationError("retry_policy.exponential_base must be at least 1.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize using the engine's canonical snake_case contract."""
        self.validate()
        return {
            "max_retries": self.max_retries,
            "initial_delay": self.initial_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
        }

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "RetryPolicy":
        """Deserialize a retry policy."""
        return cls(**value)


@dataclass(frozen=True)
class Condition:
    """A portable edge condition evaluated against graph state."""

    key: str
    operator: str
    value: Any

    OPERATORS: ClassVar[set] = {"eq", "ne", "gt", "gte", "lt", "lte"}
    ORDERING_OPERATORS: ClassVar[set] = {"gt", "gte", "lt", "lte"}

    def __post_init__(self) -> None:
        """Validate the backend's structured edge-condition contract."""
        if not isinstance(self.key, str) or not self.key:
            raise ValidationError("A condition key must be a non-empty string.")
        if self.operator not in self.OPERATORS:
            supported = ", ".join(sorted(self.OPERATORS))
            raise ValidationError(f"Unsupported condition operator '{self.operator}'; expected one of: {supported}.")
        if not self._is_json_scalar(self.value):
            raise ValidationError("A condition value must be a finite number, string, boolean, or None.")
        if self.operator in self.ORDERING_OPERATORS and not (
            isinstance(self.value, (int, float, str)) and not isinstance(self.value, bool)
        ):
            raise ValidationError(f"Condition operator '{self.operator}' requires a number or string value.")

    @staticmethod
    def _is_json_scalar(value: Any) -> bool:
        if value is None or isinstance(value, (str, bool)):
            return True
        return _is_finite_number(value)

    @classmethod
    def equals(cls, key: str, value: Any) -> "Condition":
        """Match when a state value equals ``value``."""
        return cls(key, "eq", value)

    @classmethod
    def not_equals(cls, key: str, value: Any) -> "Condition":
        """Match when a state value does not equal ``value``."""
        return cls(key, "ne", value)

    @classmethod
    def greater_than(cls, key: str, value: Any) -> "Condition":
        """Match when a state value is greater than ``value``."""
        return cls(key, "gt", value)

    @classmethod
    def greater_than_or_equal(cls, key: str, value: Any) -> "Condition":
        """Match when a state value is greater than or equal to ``value``."""
        return cls(key, "gte", value)

    @classmethod
    def less_than(cls, key: str, value: Any) -> "Condition":
        """Match when a state value is less than ``value``."""
        return cls(key, "lt", value)

    @classmethod
    def less_than_or_equal(cls, key: str, value: Any) -> "Condition":
        """Match when a state value is less than or equal to ``value``."""
        return cls(key, "lte", value)

    @classmethod
    def is_true(cls, key: str) -> "Condition":
        """Match a boolean true state value."""
        return cls.equals(key, True)

    @classmethod
    def is_false(cls, key: str) -> "Condition":
        """Match a boolean false state value."""
        return cls.equals(key, False)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the condition to the backend/engine contract."""
        return {"key": self.key, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "Condition":
        """Deserialize a structured edge condition."""
        if set(value) != {"key", "operator", "value"}:
            raise ValidationError("An edge condition must contain exactly key, operator, and value.")
        return cls(key=value["key"], operator=value["operator"], value=value["value"])


@dataclass
class Node:
    """Common configuration shared by all portable graph nodes."""

    name: str
    node_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    retry_policy: Optional[RetryPolicy] = None
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None
    input_key: Optional[str] = None
    output_key: Optional[str] = None

    TYPE: ClassVar[str] = ""

    def __post_init__(self) -> None:
        """Assign and validate the graph-local identifier."""
        self.node_id = self.node_id or _node_id(self.name)
        if not isinstance(self.node_id, str) or not self.node_id:
            raise ValidationError("A graph node ID must be a non-empty string.")
        if self.timeout is not None and self.timeout < 0:
            raise ValidationError(f"Node '{self.node_id}' timeout must be non-negative.")
        if self.retry_policy is not None:
            self.retry_policy.validate()

    @property
    def id(self) -> str:
        """Return the graph-local node ID."""
        return self.node_id or ""

    def _specific_dict(self) -> Dict[str, Any]:
        return {}

    def validate(self) -> None:
        """Validate node-specific configuration."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the node to the engine's canonical contract."""
        self.validate()
        value: Dict[str, Any] = {"id": self.id, "type": self.TYPE}
        optional = {
            "name": self.name,
            "config": self.config,
            "metadata": self.metadata,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy.to_dict() if self.retry_policy else None,
            "input_mapping": self.input_mapping,
            "output_mapping": self.output_mapping,
            "input_key": self.input_key,
            "output_key": self.output_key,
        }
        value.update({key: item for key, item in optional.items() if item not in (None, {}, [])})
        value.update({key: item for key, item in self._specific_dict().items() if item not in (None, {}, [])})
        return value


@dataclass
class LLMNode(Node):
    """A single model call in a static graph."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)

    TYPE: ClassVar[str] = "llm"

    def validate(self) -> None:
        """Validate model generation settings."""
        if not self.model:
            raise ValidationError(f"LLM node '{self.id}' requires model.")
        if self.temperature is not None and (not _is_finite_number(self.temperature) or not 0 <= self.temperature <= 2):
            raise ValidationError(f"LLM node '{self.id}' temperature must be between 0 and 2.")
        if self.max_tokens is not None and (
            not isinstance(self.max_tokens, int) or isinstance(self.max_tokens, bool) or self.max_tokens < 1
        ):
            raise ValidationError(f"LLM node '{self.id}' max_tokens must be a positive integer.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
        }


@dataclass
class ToolNode(Node):
    """A registered tool invocation."""

    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    arg_mapping: Optional[Dict[str, str]] = None
    result_key: Optional[str] = None

    TYPE: ClassVar[str] = "tool"

    def validate(self) -> None:
        """Require the engine registry name for the tool."""
        if not self.tool_name:
            raise ValidationError(f"Tool node '{self.id}' requires tool_name.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "arg_mapping": self.arg_mapping,
            "result_key": self.result_key,
        }


@dataclass
class AgentNode(Node):
    """A registered sub-agent invocation."""

    agent_name: Optional[str] = None
    agent_prompt: Optional[str] = None
    share_session: bool = False

    TYPE: ClassVar[str] = "agent"

    def validate(self) -> None:
        """Require the engine registry name for the sub-agent."""
        if not self.agent_name:
            raise ValidationError(f"Agent node '{self.id}' requires agent_name.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {"agent_name": self.agent_name, "agent_prompt": self.agent_prompt, "share_session": self.share_session}


@dataclass
class ScriptNode(Node):
    """Sandboxed Python source executed as a graph step."""

    script: Optional[str] = None
    script_input_vars: Optional[List[str]] = None
    sandbox: bool = True

    TYPE: ClassVar[str] = "script"

    def validate(self) -> None:
        """Require source and sandboxing for backend-authored graphs."""
        if not self.script:
            raise ValidationError(f"Script node '{self.id}' requires script.")
        if not self.sandbox:
            raise ValidationError(f"Script node '{self.id}' must run in the sandbox.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {"script": self.script, "script_input_vars": self.script_input_vars, "sandbox": self.sandbox}


@dataclass
class InspectorNode(Node):
    """A registered inspector check."""

    inspector_type: Optional[str] = None
    content_key: Optional[str] = None
    failure_action: str = "block"

    TYPE: ClassVar[str] = "inspector"

    def validate(self) -> None:
        """Validate inspector configuration."""
        if not self.inspector_type:
            raise ValidationError(f"Inspector node '{self.id}' requires inspector_type.")
        if self.failure_action not in {"block", "warn", "transform"}:
            raise ValidationError(f"Inspector node '{self.id}' has an invalid failure_action.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {
            "inspector_type": self.inspector_type,
            "content_key": self.content_key,
            "failure_action": self.failure_action,
        }


@dataclass
class ConditionalNode(Node):
    """A sandboxed expression that writes a boolean routing value."""

    condition: Optional[str] = None
    sandbox: bool = True

    TYPE: ClassVar[str] = "conditional"

    def validate(self) -> None:
        """Require a sandboxed expression."""
        if not self.condition:
            raise ValidationError(f"Conditional node '{self.id}' requires condition.")
        if not self.sandbox:
            raise ValidationError(f"Conditional node '{self.id}' must run in the sandbox.")

    def _specific_dict(self) -> Dict[str, Any]:
        return {"condition": self.condition, "sandbox": self.sandbox}


NODE_TYPES: Dict[str, Type[Node]] = {
    node_type.TYPE: node_type
    for node_type in (LLMNode, ToolNode, AgentNode, ScriptNode, InspectorNode, ConditionalNode)
}


@dataclass
class Edge:
    """A directed graph edge with an optional portable condition."""

    source: Union[str, Node]
    target: Union[str, Node]
    condition: Optional[Condition] = None
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source_id(self) -> str:
        """Return the source node ID."""
        return self.source.id if isinstance(self.source, Node) else self.source

    @property
    def target_id(self) -> str:
        """Return the target node ID."""
        return self.target.id if isinstance(self.target, Node) else self.target

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the edge."""
        value: Dict[str, Any] = {"source": self.source_id, "target": self.target_id}
        if self.condition is not None:
            value["condition"] = self.condition.to_dict()
        if self.label is not None:
            value["label"] = self.label
        if self.metadata:
            value["metadata"] = self.metadata
        return value

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "Edge":
        """Deserialize an edge."""
        condition = value.get("condition")
        return cls(
            source=value["source"],
            target=value["target"],
            condition=Condition.from_dict(condition) if condition is not None else None,
            label=value.get("label"),
            metadata=value.get("metadata", {}),
        )


@dataclass
class StaticGraphStrategy:
    """Execution settings stored alongside an agent graph."""

    max_iterations: Optional[int] = None
    expose_reasoning: bool = True
    budget: Optional[Dict[str, Any]] = None

    def validate(self) -> None:
        """Validate strategy settings accepted by the platform backend."""
        if self.max_iterations is not None and (
            not isinstance(self.max_iterations, int) or isinstance(self.max_iterations, bool) or self.max_iterations < 1
        ):
            raise ValidationError("strategy.max_iterations must be a positive integer.")
        if not isinstance(self.expose_reasoning, bool):
            raise ValidationError("strategy.expose_reasoning must be a boolean.")
        if self.budget is None:
            return
        if not isinstance(self.budget, dict):
            raise ValidationError("strategy.budget must be a dictionary.")
        allowed = {"max_iterations", "max_cost", "max_duration_seconds"}
        extra = set(self.budget) - allowed
        if extra:
            raise ValidationError(f"Unsupported strategy budget fields: {', '.join(sorted(extra))}.")
        for key, value in self.budget.items():
            if value is None:
                continue
            if key == "max_iterations":
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    raise ValidationError("strategy.budget.max_iterations must be a positive integer.")
            elif not _is_finite_number(value) or value <= 0:
                raise ValidationError(f"strategy.budget.{key} must be a positive number.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize static graph strategy settings."""
        self.validate()
        value: Dict[str, Any] = {"type": "static_graph"}
        if self.max_iterations is not None:
            value["max_iterations"] = self.max_iterations
        if not self.expose_reasoning:
            value["expose_reasoning"] = False
        if self.budget:
            value["budget"] = self.budget
        return value

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "StaticGraphStrategy":
        """Deserialize strategy settings."""
        extra = set(value) - {"type", "max_iterations", "expose_reasoning", "budget"}
        if extra:
            raise ValidationError(f"Unsupported static graph strategy fields: {', '.join(sorted(extra))}.")
        if value.get("type") != "static_graph":
            raise ValidationError("Only strategy.type='static_graph' is supported with an Agent graph.")
        strategy = cls(
            max_iterations=value.get("max_iterations"),
            expose_reasoning=value.get("expose_reasoning", True),
            budget=value.get("budget"),
        )
        strategy.validate()
        return strategy


@dataclass
class Graph:
    """A validated, portable static execution graph."""

    entry_point: Union[str, Node]
    nodes: List[Node]
    edges: List[Edge] = field(default_factory=list)
    validate_state: bool = True
    allow_cycles: bool = False
    max_loop_iterations: Optional[int] = None

    @property
    def entry_point_id(self) -> str:
        """Return the entry-point node ID."""
        return self.entry_point.id if isinstance(self.entry_point, Node) else self.entry_point

    def validate(self) -> None:
        """Validate graph structure before it is sent to the platform."""
        if not isinstance(self.validate_state, bool) or not isinstance(self.allow_cycles, bool):
            raise ValidationError("validate_state and allow_cycles must be booleans.")
        if not self.nodes:
            raise ValidationError("A graph must contain at least one node.")
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValidationError("Graph node IDs must be unique.")
        if self.entry_point_id not in node_ids:
            raise ValidationError("Graph entry_point must reference an existing node.")
        for node in self.nodes:
            node.validate()

        outgoing: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
        unconditional_sources: set = set()
        conditional_sources: set = set()
        conditions_by_source: Dict[str, set] = {}
        for index, edge in enumerate(self.edges):
            if edge.source_id not in outgoing or edge.target_id not in outgoing:
                raise ValidationError(f"Graph edge {index} references an unknown node.")
            if edge.condition is None:
                if edge.source_id in unconditional_sources:
                    raise ValidationError(f"Node '{edge.source_id}' has multiple unconditional outgoing edges.")
                unconditional_sources.add(edge.source_id)
            else:
                if edge.source_id in unconditional_sources:
                    raise ValidationError(
                        f"Node '{edge.source_id}' has a conditional edge after its unconditional fallback edge."
                    )
                conditional_sources.add(edge.source_id)
                serialized = json.dumps(
                    [edge.condition.key, edge.condition.operator, edge.condition.value], separators=(",", ":")
                )
                seen = conditions_by_source.setdefault(edge.source_id, set())
                if serialized in seen:
                    raise ValidationError(f"Node '{edge.source_id}' has duplicate outgoing edge conditions.")
                seen.add(serialized)
            outgoing[edge.source_id].append(edge.target_id)

        missing_fallback = sorted(conditional_sources - unconditional_sources)
        if missing_fallback:
            raise ValidationError(
                "Nodes with conditional outgoing edges require an unconditional fallback edge: "
                + ", ".join(missing_fallback)
                + "."
            )

        reachable = {self.entry_point_id}
        queue = [self.entry_point_id]
        while queue:
            for target in outgoing[queue.pop(0)]:
                if target not in reachable:
                    reachable.add(target)
                    queue.append(target)
        orphans = sorted(set(node_ids) - reachable)
        if orphans:
            raise ValidationError(f"Graph contains nodes unreachable from entry_point: {', '.join(orphans)}.")

        indegree = {node_id: 0 for node_id in node_ids}
        for targets in outgoing.values():
            for target in targets:
                indegree[target] += 1
        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            source = queue.pop(0)
            visited += 1
            for target in outgoing[source]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        has_cycle = visited != len(node_ids)
        if has_cycle and not self.allow_cycles:
            raise ValidationError("Graph contains a cycle while allow_cycles is false.")
        if self.allow_cycles and (
            not isinstance(self.max_loop_iterations, int)
            or isinstance(self.max_loop_iterations, bool)
            or self.max_loop_iterations < 1
        ):
            raise ValidationError("max_loop_iterations must be a positive integer when cycles are allowed.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the graph to the backend/engine wire contract."""
        self.validate()
        value: Dict[str, Any] = {
            "nodes": {node.id: node.to_dict() for node in self.nodes},
            "edges": [edge.to_dict() for edge in self.edges],
            "entry_point": self.entry_point_id,
            "validate_state": self.validate_state,
            "allow_cycles": self.allow_cycles,
        }
        if self.max_loop_iterations is not None:
            value["max_loop_iterations"] = self.max_loop_iterations
        return value

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "Graph":
        """Reconstruct typed SDK nodes and edges from an Agent response."""
        nodes = []
        for node_id, raw_node in value.get("nodes", {}).items():
            node_value = dict(raw_node)
            node_type = node_value.pop("type", None)
            node_value.pop("id", None)
            retry_policy = node_value.get("retry_policy")
            if retry_policy:
                node_value["retry_policy"] = RetryPolicy.from_dict(retry_policy)
            node_class = NODE_TYPES.get(node_type)
            if node_class is None:
                raise ValidationError(f"Unsupported graph node type '{node_type}'.")
            nodes.append(node_class(node_id=node_id, **node_value))
        graph = cls(
            entry_point=value.get("entry_point", ""),
            nodes=nodes,
            edges=[Edge.from_dict(edge) for edge in value.get("edges", [])],
            validate_state=value.get("validate_state", True),
            allow_cycles=value.get("allow_cycles", False),
            max_loop_iterations=value.get("max_loop_iterations"),
        )
        graph.validate()
        return graph
