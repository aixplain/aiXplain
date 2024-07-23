import pytest
import unittest.mock as mock

from aixplain.api import (
    Node,
    Pipeline,
    ParamProxy,
    NodeType,
    Link,
    ParamMapping,
    InputParam,
    OutputParam,
    ParamType,
    DataType,
    LinkableMixin,
)


def test_create_node():
    node = Node()
    assert node.pipeline is None
    assert isinstance(node.inputs, ParamProxy)
    assert isinstance(node.outputs, ParamProxy)

    pipeline = Pipeline()

    with pytest.raises(AssertionError):
        node = Node(pipeline=pipeline)

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode(pipeline=pipeline)
    assert pipeline.nodes == [node]
    assert node.pipeline is pipeline
    assert node.number == 0
    assert node.label == "INPUT(ID=0)"

    node1 = InputNode(pipeline=pipeline)
    assert pipeline.nodes == [node, node1]
    assert node1.pipeline is pipeline
    assert node1.number == 1
    assert node1.label == "INPUT(ID=1)"


def test_create_pipeline():
    pipeline = Pipeline()

    assert pipeline.nodes == []
    assert pipeline.links == []
    assert not pipeline.instance


@pytest.mark.parametrize(
    "param_cls, expected_param_type",
    [
        (InputParam, ParamType.INPUT),
        (OutputParam, ParamType.OUTPUT),
    ],
)
def test_create_input_output_param(param_cls, expected_param_type):
    param = param_cls(code="param", dataType=DataType.TEXT, value="foo")
    assert param.code == "param"
    assert param.dataType == DataType.TEXT
    assert param.value == "foo"
    assert param.param_type == expected_param_type
    assert not param.node

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    param = param_cls(
        code="param", dataType=DataType.TEXT, value="foo", node=node
    )
    assert param.code == "param"
    assert param.dataType == DataType.TEXT
    assert param.value == "foo"
    assert param.param_type == expected_param_type
    with mock.patch.object(param, "attach") as mock_attach:
        param.attach()
        mock_attach.assert_called_once()


def test_param_attach():
    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    input = InputParam(code="input", dataType=DataType.TEXT, value="foo")

    input.attach(node)
    assert input in node.inputValues
    assert input.node is node

    output = OutputParam(code="output", dataType=DataType.TEXT, value="bar")

    output.attach(node)
    assert output in node.outputValues
    assert output.node is node


def test_param_link():
    input = InputParam(code="input", dataType=DataType.TEXT, value="foo")
    output = OutputParam(code="output", dataType=DataType.TEXT, value="bar")

    with pytest.raises(AssertionError):
        output.link(input)

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    input = InputParam(code="input", dataType=DataType.TEXT, value="foo")
    output = OutputParam(
        code="output", dataType=DataType.TEXT, value="bar", node=node
    )

    with pytest.raises(AssertionError):
        input.link(output)

    with mock.patch.object(input, "back_link") as mock_back_link:
        output.link(input)
        mock_back_link.assert_called_once_with(output)


def test_param_back_link():
    input = InputParam(code="input", dataType=DataType.TEXT, value="foo")
    output = OutputParam(code="output", dataType=DataType.TEXT, value="bar")

    with pytest.raises(AssertionError):
        input.back_link(output)

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(
        code="output", dataType=DataType.TEXT, value="bar", node=a
    )
    input = InputParam(
        code="input", dataType=DataType.TEXT, value="foo", node=b
    )

    with pytest.raises(AssertionError):
        output.back_link(input)

    with mock.patch.object(a, "link") as mock_node_link:
        input.back_link(output)
        mock_node_link.assert_called_once_with(b, output.code, input.code)


def test_node_link():

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(
        code="output", dataType=DataType.TEXT, value="bar", node=a
    )
    input = InputParam(
        code="input", dataType=DataType.TEXT, value="foo", node=b
    )

    with pytest.raises(AssertionError):
        a.link(b, output.code, input.code)

    pipeline = Pipeline()
    pipeline.add_nodes(a, b)

    with mock.patch.object(a, "validate") as mock_node_validate:
        a.link(b, output, input)
        mock_node_validate.assert_called_once()

    assert len(pipeline.links) == 1
    assert pipeline.links[0].from_node == a.number
    assert pipeline.links[0].to_node == b.number
    assert pipeline.links[0].paramMapping == [
        ParamMapping(from_param="output", to_param="input")
    ]

    c = AssetNode(pipeline)
    d = AssetNode(pipeline)
    c.link(d)
    assert len(pipeline.links) == 2
    assert pipeline.links[1].from_node == c.number
    assert pipeline.links[1].to_node == d.number
    assert pipeline.links[1].paramMapping == []


def test_add_node():
    pipeline = Pipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()
    pipeline.add_node(node)
    assert pipeline.nodes == [node]
    assert pipeline.links == []

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node1 = AssetNode()
    pipeline.add_node(node1)
    assert pipeline.nodes == [node, node1]
    assert pipeline.links == []

    class OutputNode(Node):
        type: NodeType = NodeType.OUTPUT

    node2 = OutputNode()
    pipeline.add_node(node2)
    assert pipeline.nodes == [node, node1, node2]
    assert pipeline.links == []


def test_add_link():
    pipeline = Pipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()
    pipeline.add_node(node)

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node1 = AssetNode()
    pipeline.add_node(node1)

    link = Link(
        from_node=node,
        to_node=node1,
        paramMapping=[ParamMapping(from_param="output", to_param="input")],
    )
    pipeline.add_link(link)
