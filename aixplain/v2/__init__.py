"""aiXplain SDK v2 - Modern Python SDK for the aiXplain platform."""

from .core import Aixplain
from .rlm import RLM, RLMResult
from .utility import Utility
from .agent import Agent, Artifact, Budget, ContextOverflowStrategy
from .tool import Tool
from .skill import Skill
from .actions import Input, Inputs, Action, Actions
from .integration import TriggerTypeSpec, TriggerEventOption, TriggerTypes
from .trigger import Trigger, TriggerConfiguration, TriggerRepeatRule
from .file import File
from .resource import Page
from .upload_utils import FileUploader, upload_file, validate_file_for_upload
from .inspector import Inspector
from .session import (
    ExecutionConfig,
    Session,
    SessionMessage,
    SessionMessageAttachment,
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
    UntrustedURLError,
)
from .enums import (
    AuthenticationScheme,
    FileContentType,
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
    SessionStatus,
    RunStatus,
    MessageRole,
    Reaction,
    AttachmentType,
)

__all__ = [
    "Aixplain",
    "RLM",
    "RLMResult",
    "Utility",
    "Agent",
    "Artifact",
    "Budget",
    "ContextOverflowStrategy",
    "Tool",
    "Skill",
    "Resource",
    "File",
    "Page",
    "FileUploader",
    "upload_file",
    "validate_file_for_upload",
    # Session classes
    "Session",
    "SessionMessage",
    "SessionMessageAttachment",
    "ExecutionConfig",
    # Inspector
    "Inspector",
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
    "UntrustedURLError",
    # V2 enum exports
    "AuthenticationScheme",
    "FileContentType",
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
    "SessionStatus",
    "RunStatus",
    "MessageRole",
    "Reaction",
    "AttachmentType",
    # Actions / Inputs hierarchy
    "Input",
    "Inputs",
    "Action",
    "Actions",
    # Triggers
    "Trigger",
    "TriggerConfiguration",
    "TriggerRepeatRule",
    "TriggerTypeSpec",
    "TriggerEventOption",
    "TriggerTypes",
]


def __getattr__(name: str):
    """PEP 562: warn on the deprecated ``Resource`` alias, matching ``Aixplain().Resource``.

    ``Resource`` is deliberately not a plain module attribute here: a plain
    ``from .file import Resource`` above would fire the warning on every
    ``import aixplain.v2`` regardless of whether the caller ever touches the
    name. This way only an actual access to ``aixplain.v2.Resource`` (or
    ``from aixplain.v2 import Resource``) does.
    """
    if name == "Resource":
        import warnings

        warnings.warn(
            "`aixplain.v2.Resource` is deprecated; use `aixplain.v2.File` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return File
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
