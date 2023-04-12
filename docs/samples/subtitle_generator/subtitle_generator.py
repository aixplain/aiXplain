__author__ = "thiagocastroferreira"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju and Thiago Castro Ferreira
Date: May 10th 2022
Description:
    Script to generate English Subtitles to Portuguese Videos

Notes:
    Example:
        python3 subtitle_generator.py --video-pt-path https://aixplain-samples-public.s3.amazonaws.com/pipelines/sample_subtitle.mp4 \
                                      --srt-path pt.srt
                                      -k <API_KEY>
"""

import argparse
from datetime import timedelta
import os
import logging

import requests
from tqdm import tqdm

from aixplain.factories.pipeline_factory import PipelineFactory


def generate_srt(segments: list, write_file: str = None):
    """
    Generate a subtitle .srt file

    params:
    ---
        segments: list of segments returned by pipeline execution. Each segment consists of:
            start_sec: start of the segment (in seconds)
            end_sec: end of the segment (in seconds)
            response: link to the transcription of the audio in the interval
        write_file: file to write the srt file. If not provided (None), the string will be returned
    return:
    ---
        .srt string or file
    """
    subtitles = []
    for i in tqdm(range(len(segments))):
        s = segments[i]
        start = str(timedelta(seconds=s["start_sec"]))
        if len(start.split(":")[0]) == 1:
            start = "0" + start
        start = start.replace(".", ",")[:12]

        end = str(timedelta(seconds=s["end_sec"]))
        if len(end.split(":")[0]) == 1:
            end = "0" + end
        end = end.replace(".", ",")[:12]

        r = requests.get(s["response"])
        text = r.text

        subtitles.append({"index": str(i + 1), "start": start, "end": end, "text": text})

    srt = []
    for s in subtitles:
        chunk = f"{s['index']}\n{s['start']} --> {s['end']}\n{s['text']}"
        srt.append(chunk)

    result = "\n\n".join(srt)
    if write_file is not None:
        with open(write_file, "w") as f:
            f.write(result)
    return result


def main(video_path: str, srt_path: str, pipeline_id: str):
    """
    params:
    ---
        video_path:str - path to the Portuguese video to be subtitled
        srt_path:str - path to save the generated subtitle
        pipeline_id:str - aixplain Pipeline ID for subtitling pipeline
    return:
    ---
        .srt string or file
    """
    pipe = PipelineFactory.get(pipeline_id)
    response = pipe.run(data=video_path)

    if response["success"] is True:
        if response["response"]["status"] == "SUCCESS":
            translation_outcome = [data for data in response["response"]["data"] if data["function"] == "translation"][0]
            segments = translation_outcome["segments"]

            generate_srt(segments, srt_path)
        else:
            raise Exception("Failing in getting the transcriptions to the segments of the Portuguese Video.")
    else:
        raise Exception("Failing in getting the transcriptions to the segments of the Portuguese Video.")


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument("--video-pt-path", type=str, required=True)
    parser.add_argument("--srt-path", type=str, required=True)
    parser.add_argument("-k", "--pipeline-id", type=str, required=True)

    # Parse the argument
    args = parser.parse_args()

    video_path = args.video_pt_path
    srt_path = args.srt_path
    pipeline_id = args.pipeline_id

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    main(video_path, srt_path, pipeline_id)
