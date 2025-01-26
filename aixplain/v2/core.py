import os
from typing import TypeVar
from .client import AixplainClient
from .api_key import APIKey
from .data import Data
from .dataset import Dataset
from .corpus import Corpus
from .model import Model
from .pipeline import Pipeline
from .agent import Agent
from .benchmark import Benchmark, BenchmarkJob
from .metric import Metric
from .finetune import Finetune
from .script import Script
from .wallet import Wallet
from .file import File
from . import enums
from .team_agent import TeamAgent

APIKeyType = TypeVar("APIKeyType", bound=APIKey)
DataType = TypeVar("DataType", bound=Data)
DatasetType = TypeVar("DatasetType", bound=Dataset)
CorpusType = TypeVar("CorpusType", bound=Corpus)
ModelType = TypeVar("ModelType", bound=Model)
PipelineType = TypeVar("PipelineType", bound=Pipeline)
AgentType = TypeVar("AgentType", bound=Agent)
BenchmarkType = TypeVar("BenchmarkType", bound=Benchmark)
BenchmarkJobType = TypeVar("BenchmarkJobType", bound=BenchmarkJob)
MetricType = TypeVar("MetricType", bound=Metric)
FinetuneType = TypeVar("FinetuneType", bound=Finetune)
ScriptType = TypeVar("ScriptType", bound=Script)
WalletType = TypeVar("WalletType", bound=Wallet)
FileType = TypeVar("FileType", bound=File)
TeamAgentType = TypeVar("TeamAgentType", bound=TeamAgent)


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

    APIKey: APIKeyType = None
    Data: DataType = None
    Dataset: DatasetType = None
    Corpus: CorpusType = None
    Model: ModelType = None
    Pipeline: PipelineType = None
    Agent: AgentType = None
    Benchmark: BenchmarkType = None
    BenchmarkJob: BenchmarkJobType = None
    Metric: MetricType = None
    Finetune: FinetuneType = None
    Script: ScriptType = None
    Wallet: WalletType = None
    File: FileType = None
    TeamAgent: TeamAgentType = None
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

    BACKEND_URL = "https://platform-api.aixplain.com"
    BENCHMARKS_BACKEND_URL = "https://platform-api.aixplain.com"
    MODELS_RUN_URL = "https://models.aixplain.com/api/v1/execute"
    PIPELINES_RUN_URL = "https://platform-api.aixplain.com/assets/pipeline/execution/run"

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
        api_key: str = None,
        backend_url: str = None,
        pipeline_url: str = None,
        model_url: str = None,
    ):
        """Initialize the Aixplain class.

        Args:
            api_key: str: The API key for the Aixplain API.
            backend_url: str: The URL for the backend.
            pipeline_url: str: The URL for the pipeline.
            model_url: str: The URL for the model.
        """
        self.api_key = api_key or os.getenv("TEAM_API_KEY")
        assert (
            self.api_key
        ), "API key is required. You should either pass it as an argument or set the TEAM_API_KEY environment variable."

        self.base_url = backend_url or os.getenv("BACKEND_URL") or self.BACKEND_URL
        self.pipeline_url = pipeline_url or os.getenv("PIPELINES_RUN_URL") or self.PIPELINES_RUN_URL
        self.model_url = model_url or os.getenv("MODELS_RUN_URL") or self.MODELS_RUN_URL

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
        self.APIKey = type("APIKey", (APIKey,), {"context": self})
        self.Data = type("Data", (Data,), {"context": self})
        self.Dataset = type("Dataset", (Dataset,), {"context": self})
        self.Corpus = type("Corpus", (Corpus,), {"context": self})
        self.Model = type("Model", (Model,), {"context": self})
        self.Pipeline = type("Pipeline", (Pipeline,), {"context": self})
        self.Agent = type("Agent", (Agent,), {"context": self})
        self.Benchmark = type("Benchmark", (Benchmark,), {"context": self})
        self.BenchmarkJob = type("BenchmarkJob", (BenchmarkJob,), {"context": self})
        self.Metric = type("Metric", (Metric,), {"context": self})
        self.Finetune = type("Finetune", (Finetune,), {"context": self})
        self.Script = type("Script", (Script,), {"context": self})
        self.Wallet = type("Wallet", (Wallet,), {"context": self})
        self.File = type("File", (File,), {"context": self})
        self.TeamAgent = type("TeamAgent", (TeamAgent,), {"context": self})
