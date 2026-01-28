"""Core module for aiXplain v2 API."""

import os
from typing import Optional, TypeVar

from .client import AixplainClient
from .model import Model
from .agent import Agent
from .utility import Utility
from .tool import Tool
from .integration import Integration
from .file import Resource
from .inspector import Inspector
from .meta_agents import Debugger
from . import enums


ModelType = TypeVar("ModelType", bound=Model)
AgentType = TypeVar("AgentType", bound=Agent)
UtilityType = TypeVar("UtilityType", bound=Utility)
ToolType = TypeVar("ToolType", bound=Tool)
IntegrationType = TypeVar("IntegrationType", bound=Integration)
ResourceType = TypeVar("ResourceType", bound=Resource)
InspectorType = TypeVar("InspectorType", bound=Inspector)
DebuggerType = TypeVar("DebuggerType", bound=Debugger)


class Aixplain:
    """Main class for the Aixplain API.

    This class can be instantiated multiple times with different API keys,
    allowing for multi-instance usage with different authentication contexts.
    """

    # Here below we're defining both resources and enums as class level
    # attributes manually instead of populating them dynamically
    # This has two benefits:
    # 1. We can benefit from the type checking and autocompletion of the IDE.
    # 2. We can access enums and resources without having to import them.

    Model: ModelType = None
    Agent: AgentType = None
    Utility: UtilityType = None
    Tool: ToolType = None
    Integration: IntegrationType = None
    Resource: ResourceType = None
    Inspector: InspectorType = None
    Debugger: DebuggerType = None

    Function = enums.Function
    Supplier = enums.Supplier
    Language = enums.Language
    License = enums.License

    AssetStatus = enums.AssetStatus
    ErrorHandler = enums.ErrorHandler
    FileType = enums.FileType
    OnboardStatus = enums.OnboardStatus
    OwnershipType = enums.OwnershipType
    Privacy = enums.Privacy
    ResponseStatus = enums.ResponseStatus
    SortBy = enums.SortBy
    SortOrder = enums.SortOrder
    StorageType = enums.StorageType

    BACKEND_URL = "https://platform-api.aixplain.com"
    BENCHMARKS_BACKEND_URL = "https://platform-api.aixplain.com"
    MODELS_RUN_URL = "https://models.aixplain.com/api/v2/execute"
    PIPELINES_RUN_URL = "https://platform-api.aixplain.com/assets/pipeline/execution/run"

    def __init__(
        self,
        api_key: Optional[str] = None,
        backend_url: Optional[str] = None,
        pipeline_url: Optional[str] = None,
        model_url: Optional[str] = None,
    ) -> None:
        """Initialize the Aixplain class.

        Args:
            api_key: str: The API key for the Aixplain API.
            backend_url: str: The URL for the backend.
            pipeline_url: str: The URL for the pipeline.
            model_url: str: The URL for the model.
        """
        self.api_key = api_key or os.getenv("TEAM_API_KEY") or ""
        assert self.api_key, (
            "API key is required. You should either pass it as an argument or "
            "set the TEAM_API_KEY environment variable."
        )

        self.backend_url = backend_url or os.getenv("BACKEND_URL") or self.BACKEND_URL
        self.pipeline_url = pipeline_url or os.getenv("PIPELINES_RUN_URL") or self.PIPELINES_RUN_URL
        self.model_url = model_url or os.getenv("MODELS_RUN_URL") or self.MODELS_RUN_URL

        self.init_client()
        self.init_resources()

    def init_client(self) -> None:
        """Initialize the client."""
        self.client = AixplainClient(
            base_url=self.backend_url,
            team_api_key=self.api_key,
        )

    def init_resources(self) -> None:
        """Initialize the resources.

        We're dynamically creating the classes here to avoid potential race
        conditions when using class level attributes
        """
        self.Model = type("Model", (Model,), {"context": self})
        self.Agent = type("Agent", (Agent,), {"context": self})
        self.Utility = type("Utility", (Utility,), {"context": self})
        self.Tool = type("Tool", (Tool,), {"context": self})
        self.Integration = type("Integration", (Integration,), {"context": self})
        self.Resource = type("Resource", (Resource,), {"context": self})
        self.Inspector = type("Inspector", (Inspector,), {"context": self})
        self.Debugger = type("Debugger", (Debugger,), {"context": self})
