"""V2 enums module - self-contained to avoid legacy dependencies.

This module provides all enum types used throughout the v2 SDK.
"""

from enum import Enum


class AuthenticationScheme(str, Enum):
    """Authentication schemes supported by integrations."""

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH1 = "OAUTH1"
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    NO_AUTH = "NO_AUTH"


class FileType(str, Enum):
    """File types supported by the platform."""

    CSV = "CSV"
    JSON = "JSON"
    TXT = "TXT"
    PDF = "PDF"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    DATABASE = "DATABASE"
    OTHER = "OTHER"


class Function(str, Enum):
    """AI functions supported by the platform."""

    SEARCH = "SEARCH"
    TRANSLATION = "TRANSLATION"
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS"
    CLASSIFICATION = "CLASSIFICATION"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    TEXT_GENERATION = "TEXT_GENERATION"
    SPEECH_RECOGNITION = "SPEECH_RECOGNITION"
    IMAGE_CLASSIFICATION = "IMAGE_CLASSIFICATION"
    OBJECT_DETECTION = "OBJECT_DETECTION"
    UTILITIES = "utilities"  # Add the missing utilities function


class Language(str, Enum):
    """Languages supported by the platform."""

    ENGLISH = "ENGLISH"
    SPANISH = "SPANISH"
    FRENCH = "FRENCH"
    GERMAN = "GERMAN"
    ITALIAN = "ITALIAN"
    PORTUGUESE = "PORTUGUESE"
    CHINESE = "CHINESE"
    JAPANESE = "JAPANESE"
    KOREAN = "KOREAN"
    ARABIC = "ARABIC"
    HINDI = "HINDI"
    RUSSIAN = "RUSSIAN"


class License(str, Enum):
    """Licenses supported by the platform."""

    MIT = "MIT"
    APACHE_2_0 = "APACHE_2_0"
    GPL_3_0 = "GPL_3_0"
    BSD_3_CLAUSE = "BSD_3_CLAUSE"
    CC_BY_4_0 = "CC_BY_4_0"
    CC_BY_SA_4_0 = "CC_BY_SA_4_0"
    PROPRIETARY = "PROPRIETARY"


class AssetStatus(str, Enum):
    """Asset status values."""

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
    DEPRECATED_DRAFT = "deprecated_draft"


class Privacy(str, Enum):
    """Privacy settings."""

    PUBLIC = "Public"
    PRIVATE = "Private"
    RESTRICTED = "Restricted"


class OnboardStatus(str, Enum):
    """Onboarding status values."""

    ONBOARDING = "onboarding"
    ONBOARDED = "onboarded"
    FAILED = "failed"
    DELETED = "deleted"


class OwnershipType(str, Enum):
    """Ownership types."""

    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"
    TEAM = "TEAM"


class SortBy(str, Enum):
    """Sort options."""

    NAME = "NAME"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "ASC"
    DESC = "DESC"


class ErrorHandler(str, Enum):
    """Error handling strategies."""

    SKIP = "SKIP"
    FAIL = "FAIL"


class ResponseStatus(str, Enum):
    """Response status values."""

    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class StorageType(str, Enum):
    """Storage type options."""

    S3 = "S3"
    LOCAL = "LOCAL"
    GCS = "GCS"
    AZURE = "AZURE"


class Supplier(str, Enum):
    """AI model suppliers."""

    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    META = "META"
    HUGGINGFACE = "HUGGINGFACE"
    COHERE = "COHERE"
    AIXPLAIN = "AIXPLAIN"


class FunctionType(str, Enum):
    """Function type categories."""

    CLASSIFICATION = "CLASSIFICATION"
    GENERATION = "GENERATION"
    TRANSLATION = "TRANSLATION"
    ANALYSIS = "ANALYSIS"
    DETECTION = "DETECTION"
    RECOGNITION = "RECOGNITION"


class EvolveType(str, Enum):
    """Evolution types."""

    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"


class CodeInterpreterModel(str, Enum):
    """Code interpreter models."""

    GPT_4_CODE_INTERPRETER = "GPT_4_CODE_INTERPRETER"
    CLAUDE_3_CODE_INTERPRETER = "CLAUDE_3_CODE_INTERPRETER"


class SplittingOptions(str, Enum):
    """Enumeration of possible splitting options for text chunking.

    This enum defines the different ways that text can be split into chunks,
    including by word, sentence, passage, page, and line.
    """

    WORD = "word"
    SENTENCE = "sentence"
    PASSAGE = "passage"
    PAGE = "page"
    LINE = "line"


__all__ = [
    "AuthenticationScheme",
    "FileType",
    "Function",
    "Language",
    "License",
    "AssetStatus",
    "Privacy",
    "OnboardStatus",
    "OwnershipType",
    "SortBy",
    "SortOrder",
    "ErrorHandler",
    "ResponseStatus",
    "StorageType",
    "Supplier",
    "FunctionType",
    "EvolveType",
    "CodeInterpreterModel",
    "SplittingOptions",
]
