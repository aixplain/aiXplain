__author__ = "thiagocastroferreira"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest
from aixplain.factories import PipelineFactory
from aixplain.modules.pipeline.designer import DataType
from aixplain.modules import Pipeline


def test_create_asr_pipeline():
    pipeline = PipelineFactory.create(
        name="Pipeline for SDK Designer Test with Audio Input",
    )

    # add nodes to the pipeline
    input = pipeline.input(dataType=[DataType.AUDIO])
    model1 = pipeline.asset("60ddefab8d38c51c5885ee38")
    model2 = pipeline.asset("60ddefd68d38c51c588608f1")

    # link the nodes
    input.outputs.input.link(model1.inputs.source_audio)
    model1.outputs.data.link(model2.inputs.text)

    # use the output of the last node
    model1.use_output("data")
    model2.use_output("data")

    # save the pipeline as draft
    pipeline.save()

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""
    pipeline.delete()


def test_create_mt_pipeline_and_run():
    pipeline = PipelineFactory.create(
        name="Pipeline for SDK Designer with Text Input to Run",
    )

    # add nodes to the pipeline
    input = pipeline.input(dataType=[DataType.TEXT])
    model1 = pipeline.asset("60ddef828d38c51c5885d491")

    # link the nodes
    input.outputs.input.link(model1.inputs.text)

    # use the output of the last node
    model1.use_output("data")

    # save the pipeline as an asset
    pipeline.save(save_as_asset=True)

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""

    # run the pipeline
    output = pipeline.run(
        "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.txt", **{"batchmode": False, "version": "2.0"}
    )
    pipeline.delete()
    # print the output
    print(output)
    assert output["status"] == "SUCCESS"


@pytest.mark.parametrize(
    ["data", "dataType"],
    [
        ("This is a sample text!", DataType.TEXT),
        # (
        #     "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
        #     DataType.AUDIO,
        # ),
    ],
)
def test_routing_pipeline(data, dataType):

    TRANSLATION_ASSET = "60ddefae8d38c51c5885eff7"
    SPEECH_RECOGNITION_ASSET = "621cf3fa6442ef511d2830af"

    pipeline = Pipeline()

    input = pipeline.input(dataType=[dataType])
    translation = pipeline.asset(TRANSLATION_ASSET)
    speech_recognition = pipeline.asset(SPEECH_RECOGNITION_ASSET)

    input.route(translation.inputs.text, speech_recognition.inputs.source_audio)

    translation.use_output("data")
    speech_recognition.use_output("data")

    pipeline.save()

    output = pipeline.run(data)

    assert output["status"] == "SUCCESS"
    assert output.get("data") is not None
    assert len(output["data"]) > 0
    assert output["data"][0].get("segments") is not None
    assert len(output["data"][0]["segments"]) > 0

    # would like to assert the output of the pipeline but it's not
    # deterministic, so we can't really assert the output
