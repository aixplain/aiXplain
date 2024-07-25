from aixplain.api import Pipeline


pipeline = Pipeline()

# add nodes to the pipeline
input = pipeline.input()
translation = pipeline.asset("60ddefae8d38c51c5885eff7")
speech_recognition = pipeline.asset("621cf3fa6442ef511d2830af")

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
