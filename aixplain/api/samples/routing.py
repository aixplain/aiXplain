from aixplain.api import Pipeline

TRANSLATION_ASSET = "60ddefae8d38c51c5885eff7"
SPEECH_RECOGNITION_ASSET = "621cf3fa6442ef511d2830af"
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "fr"

pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input()
translation = pipeline.asset(TRANSLATION_ASSET)
translation.inputs.sourcelanguage = SOURCE_LANGUAGE
translation.inputs.targetlanguage = TARGET_LANGUAGE

speech_recognition = pipeline.asset(SPEECH_RECOGNITION_ASSET)
speech_recognition.inputs.language = SOURCE_LANGUAGE

# route the input to the translation and speech recognition nodes
input.route(translation.inputs.text, speech_recognition.inputs.source_audio)

# route the output of the translation and speech recognition nodes
# to the output
translation.use_output("data")
speech_recognition.use_output("data")

# save the pipeline as draft
pipeline.save()

# run the pipeline
output = pipeline.run("hello programmatic pipeline!")

# print the output
print(output)
