import pytest
from unittest.mock import patch, Mock, call

from aixplain.enums import DataType
from aixplain.modules.pipeline.designer.base import (
    Node,
    Link,
    Param,
    ParamProxy,
    Inputs,
    Outputs,
    InputParam,
    OutputParam,
)

from aixplain.modules.pipeline.designer.enums import (
    ParamType,
    NodeType,
)

from aixplain.modules.pipeline.designer.mixins import LinkableMixin
from aixplain.modules.pipeline.designer.pipeline import DesignerPipeline
from aixplain.modules.pipeline.designer.base import find_prompt_params


def test_create_node():

    pipeline = DesignerPipeline()

    class BareNode(Node):
        pass

    with patch("aixplain.modules.pipeline.designer.Node.attach_to") as mock_attach_to:
        node = BareNode(number=3, label="FOO")
        mock_attach_to.assert_not_called()
        assert isinstance(node.inputs, Inputs)
        assert isinstance(node.outputs, Outputs)
        assert node.number == 3
        assert node.label == "FOO"

    class FooNodeInputs(Inputs):
        pass

    class FooNodeOutputs(Outputs):
        pass

    class FooNode(Node[FooNodeInputs, FooNodeOutputs]):
        inputs_class = FooNodeInputs
        outputs_class = FooNodeOutputs

    with patch("aixplain.modules.pipeline.designer.Node.attach_to") as mock_attach_to:
        node = FooNode(pipeline=pipeline, number=3, label="FOO")
        mock_attach_to.assert_called_once_with(pipeline)
        assert isinstance(node.inputs, FooNodeInputs)
        assert isinstance(node.outputs, FooNodeOutputs)
        assert node.number == 3
        assert node.label == "FOO"


def test_node_attach_to():

    pipeline = DesignerPipeline()

    class BareNode(Node):
        pass

    node = BareNode()
    with pytest.raises(AssertionError) as excinfo:
        node.attach_to(pipeline)

    assert "Node type not set" in str(excinfo.value)

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()
    c = AssetNode()
    d = AssetNode(number=8)
    e = AssetNode(number=8)

    a.attach_to(pipeline)
    b.attach_to(pipeline)
    assert b.pipeline is pipeline
    assert b.number == 1
    assert b.label == "ASSET(ID=1)"
    assert b in pipeline.nodes
    assert len(pipeline.nodes) == 2

    c.attach_to(pipeline)
    assert c.pipeline is pipeline
    assert c.number == 2
    assert c.label == "ASSET(ID=2)"
    assert c in pipeline.nodes
    assert len(pipeline.nodes) == 3

    d.attach_to(pipeline)
    assert d.pipeline is pipeline
    assert d.number == 8
    assert d.label == "ASSET(ID=8)"
    assert d in pipeline.nodes
    assert len(pipeline.nodes) == 4

    with pytest.raises(AssertionError) as excinfo:
        e.attach_to(pipeline)

    assert "Node number already exists" in str(excinfo.value)


def test_node_serialize():
    pipeline = DesignerPipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node = AssetNode()

    with patch.object(node.inputs, "serialize") as mock_inputs_serialize:
        with patch.object(node.outputs, "serialize") as mock_outputs_serialize:
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

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
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

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
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

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
        param = UnTypedParam(
            code="param",
            data_type=DataType.TEXT,
            value="foo",
            param_type=ParamType.OUTPUT,
        )
        mock_attach_to.assert_not_called()

    assert param.param_type == ParamType.OUTPUT

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
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

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
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

    with patch("aixplain.modules.pipeline.designer.Param.attach_to") as mock_attach_to:
        param = param_cls(code="param", data_type=DataType.TEXT, value="foo", node=node)
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

    with patch.object(node.inputs, "add_param") as mock_add_param:
        input.attach_to(node)
        mock_add_param.assert_called_once_with(input)
    assert input.node is node

    with pytest.raises(AssertionError) as excinfo:
        input.attach_to(node)

    assert "Param already attached to a node" in str(excinfo.value)

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar")

    with patch.object(node.outputs, "add_param") as mock_add_param:
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

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar", node=a)
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo", node=b)

    with patch.object(input, "back_link") as mock_back_link:
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

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar", node=a)
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo", node=b)

    with patch.object(a, "link") as mock_link:
        input.back_link(output)
        mock_link.assert_called_once_with(b, output, input)


def test_create_pipeline():
    pipeline = DesignerPipeline()

    assert pipeline.nodes == []
    assert pipeline.links == []
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

    pipeline = DesignerPipeline()

    with patch("aixplain.modules.pipeline.designer.Link.attach_to") as mock_attach_to:
        link = Link(
            from_node=a,
            to_node=b,
            from_param="output",
            to_param="input",
            pipeline=pipeline,
        )
        mock_attach_to.assert_called_once_with(pipeline)


def test_link_attach_to():

    pipeline = DesignerPipeline()

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

    with patch.object(a, "attach_to") as mock_a_attach_to:
        with patch.object(b, "attach_to") as mock_b_attach_to:
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

    with patch.object(a, "attach_to") as mock_a_attach_to:
        with patch.object(b, "attach_to") as mock_b_attach_to:
            link.attach_to(pipeline)
            mock_a_attach_to.assert_not_called()
            mock_b_attach_to.assert_not_called()
            assert link.pipeline is pipeline
            assert link in pipeline.links

    with pytest.raises(AssertionError) as excinfo:
        link.attach_to(pipeline)

    assert "Link already attached to a pipeline" in str(excinfo.value)


def test_link_serialize():
    pipeline = DesignerPipeline()

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

    with patch.object(param_proxy, "_create_param") as mock_create_param:
        with patch.object(param_proxy, "add_param") as mock_add_param:
            param = param_proxy.create_param("foo", DataType.TEXT, "bar", is_required=True)
            mock_create_param.assert_called_once_with("foo", DataType.TEXT, "bar")
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


def test_param_proxy_set_param_value():
    prompt_param = Mock(spec=Param, code="prompt")
    param_proxy = ParamProxy(Mock())
    param_proxy._params = [prompt_param]
    with patch.object(param_proxy, "special_prompt_handling") as mock_special_prompt_handling:
        param_proxy.prompt = "hello {{foo}}"
        mock_special_prompt_handling.assert_called_once_with("prompt", "hello {{foo}}")
        assert prompt_param.value == "hello {{foo}}"

        # Use a non string value
        param_proxy.prompt = 123
        assert prompt_param.value == 123

        # Now change it to another non string value
        param_proxy.prompt = 456
        assert prompt_param.value == 456


def test_param_proxy_special_prompt_handling():
    from aixplain.modules.pipeline.designer.nodes import AssetNode

    asset_node = Mock(spec=AssetNode, asset=Mock(function="text-generation"))
    param_proxy = ParamProxy(asset_node)
    with patch("aixplain.modules.pipeline.designer.base.find_prompt_params") as mock_find_prompt_params:
        mock_find_prompt_params.return_value = []
        param_proxy.special_prompt_handling("prompt", "hello {{foo}}")
        mock_find_prompt_params.assert_called_once_with("hello {{foo}}")
        asset_node.inputs.create_param.assert_not_called()
        asset_node.reset_mock()
        mock_find_prompt_params.reset_mock()

        mock_find_prompt_params.return_value = ["foo"]
        param_proxy.special_prompt_handling("prompt", "hello {{foo}}")
        mock_find_prompt_params.assert_called_once_with("hello {{foo}}")
        asset_node.inputs.create_param.assert_called_once_with("foo", DataType.TEXT, is_required=True)
        asset_node.reset_mock()
        mock_find_prompt_params.reset_mock()

        mock_find_prompt_params.return_value = ["foo", "bar"]
        param_proxy.special_prompt_handling("prompt", "hello {{foo}} {{bar}}")
        mock_find_prompt_params.assert_called_once_with("hello {{foo}} {{bar}}")
        assert asset_node.inputs.create_param.call_count == 2
        assert asset_node.inputs.create_param.call_args_list == [
            call("foo", DataType.TEXT, is_required=True),
            call("bar", DataType.TEXT, is_required=True),
        ]


def test_node_link():
    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    b = AssetNode()

    output = OutputParam(code="output", data_type=DataType.TEXT, value="bar", node=a)
    input = InputParam(code="input", data_type=DataType.TEXT, value="foo", node=b)

    # here too lazy to mock Link class properly
    # checking the output instance instead
    link = a.link(b, from_param=output, to_param=input)
    assert isinstance(link, Link)
    assert link.from_node == a
    assert link.to_node == b
    assert link.from_param == "output"
    assert link.to_param == "input"


def test_pipeline_add_node():
    pipeline = DesignerPipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()
    pipeline.add_node(node)
    assert pipeline.nodes == [node]
    assert pipeline.links == []

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    node1 = AssetNode()
    with patch.object(node1, "attach_to") as mock_attach_to:
        pipeline.add_node(node1)
        mock_attach_to.assert_called_once_with(pipeline)


def test_pipeline_add_nodes():
    pipeline = DesignerPipeline()

    class InputNode(Node):
        type: NodeType = NodeType.INPUT

    node = InputNode()

    with patch.object(pipeline, "add_node") as mock_add_node:
        pipeline.add_nodes(node)
        assert mock_add_node.call_count == 1

    node1 = InputNode()
    node2 = InputNode()

    with patch.object(pipeline, "add_node") as mock_add_node:
        pipeline.add_nodes(node1, node2)
        assert mock_add_node.call_count == 2


def test_pipeline_add_link():
    pipeline = DesignerPipeline()

    class AssetNode(Node):
        type: NodeType = NodeType.ASSET

    a = AssetNode()
    a.outputs.create_param("output", DataType.TEXT)
    b = AssetNode()
    b.inputs.create_param("input", DataType.TEXT)

    link = Link(from_node=a, to_node=b, from_param="output", to_param="input")
    pipeline.add_link(link)

    with patch.object(link, "attach_to") as mock_attach_to:
        pipeline.add_link(link)
        mock_attach_to.assert_called_once_with(pipeline)


def test_pipeline_decision_node_passthrough_linking():
    from aixplain.modules.pipeline.designer import Route
    from aixplain.modules.pipeline.designer.nodes import Input, Output, Decision

    input_node = Input()
    output_node = Output()

    decision_node = Decision(routes=[Mock(spec=Route)])

    # Decision node "passthrough" param should be linked first to infer output param "data"
    with pytest.raises(ValueError):
        decision_node.link(output_node, from_param="data", to_param="output")

    # Link the "passthrough" param to the asset node
    input_node.outputs.input.link(decision_node.inputs.passthrough)

    # Now we can link the "data" param to the asset node
    decision_node.link(output_node, from_param="data", to_param="output")

    assert decision_node.outputs.data.link_ is not None
    assert decision_node.outputs.data.link_.from_node == decision_node
    assert decision_node.outputs.data.link_.to_node == output_node
    assert decision_node.outputs.data.link_.to_param == "output"
    assert decision_node.outputs.data.data_type == input_node.outputs.input.data_type
    assert decision_node.outputs.data.link_.data_source_id == input_node.number


def test_pipeline_special_prompt_validation():
    from aixplain.modules.pipeline.designer.nodes import AssetNode

    pipeline = DesignerPipeline()
    asset_node = Mock(
        spec=AssetNode,
        label="LLM(ID=1)",
        asset=Mock(function="text-generation"),
        inputs=Mock(prompt=Mock(value="hello {{foo}}"), text=Mock(is_required=True)),
    )
    with patch.object(pipeline, "is_param_set") as mock_is_param_set:
        mock_is_param_set.return_value = False
        pipeline.special_prompt_validation(asset_node)
        mock_is_param_set.assert_called_once_with(asset_node, asset_node.inputs.prompt)
        assert asset_node.inputs.text.is_required is True
        mock_is_param_set.reset_mock()
        mock_is_param_set.return_value = True
        with patch("aixplain.modules.pipeline.designer.pipeline.find_prompt_params") as mock_find_prompt_params:
            mock_find_prompt_params.return_value = []
            pipeline.special_prompt_validation(asset_node)
            mock_is_param_set.assert_called_once_with(asset_node, asset_node.inputs.prompt)
            mock_find_prompt_params.assert_called_once_with(asset_node.inputs.prompt.value)
            assert asset_node.inputs.text.is_required is True

            mock_is_param_set.reset_mock()
            mock_is_param_set.return_value = True
            mock_find_prompt_params.reset_mock()
            mock_find_prompt_params.return_value = ["foo"]
            asset_node.inputs.__contains__ = Mock(return_value=False)

            with pytest.raises(
                ValueError,
                match="Param foo of node LLM\\(ID=1\\) should be defined and set",
            ):
                pipeline.special_prompt_validation(asset_node)

            mock_is_param_set.assert_called_once_with(asset_node, asset_node.inputs.prompt)
            mock_find_prompt_params.assert_called_once_with(asset_node.inputs.prompt.value)
            assert asset_node.inputs.text.is_required is False

            mock_is_param_set.reset_mock()
            mock_is_param_set.return_value = True
            mock_find_prompt_params.reset_mock()
            mock_find_prompt_params.return_value = ["foo"]
            asset_node.inputs.text.is_required = True

            asset_node.inputs.__contains__ = Mock(return_value=True)
            pipeline.special_prompt_validation(asset_node)
            mock_is_param_set.assert_called_once_with(asset_node, asset_node.inputs.prompt)
            mock_find_prompt_params.assert_called_once_with(asset_node.inputs.prompt.value)
            assert asset_node.inputs.text.is_required is False


@pytest.mark.parametrize(
    "input, expected",
    [
        ("hello {{foo}}", ["foo"]),
        ("hello {{foo}} {{bar}}", ["foo", "bar"]),
        ("hello {{foo}} {{bar}} {{baz}}", ["foo", "bar", "baz"]),
        # no match cases
        ("hello bar", []),
        ("hello {{foo]] bar", []),
        ("hello {foo} bar", []),
        # edge cases
        ("", []),
        ("{{}}", []),
        # interesting cases
        ("hello {{foo {{bar}} baz}} {{bar}} {{baz}}", ["foo {{bar", "bar", "baz"]),
    ],
)
def test_find_prompt_params(input, expected):
    print(input, expected)
    assert find_prompt_params(input) == expected


def test_pipeline_serialize():
    pipeline = DesignerPipeline()

    # Create nodes
    class AssetNode(Node, LinkableMixin):
        type: NodeType = NodeType.ASSET

    node1 = AssetNode(pipeline=pipeline)
    node2 = AssetNode(pipeline=pipeline)

    # Create multiple parameters for each node
    node1.outputs.create_param("output1", DataType.TEXT, "foo1")
    node1.outputs.create_param("output2", DataType.TEXT, "foo2")
    node2.inputs.create_param("input1", DataType.TEXT, "bar1")
    node2.inputs.create_param("input2", DataType.TEXT, "bar2")

    # Create multiple links between the same nodes
    link1 = Link(
        from_node=node1,
        to_node=node2,
        from_param="output1",
        to_param="input1",
    )
    pipeline.add_link(link1)

    link2 = Link(
        from_node=node1,
        to_node=node2,
        from_param="output2",
        to_param="input2"
    )
    pipeline.add_link(link2)

    serialized = pipeline.serialize()

    # Verify pipeline serialization
    assert len(serialized["links"]) == 1
    assert len(serialized["links"][0]["paramMapping"]) == 2
    assert {"from": "output1", "to": "input1"} in serialized["links"][0]["paramMapping"]
    assert {"from": "output2", "to": "input2"} in serialized["links"][0]["paramMapping"]
    assert serialized["nodes"][0] == node1.serialize()
    assert serialized["nodes"][1] == node2.serialize()
