import pytest

from aixplain.enums import DataType, ResponseStatus
from aixplain.factories import PipelineFactory, DatasetFactory
from aixplain.modules.pipeline.designer import (
    Link,
    Operation,
    Route,
    RouteType,
)
from aixplain.modules import Pipeline
from aixplain.modules.pipeline.designer import AssetNode
from uuid import uuid4


@pytest.fixture
def pipeline():
    # Setup: Initialize the pipeline
    pipeline = PipelineFactory.init(
        name=str(uuid4()),
    )

    # Yield control back to the test function
    yield pipeline

    # Teardown: Ensure the pipeline is deleted
    if pipeline is not None:
        pipeline.delete()


def test_create_asr_pipeline(pipeline):
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


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_create_mt_pipeline_and_run(pipeline, PipelineFactory):
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
        **{"batchmode": False, "version": "3.0"},
    )
    assert output["status"] == ResponseStatus.SUCCESS


def test_routing_pipeline(pipeline):
    TRANSLATION_ASSET = "60ddefae8d38c51c5885eff7"
    SPEECH_RECOGNITION_ASSET = "621cf3fa6442ef511d2830af"

    input = pipeline.input()
    translation = pipeline.asset(TRANSLATION_ASSET)
    speech_recognition = pipeline.asset(SPEECH_RECOGNITION_ASSET)

    input.route(translation.inputs.text, speech_recognition.inputs.source_audio)

    translation.use_output("data")
    speech_recognition.use_output("data")

    pipeline.save()

    output = pipeline.run("This is a sample text!", **{"batchmode": False, "version": "3.0"})
    assert output["status"] == ResponseStatus.SUCCESS


def test_scripting_pipeline(pipeline):
    SPEAKER_DIARIZATION_AUDIO_ASSET = "62fab6ecb39cca09ca5bc365"

    input = pipeline.input()

    segmentor = pipeline.speaker_diarization_audio(asset_id=SPEAKER_DIARIZATION_AUDIO_ASSET)

    script = pipeline.script(script_path="tests/functional/pipelines/data/script.py")
    script.inputs.create_param(code="transcripts", data_type=DataType.TEXT)
    script.inputs.create_param(code="speakers", data_type=DataType.LABEL)
    script.outputs.create_param(code="data", data_type=DataType.TEXT)

    input.outputs.input.link(segmentor.inputs.audio)
    segmentor.outputs.data.link(script.inputs.speakers)

    script.use_output("data")

    pipeline.save()

    output = pipeline.run(
        "s3://aixplain-platform-assets/samples/en/CPAC1x2.wav",
        version="3.0",
    )
    assert output["status"] == ResponseStatus.SUCCESS


def test_decision_pipeline(pipeline):
    SENTIMENT_ANALYSIS_ASSET = "6172874f720b09325cbcdc33"

    input = pipeline.input()

    sentiment_analysis = pipeline.sentiment_analysis(asset_id=SENTIMENT_ANALYSIS_ASSET)

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

    input.outputs.input.link(sentiment_analysis.inputs.text)
    sentiment_analysis.outputs.data.link(decision_node.inputs.comparison)
    input.outputs.input.link(decision_node.inputs.passthrough)
    decision_node.outputs.data.link(positive_output.inputs.output)
    decision_node.outputs.data.link(negative_output.inputs.output)

    pipeline.save()
    output = pipeline.run(
        "I feel so bad today!",
        version="3.0",
    )
    assert output["status"] == ResponseStatus.SUCCESS
    assert output.get("data") is not None


def test_reconstructing_pipeline(pipeline):
    input = pipeline.input()

    segmentor = pipeline.speaker_diarization_audio(asset_id="62fab6ecb39cca09ca5bc365")

    speech_recognition = pipeline.speech_recognition(asset_id="60ddefab8d38c51c5885ee38")

    reconstructor = pipeline.text_reconstruction(asset_id="636cf7ab0f8ddf0db97929e4")

    input.outputs.input.link(segmentor.inputs.audio)
    segmentor.outputs.audio.link(speech_recognition.inputs.source_audio)
    speech_recognition.outputs.data.link(reconstructor.inputs.text)

    reconstructor.use_output("data")

    pipeline.save()

    output = pipeline.run(
        "s3://aixplain-platform-assets/samples/en/CPAC1x2.wav",
        version="3.0",
    )
    assert output["status"] == ResponseStatus.SUCCESS
    assert output.get("data") is not None


def test_metric_pipeline(pipeline):
    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id
    reference_id = dataset.target_data["pt"][0].id

    # Instantiate input nodes
    text_input_node = pipeline.input(label="TextInput")
    reference_input_node = pipeline.input(label="ReferenceInput")

    # Instantiate the metric node
    translation_metric_node = pipeline.text_generation_metric(asset_id="639874ab506c987b1ae1acc6")

    # Instantiate output node
    score_output_node = pipeline.output()

    # Link the nodes
    text_input_node.link(translation_metric_node, from_param="input", to_param="hypotheses")

    reference_input_node.link(translation_metric_node, from_param="input", to_param="references")

    translation_metric_node.link(score_output_node, from_param="data", to_param="output")

    translation_metric_node.inputs.score_identifier = "bleu"

    # Save and run the pipeline
    pipeline.save()

    output = pipeline.run(
        data={"TextInput": reference_id, "ReferenceInput": reference_id},
        data_asset={"TextInput": data_asset_id, "ReferenceInput": data_asset_id},
        version="3.0",
    )

    assert output["status"] == ResponseStatus.SUCCESS
    assert output.get("data") is not None
