import json

from aixplain.api import Pipeline, DataType


pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input(dataType=[DataType.AUDIO])
script = pipeline.script(script_path='aixplain/api/samples/fixtures/script.py')
script.add_input_param('transcripts', DataType.TEXT)
script.add_input_param('speakers', DataType.LABEL)
script.add_output_param('data', DataType.TEXT)

segmentor = pipeline.segmentor('62fab6ecb39cca09ca5bc365')
speech_recognition = pipeline.asset('60ddefab8d38c51c5885ee38')

input.outputs.input.link(segmentor.inputs.audio)
segmentor.outputs.data.link(speech_recognition.inputs.source_audio)
segmentor.outputs.data.link(script.inputs.transcripts)
speech_recognition.outputs.data.link(script.inputs.speakers)
script.use_output('data')

# print the pipeline as json
print(json.dumps(pipeline.to_dict(), indent=2))

# save the pipeline as draft
pipeline.save()

output = pipeline.run('https://aixplain-platform-assets.s3.amazonaws.com/samples/en/discovery_demo.wav')

print(output)
