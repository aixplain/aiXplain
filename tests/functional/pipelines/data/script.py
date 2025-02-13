def main(speakers):
    # build the response
    response = []
    for i, speaker in enumerate(speakers):
        print(f"Processing speaker at index={i}")
        data = speaker["data"]
        data_modified = f"SCRIPT MODIFIED: {data}"
        response.append(
            {
                "index": i,
                "success": True,
                "input_type": "text",
                "is_url": False,
                "details": {},
                "data": data_modified,
                "input": data_modified,
            }
        )
    return response
