import os
import inspect
from enum import Enum

from .client import AixplainClient
from . import enums
from . import enums_include


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
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern for the Aixplain class.
        Otherwise, the environment variables will be overwritten in multiple instances.

        TODO: This should be removed once the factory classes are removed.
        """
        if not cls._instance:
            cls._instance = super(Aixplain, cls).__new__(cls)

        for name, obj in inspect.getmembers(enums, inspect.isclass):
            if issubclass(obj, Enum):
                setattr(cls, name, obj)

        for name, obj in inspect.getmembers(enums_include, inspect.isclass):
            if issubclass(obj, Enum):
                setattr(cls, name, obj)

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
        from .model import Model
        from .pipeline import Pipeline
        from .agent import Agent

        self.Model = type("Model", (Model,), {"context": self})
        self.Pipeline = type("Pipeline", (Pipeline,), {"context": self})
        self.Agent = type("Agent", (Agent,), {"context": self})
