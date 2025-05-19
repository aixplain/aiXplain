import json
from typing import Iterator

from aixplain.modules.model.response import ModelResponse, ResponseStatus


class ModelResponseStreamer:
    def __init__(self, iterator: Iterator):
        self.iterator = iterator
        self.status = ResponseStatus.IN_PROGRESS

    def __next__(self):
        """
        Returns the next chunk of the response.
        """
        line = next(self.iterator).replace("data: ", "")
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = {"data": line}
        content = data.get("data", "")
        if content == "[DONE]":
            self.status = ResponseStatus.SUCCESS
            content = ""
        return ModelResponse(status=self.status, data=content)

    def __iter__(self):
        return self
