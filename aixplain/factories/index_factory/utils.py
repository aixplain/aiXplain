
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Text, Optional, ClassVar, Dict, Union
from aixplain.enums import IndexStores, EmbeddingModel
from abc import ABC, abstractmethod
from aixplain.factories import ModelFactory
from aixplain.enums import Function


class BaseIndexParams(BaseModel, ABC):
    model_config = ConfigDict(use_enum_values=True)
    name: Text
    description: Optional[Text] = ""

    def to_dict(self):
        data = self.model_dump(exclude_none=True)
        data["data"] = data.pop("name")
        return data

    @property
    @abstractmethod
    def id(self) -> str:
        """Abstract property that must be implemented in subclasses."""
        pass


class BaseIndexParamsWithEmbeddingModel(BaseIndexParams, ABC):

    embedding_model: Optional[Union[EmbeddingModel, str]] = EmbeddingModel.OPENAI_ADA002
    embedding_size: Optional[int] = None

    @field_validator('embedding_model')
    def validate_embedding_model(cls, model_id) -> bool:
        model = ModelFactory.get(model_id)
        if model.function == Function.TEXT_EMBEDDING:
            return model_id
        else:
            raise ValueError("This is not an embedding model")


    def to_dict(self):
        data = super().to_dict()
        data["model"] = data.pop("embedding_model")

        if data.get("embedding_size"):
            data["additional_params"] = {"embedding_size": data.pop("embedding_size")}
        return data

class VectaraParams(BaseIndexParams):
    _id: ClassVar[str] = IndexStores.VECTARA.get_model_id()

    @property
    def id(self) -> str:
        return self._id


class ZeroEntropyParams(BaseIndexParams):
    _id: ClassVar[str] = IndexStores.ZERO_ENTROPY.get_model_id()

    @property
    def id(self) -> str:
        return self._id


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
