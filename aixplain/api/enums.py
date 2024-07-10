from enum import Enum


class DataType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    LABEL = "label"


class RouteType(str, Enum):
    CHECK_TYPE = "checkType"
    CHECK_VALUE = "checkValue"


class Operation(str, Enum):
    GREATER_THAN = "greaterThan"
    GREATER_THAN_OR_EQUAL = "greaterThanOrEqual"
    LESS_THAN = "lessThan"
    LESS_THAN_OR_EQUAL = "lessThanOrEqual"
    EQUAL = "equal"
    DIFFERENT = "different"


class NodeType(str, Enum):
    ASSET = "ASSET"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    SCRIPT = "SCRIPT"
    SEGMENTOR = "SEGMENT"
    RECONSTRUCTOR = "RECONSTRUCT"
    ROUTER = "ROUTER"
    DECISION = "DECISION"


class AssetType(str, Enum):
    MODEL = "MODEL"


class FunctionType(str, Enum):
    AI = "AI"
    SEGMENTOR = "SEGMENTOR"
    RECONSTRUCTOR = "RECONSTRUCTOR"


class ParamType:
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
