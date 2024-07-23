from typing import Union

from .base import Node, Link, Param, ParamMapping


class LinkableMixin:
    """
    Linkable mixin class, this class will be used to link the output of the
    node to the input of another node.

    This class will be used to link the output of the node to the input of
    another node.
    """

    def validate(
        self,
        to_node: Node,
        from_param: Union[str, Param] = None,
        to_param: Union[str, Param] = None,
    ) -> None:
        """
        Validate the link between the nodes. This method will validate if the
        link between the nodes is valid.

        :param to_node: the node to link to
        :param from_param: the output parameter or the code of the output
        parameter
        :param to_param: the input parameter or the code of the input parameter
        :raises ValueError: if the link is not valid
        """
        if from_param:
            if isinstance(from_param, str):
                from_param = self.outputs[from_param]
            assert from_param, "From param not found"

        if to_param:
            if isinstance(to_param, str):
                to_param = to_node.inputs[to_param]
            assert to_param, "To param not found"

        # if from_param and to_param:
        #     # validate if both params has the same data type
        #     # if they're not none
        #     if from_param.dataType and to_param.dataType:
        #         if from_param.dataType != to_param.dataType:
        #             raise ValueError(
        #                 f"Param {from_param.code} and {to_param.code} "
        #                 "have different data types"
        #             )

    def link(
        self,
        to_node: Node,
        from_param: Union[str, Param] = None,
        to_param: Union[str, Param] = None,
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

        assert self.pipeline, "Node not added to a pipeline"
        assert to_node.pipeline, "Node not added to a pipeline"

        self.validate(to_node, from_param, to_param)

        param_mapping = []
        if from_param and to_param:
            param_mapping = [
                ParamMapping(from_param=from_param, to_param=to_param)
            ]

        return Link(
            pipeline=self.pipeline,
            from_node=self.number,
            to_node=to_node.number,
            paramMapping=param_mapping,
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
        assert self.pipeline, "Node not added to a pipeline"

        router = self.pipeline.router(
            [(param.dataType, param.node) for param in params]
        )
        self.link(router)
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
        assert self.pipeline, "Node not added to a pipeline"
        output = self.pipeline.output()
        param = param if isinstance(param, Param) else self.outputs[param]
        param.link(output.inputs.output)
        return output
