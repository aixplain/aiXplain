import json
from aixplain.api import Pipeline, Route, RouteType, Operation
from aixplain.api.pipeline import SentimentAnalysis

pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input()

# option 1
sentiment_analysis = pipeline.sentiment_analysis(
    assetId="6172874f720b09325cbcdc33"
)

# option 2
sentiment_analysis = SentimentAnalysis(
    pipeline=pipeline, assetId="6172874f720b09325cbcdc33"
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
input.output.link(sentiment_analysis.t)
sentiment_analysis.data.link(decision_node.comparison)
input.input.link(decision_node.passthrough)
decision_node.input.link(positive_output.input)
decision_node.input.link(negative_output.input)

# save the pipeline as draft
pipeline.save()

# print the pipeline as json
print(json.dumps(pipeline.to_dict(), indent=2))

# run the pipeline
# output = pipeline.run("I feel so happy today!")
output = pipeline.run("I feel so bad today!")

# print the output
print(output)
