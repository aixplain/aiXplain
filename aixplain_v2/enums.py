from enum import Enum


class Function(str, Enum):
    # TODO: Below the enums are subset of the enums in the actual API.
    # The entire list of enums should be generated from the actual API.
    TRANSLATION = "translation"
    TEXT_GENERATION = "text_generation"


class Supplier(str, Enum):
    # TODO: Below the enums are subset of the enums in the actual API.
    # The entire list of enums should be generated from the actual API.
    OPENAI = "openai"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class OwnershipType(str, Enum):
    SUBSCRIBED = "SUBSCRIBED"
    OWNED = "OWNED"


class SortBy(str, Enum):
    CREATION_DATE = "createdAt"
    PRICE = "normalizedPrice"
    POPULARITY = "totalSubscribed"


class SortOrder(Enum):
    ASCENDING = 1
    DESCENDING = -1


class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"


class DataType(str, Enum):
    AUDIO = "audio"
    FLOAT = "float"
    IMAGE = "image"
    INTEGER = "integer"
    LABEL = "label"
    TENSOR = "tensor"
    TEXT = "text"
    VIDEO = "video"
    EMBEDDING = "embedding"
    NUMBER = "number"
    BOOLEAN = "boolean"
