from pydantic import BaseModel, ConfigDict
from typing import Text, Optional, ClassVar
from aixplain.enums import IndexStores, EmbeddingModel
from abc import ABC, abstractmethod


class BaseIndexParams(BaseModel, ABC):
    model_config = ConfigDict(use_enum_values=True)
    data: Text
    description: Optional[Text] = ""

    def to_dict(self):
        return self.model_dump(exclude_none=True)

    @property
    @abstractmethod
    def id(self) -> str:
        """Abstract property that must be implemented in subclasses."""
        pass


class BaseIndexParamsWithEmbeddingModel(BaseIndexParams, ABC):
    embedding_model: Optional[EmbeddingModel] = EmbeddingModel.OPENAI_ADA002

    def to_dict(self):
        data = super().to_dict()
        data["model"] = (
            data.pop("embedding_model").value
            if isinstance(self.embedding_model, EmbeddingModel)
            else data.pop("embedding_model")
        )
        return data


class VectaraParams(BaseIndexParams):
    _id: ClassVar[str] = IndexStores.VECTARA.get_model_id()

    @property
    def id(self) -> str:
        return self._id


class ZeroEntropyParams(BaseIndexParams):
    _id: ClassVar[str] = ""

    def __init__(self, **kwargs):
        raise ValueError("ZeroEntropy is not supported yet")


class AirParams(BaseIndexParamsWithEmbeddingModel):
    _id: ClassVar[str] = IndexStores.AIR.get_model_id()

    @property
    def id(self) -> str:
        return self._id


class GraphRAGParams(BaseIndexParamsWithEmbeddingModel):
    _id: ClassVar[str] = IndexStores.GRAPHRAG.get_model_id()
    llm: Optional[Text] = None

    @property
    def id(self) -> str:
        return self._id
