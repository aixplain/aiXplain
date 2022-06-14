# Video Subtitling Example

The code in `subtitle_generator.py` subtitles a video spoken one source language to a target language and generates an srt file as an output.

In this example pipeline, it receives an English video as input and first extracts its audio, which is then fed to a VAD node, responsible to find the voice activity segments of the audio input. These segments are then transcribed by a speech recognition node and then translated into Spanish by a translation English-Spanish node. Finally, a Speech Synthesis node is added to dub the Spanish translation.

<img src="../../assets/designer-subtitling-sample.png" width=25% height=25%>

## Run the Example

### Build a Pipeline using aiXplain Pipelines

In order to build a subtitle generation pipeline, you need to log in to [aiXplain platform](https://platform.aixplain.com/) and use the web UI for designing pipelines as shown by the documentation video in this [link](https://aixplain.com/designer-tutorial/).

As instructed in the video embedded in the link above, please copy your pipeline API key from the assets page and use it to run the code as shown below.

### Run Code

Generate a http(s) link to your video file to subtitle.
Using the API_KEY generated for subtitling in the step above, run the code:

```
python3 subtitle_generator.py --video-pt-path <http_link_to_video> \
                                --srt-path pt.srt
                                -k <API_KEY>
```

### Sample Output

You can refer to a sample output in this [file](../../assets/subtitle-generator-output.json).
