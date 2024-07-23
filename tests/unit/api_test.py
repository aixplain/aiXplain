import pytest
import unittest.mock as mock

from aixplain.api import (
    Node,
    Pipeline,
    NodeType,
    Link,
    ParamMapping,
    InputParam,
    OutputParam,
    ParamType,
    LinkableMixin,
    ParamProxy,
    DataType,
)


def test_create_param_mapping():
    param_mapping = ParamMapping(from_param="output", to_param="input")
    assert param_mapping.from_param == "output"
    assert param_mapping.to_param == "input"

    output = OutputParam(code="output", dataType=DataType.TEXT, value="foo")
    input = InputParam(code="input", dataType=DataType.TEXT, value="bar")
    param_mapping = ParamMapping(from_param=output, to_param=input)
    assert param_mapping.from_param == "output"
    assert param_mapping.to_param == "input"


def test_create_node():
    node = Node()
    assert node.pipeline is None
    assert isinstance(node.inputs, ParamProxy)
    assert isinstance(node.outputs, ParamProxy)

    pipeline = Pipeline()

    with pytest.raises(AssertionError) as excinfo:
        node = Node(pipeline=pipeline)

    assert "Node type not set" in str(excinfo.value)

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

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    with mock.patch("aixplain.api.Param.attach") as mock_attach:
        param = param_cls(
            code="param", dataType=DataType.TEXT, value="foo", node=node
        )
        mock_attach.assert_called_once_with(node)
        assert param.code == "param"
        assert param.dataType == DataType.TEXT
        assert param.value == "foo"
        assert param.param_type == expected_param_type


def test_param_attach():
    class AssetNode(Node):
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

    with pytest.raises(AssertionError) as excinfo:
        output.link(input)

    assert "Param not attached to a node" in str(excinfo.value)

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

    with pytest.raises(AssertionError) as excinfo:
        input.link(output)

    assert "Invalid param type" in str(excinfo.value)

    with mock.patch.object(input, "back_link") as mock_back_link:
        output.link(input)
        mock_back_link.assert_called_once_with(output)


def test_param_back_link():
    input = InputParam(code="input", dataType=DataType.TEXT, value="foo")
    output = OutputParam(code="output", dataType=DataType.TEXT, value="bar")

    with pytest.raises(AssertionError) as excinfo:
        input.back_link(output)

    assert "Param not attached to a node" in str(excinfo.value)

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

    with pytest.raises(AssertionError) as excinfo:
        output.back_link(input)

    assert "Invalid param type" in str(excinfo.value)

    with mock.patch.object(a, "link") as mock_node_link:
        input.back_link(output)
        mock_node_link.assert_called_once_with(b, output.code, input.code)


def test_link_create():
    link = Link(
        from_node=0,
        to_node=1,
        paramMapping=[ParamMapping(from_param="output", to_param="input")],
    )
    assert link.from_node == 0
    assert link.to_node == 1
    assert link.paramMapping == [
        ParamMapping(from_param="output", to_param="input")
    ]
    assert not link.pipeline

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    pipeline = Pipeline()
    a = AssetNode(pipeline=pipeline)
    b = AssetNode(pipeline=pipeline)

    pipeline = Pipeline()
    with mock.patch("aixplain.api.Link.attach") as mock_attach:
        link = Link(
            from_node=a.number,
            to_node=b.number,
            paramMapping=[ParamMapping(from_param="output", to_param="input")],
            pipeline=pipeline,
        )
        assert link.from_node == 0
        assert link.to_node == 1
        assert link.paramMapping == [
            ParamMapping(from_param="output", to_param="input")
        ]
        mock_attach.assert_called_once_with(pipeline)


def test_link_attach():

    pipeline = Pipeline()

    link = Link(
        from_node=0,
        to_node=1,
        paramMapping=[ParamMapping(from_param="output", to_param="input")],
    )

    link.attach(pipeline)

    assert link.pipeline is pipeline
    assert link in pipeline.links


def test_param_proxy():
    params = [
        InputParam(code="transcripts", dataType=DataType.TEXT, value="foo"),
        InputParam(code="speakers", dataType=DataType.LABEL, value="bar"),
    ]
    param_proxy = ParamProxy(params)
    assert param_proxy.params == params
    assert param_proxy.transcripts == params[0]
    assert param_proxy.speakers == params[1]

    assert param_proxy["transcripts"] == params[0]
    assert param_proxy["speakers"] == params[1]

    assert param_proxy("transcripts") == params[0]
    assert param_proxy("speakers") == params[1]

    with pytest.raises(AttributeError) as excinfo:
        param_proxy.foo

    assert "Param 'foo' not found" in str(excinfo.value)

    param_proxy.transcripts = "bar"
    assert param_proxy.transcripts.value == "bar"

    param_proxy["transcripts"] = "foo"
    assert param_proxy.transcripts.value == "foo"

    param_proxy("transcripts", "baz")
    assert param_proxy.transcripts.value == "baz"


def test_node_to_dict():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    assert node.to_dict() == {
        "number": node.number,
        "type": NodeType.ASSET,
        "inputValues": [],
        "outputValues": [],
        "label": node.label,
    }


def test_node_attach():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    pipeline = Pipeline()
    node.attach(pipeline)
    assert node.pipeline is pipeline
    assert node.number == 0
    assert node.label == "ASSET(ID=0)"

    node1 = AssetNode()
    node1.attach(pipeline)
    assert node1.pipeline is pipeline
    assert node1.number == 1
    assert node1.label == "ASSET(ID=1)"

    with pytest.raises(AssertionError) as excinfo:
        node.attach(pipeline)

    assert "Node already attached to a pipeline" in str(excinfo.value)

    node = Node()
    with pytest.raises(AssertionError) as excinfo:
        node.attach(pipeline)

    assert "Node type not set" in str(excinfo.value)


def test_node_add_input_output_param():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    node.add_input_param("input", DataType.TEXT, "foo")
    assert len(node.inputValues) == 1
    assert node.inputValues[0].code == "input"
    assert node.inputValues[0].dataType == DataType.TEXT
    assert node.inputValues[0].value == "foo"
    assert node.inputValues[0].node is node

    node.add_input_param("input", DataType.TEXT, "bar")
    assert len(node.inputValues) == 2
    assert node.inputValues[1].code == "input"
    assert node.inputValues[1].dataType == DataType.TEXT
    assert node.inputValues[1].value == "bar"
    assert node.inputValues[1].node is node

    node.add_output_param("output", DataType.TEXT, "bar")
    assert len(node.outputValues) == 1
    assert node.outputValues[0].code == "output"
    assert node.outputValues[0].dataType == DataType.TEXT
    assert node.outputValues[0].value == "bar"
    assert node.outputValues[0].node is node


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

    with pytest.raises(AssertionError) as excinfo:
        a.link(b, output.code, input.code)

    assert "Node not attached to a pipeline" in str(excinfo.value)

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


def test_pipeline_add_node():
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


def test_pipeline_add_nodes():
    pipeline = Pipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()
    pipeline.add_nodes(node)
    assert pipeline.nodes == [node]
    assert pipeline.links == []

    node1 = InputNode()
    node2 = InputNode()
    pipeline.add_nodes(node1, node2)
    assert pipeline.nodes == [node, node1, node2]


def test_pipeline_add_link():
    pipeline = Pipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    pipeline.add_node(node)

    node1 = AssetNode()
    pipeline.add_node(node1)

    link = Link(
        from_node=node,
        to_node=node1,
        paramMapping=[ParamMapping(from_param="output", to_param="input")],
    )
    pipeline.add_link(link)
    with mock.patch.object(link, "attach") as mock_attach:
        pipeline.add_link(link)
        mock_attach.assert_called_once_with(pipeline)


def test_pipeline_save():
    pipeline = Pipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    pipeline.add_node(node)

    node1 = AssetNode()
    pipeline.add_node(node1)

    link = Link(
        from_node=node,
        to_node=node1,
        paramMapping=[ParamMapping(from_param="output", to_param="input")],
    )
    pipeline.add_link(link)

    with mock.patch.object(pipeline, "validate") as mock_validate:
        with mock.patch(
            "aixplain.factories.pipeline_factory.PipelineFactory.create"
        ) as mock_create:
            pipeline.save()
            mock_create.assert_called_once()
            assert pipeline.instance is mock_create.return_value
        mock_validate.assert_called_once()


def test_pipeline_run():
    pipeline = Pipeline()

    with pytest.raises(ValueError) as excinfo:
        pipeline.run()

    assert "Pipeline not saved" in str(excinfo.value)

    pipeline.instance = mock.MagicMock()
    pipeline.run("foo", "bar")
    pipeline.instance.run.assert_called_once_with("foo", "bar")
