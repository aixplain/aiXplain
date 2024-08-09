import json

from aixplain.factories.pipeline_factory import PipelineFactory


pipeline = PipelineFactory.init("Pipeline with Reconstructing")

# add nodes to the pipeline
input = pipeline.input()

segmentor = pipeline.speaker_diarization_audio(
    asset_id="62fab6ecb39cca09ca5bc365"
)

speech_recognition = pipeline.speech_recognition(
    asset_id="60ddefab8d38c51c5885ee38"
)

reconstructor = pipeline.bare_reconstructor()

# link the nodes
input.outputs.input.link(segmentor.inputs.audio)
segmentor.outputs.audio.link(speech_recognition.inputs.source_audio)
speech_recognition.outputs.data.link(reconstructor.inputs.data)

reconstructor.use_output("data")

# print the pipeline as json
print(json.dumps(pipeline.serialize(), indent=2))

# save the pipeline as draft
pipeline.save()

# run the pipeline
output = pipeline.run(
    "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/discovery_demo.wav",
)

# print the output
print(output)