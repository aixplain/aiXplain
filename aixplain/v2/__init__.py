"""aiXplain SDK v2 - Modern Python SDK for the aiXplain platform."""

from .core import Aixplain
from .rlm import RLM, RLMResult
from .utility import Utility
from .agent import Agent, ContextOverflowStrategy
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
from .agent_evaluator import (
    Eval,
    AgentEvaluationResultsChatbot,
    AgentEvaluationRow,
    AgentEvaluationRun,
    Dataset,
    EvalCase,
    Metric,
    MetricResponse,
    compare_agents_side_by_side,
    normalize_eval_results_dataframe,
)
from .eval_experiment import (
    EXPERIMENT_COMPARISON_COL_RUN_CREATED_AT,
    EXPERIMENT_COMPARISON_COL_RUN_INDEX,
    Experiment,
    ExperimentLocalCache,
    ExperimentRun,
    ExperimentRunDiff,
    ExperimentRunDiffCase,
    ExperimentRunDiffCaseList,
    default_experiment_cache_dir,
)
from .eval_results_display import (
    case_comparison_html,
    case_rows,
    guess_compare_value_columns,
    load_eval_csv,
    pivot_agents_wide,
    summarize_by_agent,
)
from .api_key import APIKey, APIKeyLimits, APIKeyUsageLimit, TokenType
from .issue import IssueReporter, IssueSeverity
from .exceptions import (
    AixplainV2Error,
    ResourceError,
    APIError,
    AixplainIssueError,
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
    "ContextOverflowStrategy",
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
    "Eval",
    "AgentEvaluationRow",
    "AgentEvaluationRun",
    "AgentEvaluationResultsChatbot",
    "EvalCase",
    "Dataset",
    "Metric",
    "MetricResponse",
    "compare_agents_side_by_side",
    "normalize_eval_results_dataframe",
    "Experiment",
    "ExperimentRun",
    "ExperimentRunDiff",
    "ExperimentRunDiffCase",
    "ExperimentRunDiffCaseList",
    "ExperimentLocalCache",
    "default_experiment_cache_dir",
    "EXPERIMENT_COMPARISON_COL_RUN_INDEX",
    "EXPERIMENT_COMPARISON_COL_RUN_CREATED_AT",
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
    "IssueReporter",
    "IssueSeverity",
    # Progress tracking
    "AgentProgressTracker",
    "ProgressFormat",
    # Exceptions
    "AixplainV2Error",
    "ResourceError",
    "APIError",
    "AixplainIssueError",
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
