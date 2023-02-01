__author__ = "aiXplain"

from enum import Enum


class DataType(Enum):
    AUDIO = "audio"
    FLOAT = "float"
    IMAGE = "image"
    INTEGER = "integer"
    LABEL = "label"
    TENSOR = "tensor"
    TEXT = "text"
    VIDEO = "video"
