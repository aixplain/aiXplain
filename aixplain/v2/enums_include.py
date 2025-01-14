from enum import Enum


class AssetStatus(str, Enum):
    DRAFT = "draft"
    HIDDEN = "hidden"
    SCHEDULED = "scheduled"
    ONBOARDING = "onboarding"
    ONBOARDED = "onboarded"
    PENDING = "pending"
    FAILED = "failed"
    TRAINING = "training"
    REJECTED = "rejected"
    ENABLING = "enabling"
    DELETING = "deleting"
    DISABLED = "disabled"
    DELETED = "deleted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELING = "canceling"
    CANCELED = "canceled"


class DataSplit(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class DataSubtype(str, Enum):
    AGE = "age"
    GENDER = "gender"
    INTERVAL = "interval"
    OTHER = "other"
    RACE = "race"
    SPLIT = "split"
    TOPIC = "topic"


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


class ErrorHandler(str, Enum):
    """
    Enumeration class defining different error handler strategies.

    Attributes:
        SKIP (str): skip failed rows.
        FAIL (str): raise an exception.
    """

    SKIP = "skip"
    FAIL = "fail"


class FileType(str, Enum):
    CSV = ".csv"
    JSON = ".json"
    TXT = ".txt"
    XML = ".xml"
    FLAC = ".flac"
    MP3 = ".mp3"
    WAV = ".wav"
    JPEG = ".jpeg"
    PNG = ".png"
    JPG = ".jpg"
    GIF = ".gif"
    WEBP = ".webp"
    AVI = ".avi"
    MP4 = ".mp4"
    MOV = ".mov"
    MPEG4 = ".mpeg4"


class OnboardStatus(str, Enum):
    ONBOARDING = "onboarding"
    ONBOARDED = "onboarded"
    FAILED = "failed"
    DELETED = "deleted"


class OwnershipType(str, Enum):
    SUBSCRIBED = "SUBSCRIBED"
    OWNED = "OWNED"


class Privacy(str, Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"
    RESTRICTED = "Restricted"


class ResponseStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SortBy(str, Enum):
    CREATION_DATE = "createdAt"
    PRICE = "normalizedPrice"
    POPULARITY = "totalSubscribed"


class SortOrder(Enum):
    ASCENDING = 1
    DESCENDING = -1


class StorageType(str, Enum):
    TEXT = "text"
    URL = "url"
    FILE = "file"
