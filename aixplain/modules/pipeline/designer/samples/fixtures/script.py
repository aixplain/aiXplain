__author__ = "thiagocastroferreira"

import argparse
import json


def main(transcripts, speakers, output_file):
    # get the speech recognition json
    transcripts = json.load(open(transcripts))
    # get the speaker diarization json
    speakers = json.load(open(speakers))

    # build the response
    response = []
    for i, transcript in enumerate(transcripts):
        merge = {
            "transcript": transcript["attributes"]["data"],
            "speaker": speakers[i]["attributes"]["data"]["data"],
        }
        response.append(
            {
                "index": i,
                "success": True,
                "input_type": "text",
                "is_url": transcript["is_url"],
                "details": {},
                "input_segment_info": transcript["input_segment_info"],
                "attributes": {"data": merge, "input": merge},
            }
        )

    # save the response, based on the intermediate representation format, in the output_file
    with open(output_file, "w") as f:
        json.dump(response, f)


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument("--transcripts", type=str, required=True)
    parser.add_argument("--speakers", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    # Parse the argument
    args = parser.parse_args()

    transcripts = args.transcripts
    speakers = args.speakers
    output_file = args.output_file

    main(transcripts, speakers, output_file)
