# This is a compatibility layer for v2 modules
# All enums are now centralized in aixplain.enums.generated_enums
# This file redirects imports to maintain backward compatibility

from aixplain.enums.generated_enums import Function, Supplier, Language, License
from aixplain.enums import (
    AssetStatus,
    DataSplit,
    DataSubtype,
    DataType,
    ErrorHandler,
    FileType,
    OnboardStatus,
    OwnershipType,
    Privacy,
    ResponseStatus,
    SortBy,
    SortOrder,
    StorageType,
)
from enum import Enum


class ToolType(str, Enum):
    """Enum for tool types."""

    UTILITY = "utility"
    MODEL = "model"
    PIPELINE = "pipeline"
    INTEGRATION = "integration"


class AuthenticationScheme(str, Enum):
    """Authentication schemes supported by integrations."""

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH1 = "OAUTH1"
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    NO_AUTH = "NO_AUTH"


__all__ = [
    "Function",
    "Supplier",
    "Language",
    "License",
    "AssetStatus",
    "DataSplit",
    "DataSubtype",
    "DataType",
    "ErrorHandler",
    "FileType",
    "OnboardStatus",
    "OwnershipType",
    "Privacy",
    "ResponseStatus",
    "SortBy",
    "SortOrder",
    "StorageType",
    "ToolType",
]
