import pytest
import unittest.mock as mock

from aixplain.api import (
    Node,
    Pipeline,
    NodeType,
    Link,
    Param,
    ParamProxy,
    Inputs,
    Outputs,
    InputParam,
    OutputParam,
    ParamType,
    LinkableMixin,
    DataType,
)


def test_create_node():

    pipeline = Pipeline()

    class BareNode(Node):
        pass

    with mock.patch("aixplain.api.Node.attach_to") as mock_attach_to:
        node = BareNode()
        mock_attach_to.assert_not_called()
        assert isinstance(node.inputs, Inputs)
        assert isinstance(node.outputs, Outputs)

    class FooNodeInputs(Inputs):
        pass

    class FooNodeOutputs(Outputs):
        pass

    class FooNode(Node[FooNodeInputs, FooNodeOutputs]):
        inputs_class = FooNodeInputs
        outputs_class = FooNodeOutputs

    with mock.patch("aixplain.api.Node.attach_to") as mock_attach_to:
        node = FooNode(pipeline=pipeline)
        mock_attach_to.assert_called_once_with(pipeline)
        assert isinstance(node.inputs, FooNodeInputs)
        assert isinstance(node.outputs, FooNodeOutputs)


def test_node_attach_to():

    pipeline = Pipeline()

    class BareNode(Node):
        pass

    node = BareNode()
    with pytest.raises(AssertionError) as excinfo:
        node.attach_to(pipeline)

    assert "Node type not set" in str(excinfo.value)

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    node.number = 0
    with pytest.raises(AssertionError) as excinfo:
        node.attach_to(pipeline)

    assert "Node number already set" in str(excinfo.value)

    node = AssetNode()
    node.label = "ASSET(ID=0)"

    with pytest.raises(AssertionError) as excinfo:
        node.attach_to(pipeline)

    assert "Node label already set" in str(excinfo.value)

    node = AssetNode()
    node.attach_to(pipeline)
    assert node.pipeline is pipeline
    assert node.number == 0
    assert node.label == "ASSET(ID=0)"
    assert node in pipeline.nodes
    assert len(pipeline.nodes) == 1

    node1 = AssetNode()
    node1.attach_to(pipeline)
    assert node1.pipeline is pipeline
    assert node1.number == 1
    assert node1.label == "ASSET(ID=1)"
    assert node in pipeline.nodes
    assert len(pipeline.nodes) == 2

    with pytest.raises(AssertionError) as excinfo:
        node.attach_to(pipeline)

    assert "Node already attached to a pipeline" in str(excinfo.value)


def test_node_serialize():
    pipeline = Pipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    with mock.patch.object(node.inputs, "serialize") as mock_inputs_serialize:
        with mock.patch.object(
            node.outputs, "serialize"
        ) as mock_outputs_serialize:
            assert node.serialize() == {
                "number": node.number,
                "type": NodeType.ASSET,
                "inputValues": mock_inputs_serialize.return_value,
                "outputValues": mock_outputs_serialize.return_value,
                "label": node.label,
            }
            node.attach_to(pipeline)
            mock_inputs_serialize.assert_called_once()
            mock_outputs_serialize.assert_called_once()
            mock_inputs_serialize.reset_mock()
            mock_outputs_serialize.reset_mock()

            assert node.serialize() == {
                "number": node.number,
                "type": NodeType.ASSET,
                "inputValues": mock_inputs_serialize.return_value,
                "outputValues": mock_outputs_serialize.return_value,
                "label": node.label,
            }
            mock_inputs_serialize.assert_called_once()
            mock_outputs_serialize.assert_called_once()


def test_create_param():

    class TypedParam(Param):
        param_type = ParamType.INPUT

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = TypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
        )
        mock_attach_to.assert_not_called()

    assert param.code == "param"
    assert param.data_type == DataType.TEXT
    assert param.value == "foo"
    assert param.param_type == ParamType.INPUT

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = TypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
            param_type=ParamType.OUTPUT,
        )
        mock_attach_to.assert_not_called()

    assert param.code == "param"
    assert param.data_type == DataType.TEXT
    assert param.value == "foo"
    assert param.param_type == ParamType.INPUT

    class UnTypedParam(Param):
        pass

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = UnTypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
            param_type=ParamType.OUTPUT,
        )
        mock_attach_to.assert_not_called()

    assert param.param_type == ParamType.OUTPUT

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = UnTypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
            param_type=ParamType.INPUT,
        )
        mock_attach_to.assert_not_called()

    assert param.param_type == ParamType.INPUT

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = UnTypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
            param_type=ParamType.INPUT,
            node=node,
        )
        mock_attach_to.assert_called_once_with(node)


@pytest.mark.parametrize(
    "param_cls, expected_param_type",
    [
        (InputParam, ParamType.INPUT),
        (OutputParam, ParamType.OUTPUT),
    ],
)
def test_create_input_output_param(param_cls, expected_param_type):
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    with mock.patch("aixplain.api.Param.attach_to") as mock_attach_to:
        param = param_cls(
            code="param", data_type=DataType.TEXT, value="foo", node=node
        )
        mock_attach_to.assert_called_once_with(node)
        assert param.code == "param"
        assert param.data_type == DataType.TEXT
        assert param.value == "foo"
        assert param.param_type == expected_param_type
        assert not param.node


def test_param_attach_to():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    class NoTypeParam(Param):
        pass

    param = NoTypeParam(code="param", data_type=DataType.TEXT, value="foo")
    with pytest.raises(AssertionError) as excinfo:
        param.attach_to(node)

    assert "Param type not set" in str(excinfo.value)

    input = InputParam(code="input", data_type=DataType.TEXT, value="foo")

    with mock.patch.object(node.inputs, "add_param") as mock_add_param:
        input.attach_to(node)
        mock_add_param.assert_called_once_with(input)
    assert input.node is node

    with pytest.raises(AssertionError) as excinfo:
        input.attach_to(node)

    assert "Param already attached to a node" in str(excinfo.value)

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")

    with mock.patch.object(node.outputs, "add_param") as mock_add_param:
        output.attach_to(node)
        mock_add_param.assert_called_once_with(output)
    assert output.node is node


def test_param_link():
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo")
    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")

    with pytest.raises(AssertionError) as excinfo:
        output.link(input)

    assert "Param not attached to a node" in str(excinfo.value)

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")
    output.node = a
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo")
    input.node = b

    with pytest.raises(AssertionError) as excinfo:
        input.link(output)

    assert "Invalid param type" in str(excinfo.value)

    with pytest.raises(AssertionError) as excinfo:
        output.link(input)

    assert "Param not registered as output" in str(excinfo.value)

    output = OutputParam(
        code="output", data_type=DataType.TEXT, value="bar", node=a
    )
    input = InputParam(
        code="input", data_type=DataType.TEXT, value="foo", node=b
    )

    with mock.patch.object(input, "back_link") as mock_back_link:
        output.link(input)
        mock_back_link.assert_called_once_with(output)


def test_param_back_link():
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo")
    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")

    with pytest.raises(AssertionError) as excinfo:
        input.back_link(output)

    assert "Param not attached to a node" in str(excinfo.value)

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")
    output.node = a
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo")
    input.node = b

    with pytest.raises(AssertionError) as excinfo:
        output.back_link(input)

    assert "Invalid param type" in str(excinfo.value)

    with pytest.raises(AssertionError) as excinfo:
        input.back_link(output)

    assert "Param not registered as input" in str(excinfo.value)

    output = OutputParam(
        code="output", data_type=DataType.TEXT, value="bar", node=a
    )
    input = InputParam(
        code="input", data_type=DataType.TEXT, value="foo", node=b
    )

    with mock.patch.object(a, "link") as mock_link:
        input.back_link(output)
        mock_link.assert_called_once_with(b, output, input)


def test_create_pipeline():
    pipeline = Pipeline(name="foo")

    assert pipeline.nodes == []
    assert pipeline.links == []
    assert pipeline.name == "foo"
    assert not pipeline.instance


def test_link_create():
    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    with pytest.raises(AssertionError) as excinfo:
        link = Link(
            from_node=a,
            to_node=b,
            from_param="output",
            to_param="input",
        )

    assert "Invalid from param" in str(excinfo.value)

    a.outputs.create_param("output", DataType.TEXT, "foo")

    with pytest.raises(AssertionError) as excinfo:
        link = Link(
            from_node=a,
            to_node=b,
            from_param="output",
            to_param="input",
        )

    assert "Invalid to param" in str(excinfo.value)

    b.inputs.create_param("input", DataType.TEXT, "bar")

    link = Link(
        from_node=a,
        to_node=b,
        from_param="output",
        to_param="input",
    )

    assert link.from_node == a
    assert link.to_node == b
    assert link.from_param == "output"
    assert link.to_param == "input"

    pipeline = Pipeline()

    with mock.patch("aixplain.api.Link.attach_to") as mock_attach_to:
        link = Link(
            from_node=a,
            to_node=b,
            from_param="output",
            to_param="input",
            pipeline=pipeline,
        )
        mock_attach_to.assert_called_once_with(pipeline)


def test_link_attach_to():

    pipeline = Pipeline()

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    a.outputs.create_param("output", DataType.TEXT, "foo")
    b.inputs.create_param("input", DataType.TEXT, "bar")

    link = Link(
        from_node=a,
        to_node=b,
        from_param="output",
        to_param="input",
    )

    with mock.patch.object(a, "attach_to") as mock_a_attach_to:
        with mock.patch.object(b, "attach_to") as mock_b_attach_to:
            link.attach_to(pipeline)
            mock_a_attach_to.assert_called_once_with(pipeline)
            mock_b_attach_to.assert_called_once_with(pipeline)
            assert link.pipeline is pipeline
            assert link in pipeline.links

    a = AssetNode(pipeline=pipeline)
    b = AssetNode(pipeline=pipeline)
    a.outputs.create_param("output", DataType.TEXT, "foo")
    b.inputs.create_param("input", DataType.TEXT, "bar")

    link = Link(
        from_node=a,
        to_node=b,
        from_param="output",
        to_param="input",
    )

    with mock.patch.object(a, "attach_to") as mock_a_attach_to:
        with mock.patch.object(b, "attach_to") as mock_b_attach_to:
            link.attach_to(pipeline)
            mock_a_attach_to.assert_not_called()
            mock_b_attach_to.assert_not_called()
            assert link.pipeline is pipeline
            assert link in pipeline.links

    with pytest.raises(AssertionError) as excinfo:
        link.attach_to(pipeline)

    assert "Link already attached to a pipeline" in str(excinfo.value)


def test_link_serialize():
    pipeline = Pipeline()

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()
    a.outputs.create_param("output", DataType.TEXT, "foo")
    b.inputs.create_param("input", DataType.TEXT, "bar")

    link = Link(
        from_node=a,
        to_node=b,
        from_param="output",
        to_param="input",
    )

    with pytest.raises(AssertionError) as excinfo:
        link.serialize()

    assert "From node number not set" in str(excinfo.value)
    a.attach_to(pipeline)

    with pytest.raises(AssertionError) as excinfo:
        link.serialize()

    assert "To node number not set" in str(excinfo.value)
    b.attach_to(pipeline)

    link = Link(
        from_node=a,
        to_node=b,
        from_param="output",
        to_param="input",
    )

    assert link.serialize() == {
        "from": a.number,
        "to": b.number,
        "paramMapping": [
            {"from": "output", "to": "input"},
        ],
    }


def test_create_param_proxy():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    param_proxy = ParamProxy(node)
    assert param_proxy.node is node
    assert param_proxy._params == []


def test_param_proxy_add_param():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    param_proxy = ParamProxy(node)

    class FooParam(Param):
        pass

    param = FooParam(code="foo", data_type=DataType.TEXT)
    param_proxy.add_param(param)
    assert param in param_proxy._params
    assert hasattr(param_proxy, "foo")
    assert param_proxy.foo is param
    assert param_proxy.foo.code == "foo"
    assert param_proxy.foo.data_type == DataType.TEXT

    with pytest.raises(ValueError) as excinfo:
        param_proxy.add_param(param)

    assert "Parameter with code 'foo' already exists." in str(excinfo.value)


def test_param_proxy_create_param():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    param_proxy = ParamProxy(node)

    with mock.patch.object(param_proxy, "_create_param") as mock_create_param:
        with mock.patch.object(param_proxy, "add_param") as mock_add_param:
            param = param_proxy.create_param(
                "foo", DataType.TEXT, "bar", is_required=True
            )
            mock_create_param.assert_called_once_with(
                "foo", DataType.TEXT, "bar"
            )
            mock_add_param.assert_called_once_with(param)
            assert param.is_required is True


def test_param_proxy_attr_access():
    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    param_proxy = ParamProxy(node)

    class FooParam(Param):
        pass

    param = FooParam(code="foo", data_type=DataType.TEXT)
    param_proxy.add_param(param)

    assert param in param_proxy
    assert "foo" in param_proxy
    assert param_proxy["foo"] is param
    assert param_proxy.foo is param

    with pytest.raises(KeyError) as excinfo:
        param_proxy["bar"]

    assert "'bar'" in str(excinfo.value)


def test_node_link():

    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(
        code="output", data_type=DataType.TEXT, value="bar", node=a
    )
    input = InputParam(
        code="input", data_type=DataType.TEXT, value="foo", node=b
    )

    # here too lazy to mock Link class properly
    # checking the output instance instead
    link = a.link(b, from_param=output, to_param=input)
    assert isinstance(link, Link)
    assert link.from_node == a
    assert link.to_node == b
    assert link.from_param == "output"
    assert link.to_param == "input"


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
    with mock.patch.object(node1, "attach_to") as mock_attach_to:
        pipeline.add_node(node1)
        mock_attach_to.assert_called_once_with(pipeline)


def test_pipeline_add_nodes():
    pipeline = Pipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()

    with mock.patch.object(pipeline, "add_node") as mock_add_node:
        pipeline.add_nodes(node)
        assert mock_add_node.call_count == 1

    node1 = InputNode()
    node2 = InputNode()

    with mock.patch.object(pipeline, "add_node") as mock_add_node:
        pipeline.add_nodes(node1, node2)
        assert mock_add_node.call_count == 2


def test_pipeline_add_link():
    pipeline = Pipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    a.outputs.create_param("output", DataType.TEXT)
    b = AssetNode()
    b.inputs.create_param("input", DataType.TEXT)

    link = Link(from_node=a, to_node=b, from_param="output", to_param="input")
    pipeline.add_link(link)

    with mock.patch.object(link, "attach_to") as mock_attach_to:
        pipeline.add_link(link)
        mock_attach_to.assert_called_once_with(pipeline)


def test_pipeline_save():
    pipeline = Pipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()
    node.outputs.create_param("output", DataType.TEXT, "foo")
    pipeline.add_node(node)

    node1 = AssetNode()
    node1.inputs.create_param("input", DataType.TEXT, "bar")
    pipeline.add_node(node1)

    link = Link(
        from_node=node, to_node=node1, from_param="output", to_param="input"
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