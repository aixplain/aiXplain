from pydantic import BaseModel, ConfigDict, field_validator
from typing import Text, Optional, ClassVar, Dict, Union
from aixplain.enums import IndexStores, EmbeddingModel
from abc import ABC, abstractmethod
from aixplain.factories import ModelFactory
from aixplain.enums import Function


class BaseIndexParams(BaseModel, ABC):
    """Abstract base class for index parameters.

    This class defines the common parameters and functionality for all index types.
    It uses Pydantic for data validation and serialization.

    Attributes:
        model_config (ConfigDict): Pydantic configuration using enum values.
        name (Text): Name of the index.
        description (Optional[Text]): Description of the index. Defaults to "".
    """

    model_config = ConfigDict(use_enum_values=True)
    name: Text
    description: Optional[Text] = ""

    def to_dict(self) -> Dict:
        """Convert the parameters to a dictionary format.

        Converts the parameters to a dictionary suitable for API requests,
        renaming 'name' to 'data' in the process.

        Returns:
            Dict: Dictionary representation of the parameters.
        """
        data = self.model_dump(exclude_none=True)
        data["data"] = data.pop("name")
        return data

    @property
    @abstractmethod
    def id(self) -> str:
        """Abstract property that must be implemented in subclasses."""
        pass


class BaseIndexParamsWithEmbeddingModel(BaseIndexParams, ABC):
    """Abstract base class for index parameters that require an embedding model.

    This class extends BaseIndexParams to add support for embedding model configuration,
    including model selection and embedding size settings.

    Attributes:
        embedding_model (Optional[Union[EmbeddingModel, str]]): Model to use for text
            embeddings. Defaults to EmbeddingModel.OPENAI_ADA002.
        embedding_size (Optional[int]): Size of the embeddings to generate.
            Defaults to None.
    """

    embedding_model: Optional[Union[EmbeddingModel, str]] = EmbeddingModel.OPENAI_ADA002
    embedding_size: Optional[int] = None

    @field_validator("embedding_model")
    def validate_embedding_model(cls, model_id) -> str:
        """Validate that the provided model is a text embedding model.

        Args:
            model_id (Union[EmbeddingModel, str]): Model ID or enum value to validate.

        Returns:
            str: The validated model ID.

        Raises:
            ValueError: If the model is not a text embedding model.
        """
        model = ModelFactory.get(model_id)
        if model.function == Function.TEXT_EMBEDDING:
            return model_id
        else:
            raise ValueError("This is not an embedding model")

    def to_dict(self) -> Dict:
        """Convert the parameters to a dictionary format.

        Extends the base to_dict method to handle embedding-specific parameters,
        renaming fields and restructuring as needed for the API.

        Returns:
            Dict: Dictionary representation of the parameters with embedding
                configuration properly formatted.
        """
        data = super().to_dict()
        data["model"] = data.pop("embedding_model")

        if data.get("embedding_size"):
            data["additional_params"] = {"embedding_size": data.pop("embedding_size")}
        return data


class VectaraParams(BaseIndexParams):
    """Parameters for creating a Vectara index.

    This class defines the configuration for Vectara's vector search index.

    Attributes:
        _id (ClassVar[str]): Static model ID for Vectara index type.
    """

    _id: ClassVar[str] = IndexStores.VECTARA.get_model_id()

    @property
    def id(self) -> str:
        """Get the model ID for Vectara index type.

        Returns:
            str: The Vectara model ID.
        """
        return self._id


class ZeroEntropyParams(BaseIndexParams):
    """Parameters for creating a Zero Entropy index.

    This class defines the configuration for Zero Entropy's vector search index.

    Attributes:
        _id (ClassVar[str]): Static model ID for Zero Entropy index type.
    """

    _id: ClassVar[str] = IndexStores.ZERO_ENTROPY.get_model_id()

    @property
    def id(self) -> str:
        """Get the model ID for Zero Entropy index type.

        Returns:
            str: The Zero Entropy model ID.
        """
        return self._id


class AirParams(BaseIndexParamsWithEmbeddingModel):
    """Parameters for creating an AIR (aiXplain Index and Retrieval) index.

    This class defines the configuration for AIR's vector search index,
    including embedding model settings.

    Attributes:
        _id (ClassVar[str]): Static model ID for AIR index type.
    """

    _id: ClassVar[str] = IndexStores.AIR.get_model_id()

    @property
    def id(self) -> str:
        """Get the model ID for AIR index type.

        Returns:
            str: The AIR model ID.
        """
        return self._id


class GraphRAGParams(BaseIndexParamsWithEmbeddingModel):
    """Parameters for creating a GraphRAG (Graph-based Retrieval-Augmented Generation) index.

    This class defines the configuration for GraphRAG's vector search index,
    including embedding model and LLM settings.

    Attributes:
        _id (ClassVar[str]): Static model ID for GraphRAG index type.
        llm (Optional[Text]): ID of the LLM to use for generation. Defaults to None.
    """

    _id: ClassVar[str] = IndexStores.GRAPHRAG.get_model_id()
    llm: Optional[Text] = None

    @property
    def id(self) -> str:
        """Get the model ID for GraphRAG index type.

        Returns:
            str: The GraphRAG model ID.
        """
        return self._id
