import json
from typing import Iterator

from aixplain.modules.model.response import ModelResponse, ResponseStatus


class ModelResponseStreamer:
    """A class representing a streamer for model responses.

    This class provides an iterator interface for streaming model responses.
    It handles the conversion of JSON-like strings into ModelResponse objects
    and manages the response status.
    """

    def __init__(self, iterator: Iterator):
        """Initialize a new ModelResponseStreamer instance.

        Args:
            iterator (Iterator): An iterator that yields JSON-like strings.
        """
        self.iterator = iterator
        self.status = ResponseStatus.IN_PROGRESS

    def __next__(self):
        """Return the next chunk of the response.

        Returns:
            ModelResponse: A ModelResponse object containing the next chunk of the response.
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
        """Return the iterator for the ModelResponseStreamer.

        Returns:
            Iterator: The iterator for the ModelResponseStreamer.
        """
        return self
