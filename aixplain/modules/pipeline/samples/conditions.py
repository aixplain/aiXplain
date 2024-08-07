import json
from aixplain.factories.pipeline_factory import PipelineFactory
from aixplain.modules.pipeline.designer import Route, RouteType, Operation

pipeline = PipelineFactory.init()

# add nodes to the pipeline
input = pipeline.input()

sentiment_analysis = pipeline.sentiment_analysis(
    assetId="6172874f720b09325cbcdc33"
)

positive_output = pipeline.output()
negative_output = pipeline.output()
decision_node = pipeline.decision(
    routes=[
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.EQUAL,
            value="POSITIVE",
            path=[positive_output],
        ),
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.DIFFERENT,
            value="POSITIVE",
            path=[negative_output],
        ),
    ]
)

# link the nodes
input.outputs.input.link(sentiment_analysis.inputs.text)
sentiment_analysis.outputs.data.link(decision_node.inputs.comparison)
input.outputs.input.link(decision_node.inputs.passthrough)
decision_node.outputs.input.link(positive_output.inputs.output)
decision_node.outputs.input.link(negative_output.inputs.output)

# save the pipeline as draft
pipeline.save()

# print the pipeline as json
print(json.dumps(pipeline.serialize(), indent=2))

# run the pipeline
# output = pipeline.run("I feel so happy today!")
output = pipeline.run("I feel so bad today!")

# print the output
print(output)
