# Video Subtitling Example

The code in `subtitle_generator.py` subtitles a video spoken one source language to a target language and generates an srt file as an output.

## Run the example

### Build a pipeline using aiXplain pipelines

In order to build a subtitle generation pipeline, you need to log in to www.aixplain.com and use the web UI for designing pipelines as shown by the documentation video in this [link]().

### Run code

Generate a http(s) link to your video file to subtitle.
Using the API_KEY generated for subtitling in the step above, run the code:

```
python3 subtitle_generator.py --video-pt-path <http_link_to_video> \
                                --srt-path pt.srt
                                -k <API_KEY>
```
