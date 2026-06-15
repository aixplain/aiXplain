"""aiXplain SDK v2 - Modern Python SDK for the aiXplain platform."""

from .core import Aixplain
from .rlm import RLM, RLMResult
from .utility import Utility
from .agent import Agent, ContextOverflowStrategy
from .tool import Tool
from .index import (
    Index,
    IndexResult,
    Record,
    IndexFilter,
    IndexFilterOperator,
    Splitter,
    BaseIndexParams,
    BaseIndexParamsWithEmbeddingModel,
    AirParams,
    VectaraParams,
    GraphRAGParams,
    ZeroEntropyParams,
)
from .actions import Input, Inputs, Action, Actions
from .file import Resource
from .upload_utils import FileUploader, upload_file, validate_file_for_upload
from .inspector import (
    Inspector,
    InspectorTarget,
    InspectorAction,
    InspectorOnExhaust,
    InspectorSeverity,
    InspectorActionConfig,
    EvaluatorType,
    EvaluatorConfig,
    EditorConfig,
    PrebuiltInspector,
)
from .meta_agents import Debugger, DebugResult
from .agent_progress import AgentProgressTracker, ProgressFormat
from .api_key import APIKey, APIKeyLimits, APIKeyUsageLimit, TokenType
from .exceptions import (
    AixplainV2Error,
    ResourceError,
    APIError,
    ValidationError,
    TimeoutError,
    FileUploadError,
)
from .enums import (
    AuthenticationScheme,
    FileType,
    Function,
    Language,
    License,
    AssetStatus,
    Privacy,
    OnboardStatus,
    OwnershipType,
    SortBy,
    SortOrder,
    ErrorHandler,
    ResponseStatus,
    StorageType,
    Supplier,
    FunctionType,
    EvolveType,
    CodeInterpreterModel,
    SplittingOptions,
    DataType,
    EmbeddingModel,
    IndexStores,
)

__all__ = [
    "Aixplain",
    "RLM",
    "RLMResult",
    "Utility",
    "Agent",
    "ContextOverflowStrategy",
    "Tool",
    # Index resource + types
    "Index",
    "IndexResult",
    "Record",
    "IndexFilter",
    "IndexFilterOperator",
    "Splitter",
    "BaseIndexParams",
    "BaseIndexParamsWithEmbeddingModel",
    "AirParams",
    "VectaraParams",
    "GraphRAGParams",
    "ZeroEntropyParams",
    "Resource",
    "FileUploader",
    "upload_file",
    "validate_file_for_upload",
    # Inspector classes
    "Inspector",
    "InspectorTarget",
    "InspectorAction",
    "InspectorOnExhaust",
    "InspectorSeverity",
    "InspectorActionConfig",
    "EvaluatorType",
    "EvaluatorConfig",
    "EditorConfig",
    "PrebuiltInspector",
    # Meta-agents
    "Debugger",
    "DebugResult",
    # Progress tracking
    "AgentProgressTracker",
    "ProgressFormat",
    # API Key management
    "APIKey",
    "APIKeyLimits",
    "APIKeyUsageLimit",
    "TokenType",
    # Progress tracking
    "AgentProgressTracker",
    "ProgressFormat",
    # Exceptions
    "AixplainV2Error",
    "ResourceError",
    "APIError",
    "ValidationError",
    "TimeoutError",
    "FileUploadError",
    # V2 enum exports
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
    "DataType",
    "EmbeddingModel",
    "IndexStores",
    # Actions / Inputs hierarchy
    "Input",
    "Inputs",
    "Action",
    "Actions",
]
