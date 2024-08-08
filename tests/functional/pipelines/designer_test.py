import pytest
from aixplain.enums import DataType

from aixplain.factories import PipelineFactory
from aixplain.modules.pipeline.designer.base import Link
from aixplain.modules import Pipeline

from aixplain.modules.pipeline.designer import AssetNode


def test_create_asr_pipeline():
    pipeline = PipelineFactory.init(
        name="Pipeline for SDK Designer Test with Audio Input",
    )

    # add nodes to the pipeline
    input = pipeline.input()
    model1 = AssetNode(asset_id="60ddefab8d38c51c5885ee38")
    pipeline.add_node(model1)

    model2 = AssetNode(asset_id="60ddefd68d38c51c588608f1")
    pipeline.add_node(model2)

    # link the nodes
    link1 = Link(
        from_node=input,
        to_node=model1,
        from_param="input",
        to_param="source_audio",
    )
    pipeline.add_link(link1)

    link2 = Link(
        from_node=model1,
        to_node=model2,
        from_param="data",
        to_param="text",
    )
    pipeline.add_link(link2)

    # use the output of the last node
    model1.use_output("data")
    model2.use_output("data")

    # save the pipeline as draft
    pipeline.save()

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""
    pipeline.delete()


def test_create_mt_pipeline_and_run():
    pipeline = PipelineFactory.init(
        name="Pipeline for SDK Designer with Text Input to Run",
    )

    # add nodes to the pipeline
    input = pipeline.input()
    model1 = pipeline.translation(asset_id="60ddef828d38c51c5885d491")
    output = pipeline.output()

    # link the nodes
    input.link(
        to_node=model1,
        from_param=input.outputs.input,
        to_param=model1.inputs.text,
    )

    # use the output of the last node
    model1.link(
        to_node=output,
        from_param=model1.outputs.data,
        to_param=output.inputs.output,
    )

    # save the pipeline as an asset
    pipeline.save(save_as_asset=True)

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""

    pipeline = PipelineFactory.get(pipeline.id)

    # run the pipeline
    output = pipeline.run(
        "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.txt",
        **{"batchmode": False, "version": "2.0"},
    )
    pipeline.delete()
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

    pipeline = PipelineFactory.init(
        name="Pipeline for SDK Designer Test with Audio Input",
    )

    input = pipeline.input()
    translation = pipeline.asset(TRANSLATION_ASSET)
    speech_recognition = pipeline.asset(SPEECH_RECOGNITION_ASSET)

    input.route(translation.inputs.text, speech_recognition.inputs.source_audio)

    translation.use_output("data")
    speech_recognition.use_output("data")

    pipeline.save()

    output = pipeline.run(data)

    pipeline.delete()
    assert output["status"] == "SUCCESS"
    assert output.get("data") is not None
    assert len(output["data"]) > 0
    assert output["data"][0].get("segments") is not None
    assert len(output["data"][0]["segments"]) > 0

    # would like to assert the output of the pipeline but it's not
    # deterministic, so we can't really assert the output
