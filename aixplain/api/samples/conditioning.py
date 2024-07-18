from aixplain.api import Pipeline, DataType, Route, RouteType, Operation

pipeline = Pipeline()

# add nodes to the pipeline
"""
"nodes": [
    {
        "id": 4,
        "label": "Decision 1",
        "routes": [
            {
                "type": "checkValue",
                "operation": "greaterThanOrEqual",
                "value": 0.2,
                "path": [
                    2
                ]
            },
            {
                "type": "checkValue",
                "operation": "lessThan",
                "value": 0.2,
                "path": []
            }
        ],
        "type": "DECISION"
    },
    {
        "id": 0,
        "label": "Input 1",
        "input_type": [
            "audio"
        ],
        "output_type": [
            "audio"
        ],
        "type": "INPUT"
    },
    {
        "id": 3,
        "label": "Output 1",
        "input_type": [
            "text"
        ],
        "output_type": [
            "text"
        ],
        "type": "OUTPUT"
    },
    {
        "id": 1,
        "label": "Model 1",
        "payload": {
            "assetId": "60ddefab8d38c51c5885ee38",
            "function": "speech-recognition",
            "options": {
                "savetos3": true,
                "nodeId": 1,
                "cachable": false
            },
            "supplier": "Azure",
            "versionName": "",
            "version": "",
            "language": "en",
            "dialect": "United States"
        },
        "url": "https://models.aixplain.com/api/v1/execute",
        "input_type": [
            "audio"
        ],
        "output_type": [
            "text"
        ],
        "type": "ASSET",
        "automode": false
    },
    {
        "id": 2,
        "label": "Model 2",
        "payload": {
            "assetId": "60ddefd68d38c51c588608f1",
            "function": "translation",
            "options": {
                "savetos3": true,
                "nodeId": 2,
                "cachable": false
            },
            "supplier": "Azure",
            "versionName": "",
            "version": "",
            "sourcelanguage": "en",
            "targetlanguage": "tr"
        },
        "url": "https://models.aixplain.com/api/v1/execute",
        "input_type": [
            "text"
        ],
        "output_type": [
            "text"
        ],
        "type": "ASSET",
        "automode": false
    }
]
"""
input = pipeline.input(dataType=[DataType.AUDIO])
model1 = pipeline.asset('60ddefab8d38c51c5885ee38')
model2 = pipeline.asset('60ddefd68d38c51c588608f1')
decision1 = pipeline.decision(
    routes=[
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.GREATER_THAN_OR_EQUAL,
            value=0.2,
            path=[model2]
        ),
        Route(
            type=RouteType.CHECK_VALUE,
            operation=Operation.LESS_THAN,
            value=0.2,
            path=[]
        )
    ]
)

# link the nodes
"""
"links": [
    {
        "param_mapping": [
            {
                "from": "input",
                "to": "source_audio"
            }
        ],
        "from": input,
        "to": model1
    },
    {
        "param_mapping": [
            {
                "from": "data",
                "to": "output"
            }
        ],
        "from": model2,
        "to": output
    },
    {
        "param_mapping": [
            {
                "from": "confidence",
                "to": "comparison"
            },
            {
                "from": "data",
                "to": "passthrough"
            }
        ],
        "from": model1,
        "to": decision
    },
    {
        "param_mapping": [
            {
                "from": "data",
                "to": "text",
                "dataSourceId": 1
            }
        ],
        "from": decision,
        "to": model2
    }
]
"""
input.outputs.input.link(model1.inputs.source_audio)
model1.outputs.confidence.link(decision1.inputs.comparison)
model1.outputs.data.link(decision1.inputs.passthrough)
decision1.outputs.data.link(model2.inputs.text)

# use the output of the last node
model2.use_output('data')

# print the pipeline as json
print(pipeline.to_dict())

# save the pipeline as draft
pipeline.save()

# run the pipeline
output = pipeline.run(
    'https://aixplain-temp-0001.s3.amazonaws.com/coreengine_tests/test_audio.wav' # noqa
)

# print the output
print(output)
