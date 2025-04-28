from typing import Iterator


class ModelStreamer:
    def __init__(self, iterator: Iterator):
        self.iterator = iterator

    def __next__(self):
        return next(self.iterator).replace("data: ", "").replace("[DONE]", "")

    def __iter__(self):
        return self
