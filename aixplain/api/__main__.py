import json

from aixplain.api import Pipeline, DataType


pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.add_input()
translation = pipeline.add_asset('60ddefae8d38c51c5885eff7')
speech_recognition = pipeline.add_asset('621cf3fa6442ef511d2830af')
output = pipeline.add_output()

# link and route the nodes
input.route([
    (DataType.TEXT, translation),
    (DataType.AUDIO, speech_recognition)
])
speech_recognition.link(output, 'data', 'output')
translation.link(output, 'data', 'output')

# print the pipeline as json
print(json.dumps(pipeline.to_dict(), indent=2))

# save the pipeline as draft
pipeline.save()

output = pipeline.run('hello programmatic pipeline!')

print(output)
