import json

from aixplain.api import Pipeline


pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input()
translation = pipeline.asset('60ddefae8d38c51c5885eff7')
speech_recognition = pipeline.asset('621cf3fa6442ef511d2830af')

input.route(
    translation.inputs.text,
    speech_recognition.inputs.source_audio
)

translation.use_output('data')
speech_recognition.use_output('data')

# print the pipeline as json
print(json.dumps(pipeline.to_dict(), indent=2))

# save the pipeline as draft
pipeline.save()

output = pipeline.run('hello programmatic pipeline!')

print(output)
