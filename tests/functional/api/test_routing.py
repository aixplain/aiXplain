import pytest

from aixplain.api import Pipeline, DataType


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
    SOURCE_LANGUAGE = "en"
    TARGET_LANGUAGE = "fr"

    pipeline = Pipeline()

    input = pipeline.input(dataType=[dataType])
    translation = pipeline.asset(TRANSLATION_ASSET)
    translation.inputs.sourcelanguage = SOURCE_LANGUAGE
    translation.inputs.targetlanguage = TARGET_LANGUAGE

    speech_recognition = pipeline.asset(SPEECH_RECOGNITION_ASSET)
    speech_recognition.inputs.language = SOURCE_LANGUAGE

    input.route(
        translation.inputs.text, speech_recognition.inputs.source_audio
    )

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
