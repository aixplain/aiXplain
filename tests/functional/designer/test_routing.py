import pytest

from aixplain.factories.pipeline_factory import PipelineFactory


@pytest.mark.parametrize(
    ["data"],
    [
        ("This is a sample text!",),
    ],
)
def test_routing_pipeline(data):

    pipeline = PipelineFactory.init()

    # add nodes to the pipeline
    input = pipeline.input()
    translation = pipeline.translation(assetId="60ddefae8d38c51c5885eff7")

    speech_recognition = pipeline.speech_recognition(
        assetId="621cf3fa6442ef511d2830af"
    )

    # route the input to the translation and speech recognition nodes
    input.route(
        translation.inputs.text, speech_recognition.inputs.source_audio
    )

    # route the output of the translation and speech recognition nodes
    # to the output
    translation.use_output("data")
    speech_recognition.use_output("data")

    pipeline.save()

    output = pipeline.run(data)

    assert output["status"] == "SUCCESS"
    assert output.get("data") is not None
    assert len(output["data"]) > 0
    assert output["data"][0].get("segments") is not None
    assert len(output["data"][0]["segments"]) > 0
