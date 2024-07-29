from aixplain.api import Pipeline, DataType, Route, RouteType, Operation

pipeline = Pipeline()

# add nodes to the pipeline

input = pipeline.input(dataType=[DataType.AUDIO])
model1 = pipeline.asset(assetId="60ddefab8d38c51c5885ee38")
model2 = pipeline.asset(assetId="60ddefd68d38c51c588608f1")
decision1 = pipeline.decision(
    routes=[
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.GREATER_THAN_OR_EQUAL,
            value=0.2,
            path=[model2],
        ),
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.LESS_THAN,
            value=0.2,
            path=[],
        ),
    ]
)

# link the nodes
input.outputs.input.link(model1.inputs.source_audio)
model1.outputs.confidence.link(decision1.inputs.comparison)
model1.outputs.data.link(decision1.inputs.passthrough)
decision1.outputs.data.link(model2.inputs.text)

# use the output of the last node
model2.use_output("data")

# print the pipeline as json
print(pipeline.to_dict())

# save the pipeline as draft
pipeline.save()

# run the pipeline
output = pipeline.run("https://aixplain-temp-0001.s3.amazonaws.com/coreengine_tests/test_audio.wav")  # noqa

# print the output
print(output)
