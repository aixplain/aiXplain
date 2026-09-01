"""aiXplain SDK v2 - Modern Python SDK for the aiXplain platform."""

from .core import Aixplain
from .rlm import RLM, RLMResult
from .agent import (
    Agent,
    Artifact,
    Budget,
    BudgetDict,
    ContextOverflowStrategy,
    ContextOverflowStrategyValue,
    ConversationMessage,
    OutputFormat,
    OutputFormatValue,
    Task,
    TaskDict,
)
from .tool import Tool
from .skill import Skill
from .actions import Input, Inputs, Action, Actions
from .integration import TriggerTypeSpec, TriggerEventOption, TriggerTypes
from .trigger import (
    Trigger,
    TriggerConfiguration,
    TriggerConfigurationDict,
    TriggerRepeatRule,
    TriggerRepeatRuleDict,
)
from .file import File
from .graph import (
    AgentNode,
    Condition,
    ConditionalNode,
    Edge,
    Graph,
    InspectorNode,
    LLMNode,
    RetryPolicy,
    ScriptNode,
    StaticGraphStrategy,
    ToolNode,
)
from .resource import Page
from .upload_utils import FileUploader, upload_file, validate_file_for_upload
from .inspector import Inspector
from .session import (
    ExecutionConfig,
    ExecutionConfigDict,
    Session,
    SessionMessage,
    SessionMessageAttachment,
)
from .meta_agents import Debugger, DebugResult
from .agent_progress import AgentProgressTracker, ProgressFormat, ProgressFormatValue
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
from .api_key import (
    APIKey,
    APIKeyLimits,
    APIKeyLimitsDict,
    APIKeyUsageLimit,
    TokenType,
    TokenTypeValue,
)
from .code_utils import UtilityModelInput, UtilityModelInputDict
from .issue import IssueReporter, IssueSeverity, IssueSeverityValue
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
    DataType,
    SessionStatus,
    RunStatus,
    MessageRole,
    Reaction,
    AttachmentType,
    # Plain-data (Literal) forms of the input enums -- see docs/v2-plain-data.md
    AssetStatusValue,
    AttachmentTypeValue,
    AuthenticationSchemeValue,
    DataTypeValue,
    FileTypeValue,
    FunctionValue,
    LanguageValue,
    LicenseValue,
    OwnershipTypeValue,
    PrivacyValue,
    SortByValue,
    SortOrderValue,
    SplittingOptionsValue,
    StorageTypeValue,
    SupplierValue,
)

__all__ = [
    "Aixplain",
    "RLM",
    "RLMResult",
    "Agent",
    "Artifact",
    "Budget",
    "BudgetDict",
    "ContextOverflowStrategy",
    "ContextOverflowStrategyValue",
    "ConversationMessage",
    "OutputFormat",
    "OutputFormatValue",
    "Task",
    "TaskDict",
    "Tool",
    "Skill",
    "File",
    "Page",
    "Graph",
    "Edge",
    "Condition",
    "RetryPolicy",
    "StaticGraphStrategy",
    "LLMNode",
    "ToolNode",
    "AgentNode",
    "ScriptNode",
    "InspectorNode",
    "ConditionalNode",
    "FileUploader",
    "upload_file",
    "validate_file_for_upload",
    # Session classes
    "Session",
    "SessionMessage",
    "SessionMessageAttachment",
    "ExecutionConfig",
    "ExecutionConfigDict",
    # Inspector
    "Inspector",
    # Meta-agents
    "Debugger",
    "DebugResult",
    # Progress tracking
    "AgentProgressTracker",
    "ProgressFormat",
    "ProgressFormatValue",
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
    "APIKeyLimitsDict",
    "APIKeyUsageLimit",
    "TokenType",
    "TokenTypeValue",
    "IssueReporter",
    "IssueSeverity",
    "IssueSeverityValue",
    # Utility model inputs
    "UtilityModelInput",
    "UtilityModelInputDict",
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
    "DataType",
    "SessionStatus",
    "RunStatus",
    "MessageRole",
    "Reaction",
    "AttachmentType",
    # Plain-data (Literal) forms of the input enums
    "AssetStatusValue",
    "AttachmentTypeValue",
    "AuthenticationSchemeValue",
    "DataTypeValue",
    "FileTypeValue",
    "FunctionValue",
    "LanguageValue",
    "LicenseValue",
    "OwnershipTypeValue",
    "PrivacyValue",
    "SortByValue",
    "SortOrderValue",
    "SplittingOptionsValue",
    "StorageTypeValue",
    "SupplierValue",
    # Actions / Inputs hierarchy
    "Input",
    "Inputs",
    "Action",
    "Actions",
    # Triggers
    "Trigger",
    "TriggerConfiguration",
    "TriggerConfigurationDict",
    "TriggerRepeatRule",
    "TriggerRepeatRuleDict",
    "TriggerTypeSpec",
    "TriggerEventOption",
    "TriggerTypes",
]


def __getattr__(name: str):
    """PEP 562: warn on the deprecated ``Resource`` alias, matching ``Aixplain().Resource``.

    ``Resource`` is deliberately not a plain module attribute, and deliberately
    absent from ``__all__``: a plain ``from .file import Resource`` above, or
    listing it in ``__all__``, would fire the warning on every
    ``import aixplain.v2`` (and, transitively, every ``import aixplain`` — its
    ``from .v2 import *`` walks every name in this module's ``__all__``)
    regardless of whether the caller ever touches the name. This way only an
    actual access to ``aixplain.v2.Resource`` (or ``from aixplain.v2 import
    Resource``) does.
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
