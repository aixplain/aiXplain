import json

from aixplain.api import Pipeline, DataType


pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input()
translation = pipeline.asset('60ddefae8d38c51c5885eff7')
speech_recognition = pipeline.asset('621cf3fa6442ef511d2830af')
output_1 = pipeline.output()
output_2 = pipeline.output()

router = pipeline.router([
    (DataType.TEXT, translation),
    (DataType.AUDIO, speech_recognition)
])

input.link(router)
router.OUTPUT_INPUT.link(translation.INPUT_TEXT)
router.OUTPUT_INPUT.link(speech_recognition.INPUT_SOURCE_AUDIO)
translation.OUTPUT_DATA.link(output_1.INPUT_OUTPUT)
speech_recognition.OUTPUT_DATA.link(output_2.INPUT_OUTPUT)

# print the pipeline as json
print(json.dumps(pipeline.to_dict(), indent=2))

# save the pipeline as draft
pipeline.save()

output = pipeline.run('hello programmatic pipeline!')

print(output)
