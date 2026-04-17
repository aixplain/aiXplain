"""aiXplain SDK v2 - Modern Python SDK for the aiXplain platform."""

from .core import Aixplain
from .rlm import RLM, RLMResult
from .utility import Utility
from .agent import Agent
from .tool import Tool
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
)
from .meta_agents import Debugger, DebugResult
from .agent_progress import AgentProgressTracker, ProgressFormat
from .agent_evaluator import AgentEvaluationExecutor, EvalCase, MetricTool, MetricToolResponse
from .eval_results_display import (
    case_comparison_html,
    case_rows,
    guess_compare_value_columns,
    load_eval_csv,
    pivot_agents_wide,
    summarize_by_agent,
)
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
)

__all__ = [
    "Aixplain",
    "RLM",
    "RLMResult",
    "Utility",
    "Agent",
    "Tool",
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
    "ModelResponse",
    # Meta-agents
    "Debugger",
    "DebugResult",
    # Progress tracking
    "AgentProgressTracker",
    "ProgressFormat",
    # Agent evaluation
    "AgentEvaluationExecutor",
    "EvalCase",
    "MetricTool",
    "MetricToolResponse",
    "case_comparison_html",
    "case_rows",
    "guess_compare_value_columns",
    "load_eval_csv",
    "pivot_agents_wide",
    "summarize_by_agent",
    # API Key management
    "APIKey",
    "APIKeyLimits",
    "APIKeyUsageLimit",
    "TokenType",
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
    # Actions / Inputs hierarchy
    "Input",
    "Inputs",
    "Action",
    "Actions",
]
