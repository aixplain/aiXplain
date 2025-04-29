from typing import Iterator

from aixplain.modules.model.response import ModelResponse, ResponseStatus


class ModelResponseStreamer:
    def __init__(self, iterator: Iterator):
        self.iterator = iterator
        self.status = ResponseStatus.IN_PROGRESS
        self.full_content = ""

    def __next__(self):
        """
        Returns the next chunk of the response.
        """
        content = next(self.iterator).replace("data: ", "")
        if content == "[DONE]":
            self.status = ResponseStatus.SUCCESS
            content = ""
        self.full_content += content
        return ModelResponse(status=self.status, data=content, details={"full_content": self.full_content})

    def __iter__(self):
        return self
