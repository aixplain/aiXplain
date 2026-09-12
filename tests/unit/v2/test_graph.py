import pytest

from aixplain.v2 import (
    Agent,
    AgentNode,
    Action,
    Actions,
    Condition,
    ConditionalNode,
    Edge,
    Graph,
    InspectorNode,
    Inspector,
    Input,
    Inputs,
    LLMNode,
    RetryPolicy,
    ScriptNode,
    StaticGraphStrategy,
    ToolNode,
    Tool,
    ValidationError,
)


def test_retry_policy_and_common_node_fields_round_trip() -> None:
    node = LLMNode(
        name="Configured model",
        node_id="configured",
        model="model-id",
        config={"response_format": "json"},
        metadata={"owner": "incident-response"},
        timeout=15,
        retry_policy=RetryPolicy(max_retries=2, initial_delay=0.5, max_delay=5, exponential_base=2),
        input_mapping={"ticket": "clean_ticket"},
        output_mapping={"content": "draft"},
        messages=[{"role": "system", "content": "Be concise."}],
    )
    graph = Graph(entry_point=node, nodes=[node])

    encoded = graph.to_dict()
    decoded = Graph.from_dict(encoded)

    assert decoded.to_dict() == encoded
    assert encoded["nodes"]["configured"]["retry_policy"] == {
        "max_retries": 2,
        "initial_delay": 0.5,
        "max_delay": 5,
        "exponential_base": 2,
    }
    assert encoded["nodes"]["configured"]["input_mapping"] == {"ticket": "clean_ticket"}
    assert encoded["nodes"]["configured"]["output_mapping"] == {"content": "draft"}


@pytest.mark.parametrize(
    "policy, message",
    [
        (RetryPolicy(max_retries=-1), "max_retries"),
        (RetryPolicy(max_retries=11), "max_retries"),
        (RetryPolicy(initial_delay=-1), "non-negative"),
        (RetryPolicy(max_delay=float("inf")), "finite"),
        (RetryPolicy(exponential_base=0.5), "at least 1"),
    ],
)
def test_retry_policy_rejects_invalid_values(policy: RetryPolicy, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        policy.to_dict()


def test_static_graph_agent_builds_backend_contract() -> None:
    classify = LLMNode(
        name="Classify",
        node_id="classify",
        model="model-id",
        input_key="input",
        output_key="score",
    )
    high = ScriptNode(name="High", node_id="high", script="result = 'high'")
    graph = Graph(
        entry_point=classify,
        nodes=[classify, high],
        edges=[Edge(classify, high)],
    )

    payload = Agent(name="Router", graph=graph).build_save_payload()

    assert payload["graphVersion"] == "1"
    assert payload["strategy"] == {"type": "static_graph"}
    assert payload["graph"] == {
        "nodes": {
            "classify": {
                "id": "classify",
                "type": "llm",
                "name": "Classify",
                "input_key": "input",
                "output_key": "score",
                "model": "model-id",
            },
            "high": {
                "id": "high",
                "type": "script",
                "name": "High",
                "script": "result = 'high'",
                "sandbox": True,
            },
        },
        "edges": [{"source": "classify", "target": "high"}],
        "entry_point": "classify",
        "validate_state": True,
        "allow_cycles": False,
    }


def test_graph_round_trip_preserves_typed_nodes_and_strategy() -> None:
    response = {
        "name": "Fetched graph",
        "graphVersion": "1",
        "strategy": {"type": "static_graph", "max_iterations": 8},
        "graph": {
            "nodes": {
                "tool": {"id": "tool", "type": "tool", "name": "Search", "tool_name": "search"},
                "agent": {"id": "agent", "type": "agent", "name": "Writer", "agent_name": "writer"},
                "inspect": {
                    "id": "inspect",
                    "type": "inspector",
                    "name": "Check",
                    "inspector_type": "toxicity",
                    "failure_action": "warn",
                },
            },
            "edges": [
                {"source": "tool", "target": "agent"},
                {"source": "agent", "target": "inspect"},
            ],
            "entry_point": "tool",
            "validate_state": True,
            "allow_cycles": False,
        },
    }

    agent = Agent.from_dict(response)

    assert isinstance(agent.graph, Graph)
    assert isinstance(agent.graph.nodes[0], ToolNode)
    assert isinstance(agent.graph.nodes[1], AgentNode)
    assert isinstance(agent.graph.nodes[2], InspectorNode)
    assert isinstance(agent.strategy, StaticGraphStrategy)
    payload = agent.build_save_payload()
    assert payload["graph"]["entry_point"] == response["graph"]["entry_point"]
    assert payload["graph"]["edges"] == response["graph"]["edges"]
    assert payload["graph"]["nodes"]["tool"] == response["graph"]["nodes"]["tool"]
    assert payload["strategy"] == {"type": "static_graph", "max_iterations": 8}


def test_graph_supports_current_six_backend_node_types() -> None:
    nodes = [
        LLMNode(name="LLM", node_id="llm", model="model"),
        ToolNode(name="Tool", node_id="tool", tool_name="tool"),
        AgentNode(name="Agent", node_id="agent", agent_name="agent"),
        ScriptNode(name="Script", node_id="script", script="result = 1"),
        InspectorNode(name="Inspector", node_id="inspector", inspector_type="pii"),
        ConditionalNode(name="Conditional", node_id="conditional", condition="score > 0.5"),
    ]
    graph = Graph(
        entry_point=nodes[0],
        nodes=nodes,
        edges=[Edge(nodes[index], nodes[index + 1]) for index in range(len(nodes) - 1)],
    )

    assert [node["type"] for node in graph.to_dict()["nodes"].values()] == [
        "llm",
        "tool",
        "agent",
        "script",
        "inspector",
        "conditional",
    ]


def test_node_specific_options_serialize() -> None:
    tool = ToolNode(
        name="Tool",
        node_id="tool",
        tool_name="search",
        tool_args={"limit": 5},
        arg_mapping={"query": "research_query"},
        result_key="evidence",
    )
    agent = AgentNode(
        name="Agent",
        node_id="agent",
        agent_name="specialist",
        agent_prompt="Review {{evidence}}",
        share_session=True,
        output_key="draft",
    )
    script = ScriptNode(
        name="Script",
        node_id="script",
        script="result = {'output': draft}",
        script_input_vars=["draft"],
    )
    inspector = InspectorNode(
        name="Inspector",
        node_id="inspector",
        inspector_type="quality",
        content_key="draft",
        failure_action="transform",
    )
    conditional = ConditionalNode(
        name="Conditional",
        node_id="conditional",
        condition="bool(state.get('draft'))",
    )
    graph = Graph(
        entry_point=tool,
        nodes=[tool, agent, script, inspector, conditional],
        edges=[Edge(tool, agent), Edge(agent, script), Edge(script, inspector), Edge(inspector, conditional)],
    )

    nodes = graph.to_dict()["nodes"]

    assert nodes["tool"]["tool_args"] == {"limit": 5}
    assert nodes["agent"]["share_session"] is True
    assert nodes["script"]["script_input_vars"] == ["draft"]
    assert nodes["inspector"]["failure_action"] == "transform"
    assert nodes["conditional"]["sandbox"] is True


@pytest.mark.parametrize(
    "node, message",
    [
        (LLMNode(name="LLM"), "requires model"),
        (ToolNode(name="Tool"), "requires tool_name"),
        (AgentNode(name="Agent"), "requires agent_name"),
        (ScriptNode(name="Script"), "requires script"),
        (InspectorNode(name="Inspector"), "requires inspector_type"),
        (ConditionalNode(name="Conditional"), "requires condition"),
    ],
)
def test_each_node_type_rejects_missing_required_configuration(node: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        node.to_dict()


@pytest.mark.parametrize(
    "graph, message",
    [
        (
            Graph(
                entry_point="a",
                nodes=[LLMNode(name="A", node_id="a", model="model"), LLMNode(name="B", node_id="b", model="model")],
            ),
            "unreachable",
        ),
        (
            Graph(
                entry_point="a",
                nodes=[LLMNode(name="A", node_id="a", model="model"), LLMNode(name="B", node_id="b", model="model")],
                edges=[Edge("a", "b"), Edge("b", "a")],
            ),
            "cycle",
        ),
    ],
)
def test_graph_rejects_invalid_structure(graph: Graph, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        graph.validate()


def test_conditional_edges_require_a_last_unconditional_fallback() -> None:
    nodes = [
        LLMNode(name="A", node_id="a", model="model"),
        LLMNode(name="B", node_id="b", model="model"),
        LLMNode(name="C", node_id="c", model="model"),
    ]
    graph = Graph(
        entry_point="a",
        nodes=nodes,
        edges=[Edge("a", "b", Condition.equals("route", "b"))],
    )

    with pytest.raises(ValidationError, match="require an unconditional fallback"):
        graph.validate()


def test_structured_edge_conditions_round_trip() -> None:
    edge = Edge.from_dict(
        {
            "source": "a",
            "target": "b",
            "condition": {"key": "approved", "operator": "eq", "value": True},
        }
    )

    assert edge.condition == Condition.is_true("approved")
    assert edge.to_dict() == {
        "source": "a",
        "target": "b",
        "condition": {"key": "approved", "operator": "eq", "value": True},
    }


def test_edge_label_and_metadata_round_trip() -> None:
    encoded = {
        "source": "a",
        "target": "b",
        "label": "approved route",
        "metadata": {"audit_code": "INCIDENT_APPROVED"},
    }

    assert Edge.from_dict(encoded).to_dict() == encoded


def test_conditional_routes_serialize_in_declared_order() -> None:
    nodes = [
        LLMNode(name="A", node_id="a", model="model"),
        LLMNode(name="High", node_id="high", model="model"),
        LLMNode(name="Medium", node_id="medium", model="model"),
        LLMNode(name="Low", node_id="low", model="model"),
    ]
    graph = Graph(
        entry_point="a",
        nodes=nodes,
        edges=[
            Edge("a", "high", Condition.greater_than("score", 0.8)),
            Edge("a", "medium", Condition.greater_than("score", 0.5)),
            Edge("a", "low"),
        ],
    )

    assert [edge.get("condition") for edge in graph.to_dict()["edges"]] == [
        {"key": "score", "operator": "gt", "value": 0.8},
        {"key": "score", "operator": "gt", "value": 0.5},
        None,
    ]


@pytest.mark.parametrize("value", [["not", "scalar"], {"not": "scalar"}, float("inf")])
def test_condition_rejects_non_scalar_values(value: object) -> None:
    with pytest.raises(ValidationError, match="finite number, string, boolean, or None"):
        Condition.equals("value", value)


def test_graph_rejects_duplicate_conditions() -> None:
    nodes = [
        LLMNode(name="A", node_id="a", model="model"),
        LLMNode(name="B", node_id="b", model="model"),
        LLMNode(name="C", node_id="c", model="model"),
        LLMNode(name="D", node_id="d", model="model"),
    ]
    graph = Graph(
        entry_point="a",
        nodes=nodes,
        edges=[
            Edge("a", "b", Condition.equals("route", True)),
            Edge("a", "c", Condition.equals("route", True)),
            Edge("a", "d"),
        ],
    )

    with pytest.raises(ValidationError, match="duplicate outgoing edge conditions"):
        graph.validate()


@pytest.mark.parametrize(
    "strategy, message",
    [
        (StaticGraphStrategy(max_iterations=0), "positive integer"),
        (StaticGraphStrategy(max_iterations=True), "positive integer"),
        (StaticGraphStrategy(expose_reasoning=1), "boolean"),
        (StaticGraphStrategy(budget={"max_cost": 0}), "positive number"),
        (StaticGraphStrategy(budget={"unknown": 1}), "Unsupported strategy budget fields"),
    ],
)
def test_strategy_matches_backend_validation(strategy: StaticGraphStrategy, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        strategy.to_dict()


def test_strategy_valid_budget_and_reasoning_round_trip() -> None:
    encoded = {
        "type": "static_graph",
        "max_iterations": 12,
        "expose_reasoning": False,
        "budget": {"max_iterations": 10, "max_cost": 2.5, "max_duration_seconds": 60},
    }

    assert StaticGraphStrategy.from_dict(encoded).to_dict() == encoded


def test_bounded_cycle_serializes_when_explicitly_enabled() -> None:
    first = ScriptNode(name="First", node_id="first", script="result = {}")
    second = ScriptNode(name="Second", node_id="second", script="result = {}")
    graph = Graph(
        entry_point=first,
        nodes=[first, second],
        edges=[Edge(first, second), Edge(second, first)],
        allow_cycles=True,
        max_loop_iterations=4,
    )

    encoded = graph.to_dict()

    assert encoded["allow_cycles"] is True
    assert encoded["max_loop_iterations"] == 4


def test_graph_rejects_unknown_node_type_from_backend() -> None:
    with pytest.raises(ValidationError, match="Unsupported graph node type 'future_node'"):
        Graph.from_dict(
            {
                "nodes": {"unsupported": {"id": "unsupported", "type": "future_node", "name": "Unsupported"}},
                "edges": [],
                "entry_point": "unsupported",
            }
        )


def test_realistic_model_tool_subagent_and_inspector_payload() -> None:
    model_id = "6a610d0e7dd3d37964ce4c28"
    tool_id = "69fb7750f177c224105dabc6"
    tool = Tool(id=tool_id, name="Web Search")
    tool.__dict__["actions"] = Actions(
        {
            "search": Action(
                name="search",
                description="Search the web.",
                inputs=Inputs({"query": Input(name="query", required=True, type="string")}),
            )
        }
    )
    tool.allowed_actions = ["search"]
    def get_parameters():
        return [
            {
                "code": "SEARCH",
                "name": "search",
                "description": "Search the web.",
                "inputs": {
                    "query": {
                        "name": "query",
                        "value": None,
                        "required": True,
                        "datatype": "string",
                    }
                },
            }
        ]

    tool.get_parameters = get_parameters
    specialist = Agent(
        id="saved-specialist-id",
        name="Static Graph Research Specialist",
        description="Turns web-search evidence into a concise answer.",
        instructions="Use the supplied evidence and cite sources.",
        llm=model_id,
    )
    inspector = Inspector(
        name="Static Graph Nonempty Output Inspector",
        description="Checks that the final response is not empty.",
        severity="low",
        targets=["output"],
        action="continue",
        metric={"function": "def evaluator_fn(text):\n    return bool(str(text).strip())\n"},
    )

    summarize = LLMNode(name="Summarize", node_id="summarize", model=model_id, output_key="summary")
    search = ToolNode(
        name="Search",
        node_id="search",
        tool_name="search",
        arg_mapping={"query": "summary"},
        result_key="search_results",
    )
    delegate = AgentNode(
        name="Delegate",
        node_id="delegate",
        agent_name=specialist.name,
        agent_prompt="Use this evidence: {{search_results}}",
        output_key="draft",
    )
    graph_inspector = InspectorNode(
        name="Inspect",
        node_id="inspect",
        inspector_type=inspector.name,
        content_key="draft",
        failure_action="warn",
    )
    graph = Graph(
        entry_point=summarize,
        nodes=[summarize, search, delegate, graph_inspector],
        edges=[Edge(summarize, search), Edge(search, delegate), Edge(delegate, graph_inspector)],
    )

    payload = Agent(
        name="Static graph resources",
        llm=model_id,
        tools=[tool],
        agents=[specialist],
        inspectors=[inspector],
        graph=graph,
    ).build_save_payload()

    assert payload["model"] == {"id": model_id}
    assert payload["tools"][0]["id"] == tool_id
    assert payload["tools"][0]["actions"] == ["search"]
    assert payload["agents"] == [{"id": "saved-specialist-id", "inspectors": []}]
    assert payload["inspectors"][0]["name"] == inspector.name
    assert payload["inspectors"][0]["evaluator"]["type"] == "function"
    assert payload["graph"]["nodes"]["search"]["tool_name"] == "search"
    assert payload["graph"]["nodes"]["search"]["arg_mapping"] == {"query": "summary"}
    assert payload["graph"]["nodes"]["delegate"]["agent_name"] == specialist.name
    assert payload["graph"]["nodes"]["inspect"]["inspector_type"] == inspector.name
