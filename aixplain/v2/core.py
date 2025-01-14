import os
from typing import TypeVar
from .client import AixplainClient
from .model import Model
from .pipeline import Pipeline
from .agent import Agent
from .benchmark import Benchmark, BenchmarkJob
from .metric import Metric
from .finetune import Finetune
from .script import Script
from . import enums


ModelType = TypeVar("ModelType", bound=Model)
PipelineType = TypeVar("PipelineType", bound=Pipeline)
AgentType = TypeVar("AgentType", bound=Agent)
BenchmarkType = TypeVar("BenchmarkType", bound=Benchmark)
BenchmarkJobType = TypeVar("BenchmarkJobType", bound=BenchmarkJob)
MetricType = TypeVar("MetricType", bound=Metric)
FinetuneType = TypeVar("FinetuneType", bound=Finetune)
ScriptType = TypeVar("ScriptType", bound=Script)


class Aixplain:
    """Main class for the Aixplain API.

    Attributes:
        _instance: Aixplain: The unique instance of the Aixplain class.
        api_key: str: The API key for the Aixplain API.
        base_url: str: The URL for the backend.
        pipeline_url: str: The URL for the pipeline.
        model_url: str: The URL for the model.
        client: AixplainClient: The client for the Aixplain API.
        Model: type: The model class.
        Pipeline: type: The pipeline class.
        Agent: type: The agent class.
        Benchmark: type: The benchmark class.
        BenchmarkJob: type: The benchmark job class.
    """

    # Here below we're defining both resources and enums as class level attributes manually instead of populating them dynamically
    # This has two benefits:
    # 1. We can benefit from the type checking and autocompletion of the IDE.
    # 2. We can access enums and resources without having to import them.

    Model: ModelType = None
    Pipeline: PipelineType = None
    Agent: AgentType = None
    Benchmark: BenchmarkType = None
    BenchmarkJob: BenchmarkJobType = None
    Metric: MetricType = None
    Finetune: FinetuneType = None
    Script: ScriptType = None

    Function = enums.Function
    Supplier = enums.Supplier
    Language = enums.Language
    License = enums.License

    AssetStatus = enums.AssetStatus
    DataSplit = enums.DataSplit
    DataSubtype = enums.DataSubtype
    DataType = enums.DataType
    ErrorHandler = enums.ErrorHandler
    FileType = enums.FileType
    OnboardStatus = enums.OnboardStatus
    OwnershipType = enums.OwnershipType
    Privacy = enums.Privacy
    ResponseStatus = enums.ResponseStatus
    SortBy = enums.SortBy
    SortOrder = enums.SortOrder
    StorageType = enums.StorageType

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern for the Aixplain class.
        Otherwise, the environment variables will be overwritten in multiple instances.

        TODO: This should be removed once the factory classes are removed.
        """
        if not cls._instance:
            cls._instance = super(Aixplain, cls).__new__(cls)

        return cls._instance

    def __init__(
        self,
        api_key: str,
        backend_url: str = "https://platform-api.aixplain.com",
        pipeline_url: str = "https://platform-api.aixplain.com/assets/pipeline/execution/run",
        model_url: str = "https://models.aixplain.com/api/v1/execute",
    ):
        """Initialize the Aixplain class.

        Args:
            api_key: str: The API key for the Aixplain API.
            backend_url: str: The URL for the backend.
            pipeline_url: str: The URL for the pipeline.
            model_url: str: The URL for the model.
        """
        self.api_key = api_key
        self.base_url = backend_url
        self.pipeline_url = pipeline_url
        self.model_url = model_url
        self.init_env()
        self.init_client()
        self.init_resources()

    def init_client(self):
        """Initialize the client."""
        self.client = AixplainClient(
            base_url=self.base_url,
            team_api_key=self.api_key,
        )

    def init_env(self):
        """Initialize the environment variables.

        This is required for the legacy use of the factory classes.
        """
        os.environ["TEAM_API_KEY"] = self.api_key
        os.environ["BACKEND_URL"] = self.base_url
        os.environ["PIPELINE_URL"] = self.pipeline_url
        os.environ["MODEL_URL"] = self.model_url

    def init_resources(self):
        """Initialize the resources.

        We're dynamically creating the classes here to avoid potential race
        conditions when using class level attributes
        """
        self.Model = type("Model", (Model,), {"context": self})
        self.Pipeline = type("Pipeline", (Pipeline,), {"context": self})
        self.Agent = type("Agent", (Agent,), {"context": self})
        self.Benchmark = type("Benchmark", (Benchmark,), {"context": self})
        self.BenchmarkJob = type("BenchmarkJob", (BenchmarkJob,), {"context": self})
        self.Metric = type("Metric", (Metric,), {"context": self})
        self.Finetune = type("Finetune", (Finetune,), {"context": self})
        self.Script = type("Script", (Script,), {"context": self})
