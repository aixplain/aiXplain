from typing import Union
from .base import Node, Link, Param


class LinkableMixin:
    """
    Linkable mixin class, this class will be used to link the output of the
    node to the input of another node.

    This class will be used to link the output of the node to the input of
    another node.
    """

    def link(
        self,
        to_node: Node,
        from_param: Union[str, Param],
        to_param: Union[str, Param],
    ) -> Link:
        """
        Link the output of the node to the input of another node. This method
        will link the output of the node to the input of another node.

        :param to_node: the node to link to the output
        :param from_param: the output parameter or the code of the output
        parameter
        :param to_param: the input parameter or the code of the input parameter
        :return: the link
        """
        return Link(
            pipeline=self.pipeline,
            from_node=self,
            to_node=to_node,
            from_param=from_param,
            to_param=to_param,
        )


class RoutableMixin:
    """
    Routable mixin class, this class will be used to route the input data to
    different nodes based on the input data type.
    """

    def route(self, *params: Param) -> Node:
        """
        Route the input data to different nodes based on the input data type.
        This method will automatically link the input data to the output data
        of the node.

        :param params: the output parameters
        :return: the router node
        """
        assert self.pipeline, "Node not attached to a pipeline"

        router = self.pipeline.router([(param.data_type, param.node) for param in params])
        self.outputs.input.link(router.inputs.input)
        for param in params:
            router.outputs.input.link(param)
        return router


class OutputableMixin:
    """
    Outputable mixin class, this class will be used to link the output of the
    node to the output node of the pipeline.
    """

    def use_output(self, param: Union[str, Param]) -> Node:
        """
        Use the output of the node as the output of the pipeline.
        This method will automatically link the output of the node to the
        output node of the pipeline.

        :param param: the output parameter or the code of the output parameter
        :return: the output node
        """
        assert self.pipeline, "Node not attached to a pipeline"
        output = self.pipeline.output()
        if isinstance(param, str):
            param = self.outputs[param]
        param.link(output.inputs.output)
        return output
