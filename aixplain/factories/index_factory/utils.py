from pydantic import BaseModel, ConfigDict
from typing import Text, Optional, ClassVar
from aixplain.enums import IndexStores, EmbeddingModel


class BaseIndexParams(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    data: Text
    description: Optional[Text] = ""

    def to_dict(self):
        return self.model_dump(exclude_none=True)


class BaseIndexParamsWithEmbeddingModel(BaseIndexParams):
    embedding_model: Optional[EmbeddingModel] = EmbeddingModel.OPENAI_ADA002

    def to_dict(self):
        data = super().to_dict()
        data["model"] = data.pop("embedding_model").value if isinstance(self.embedding_model, EmbeddingModel) else data.pop("embedding_model")
        return data


class VectaraParams(BaseIndexParams):
    id: ClassVar[str] = IndexStores.VECTARA.get_model_id()
    

class ZeroEntropyParams(BaseIndexParams):
    id: ClassVar[str] = ""

    def __init__(self, **kwargs):
        raise ValueError("ZeroEntropy is not supported yet")


class AirParams(BaseIndexParamsWithEmbeddingModel):
    id: ClassVar[str] = IndexStores.AIR.get_model_id()
    

class GraphRAGParams(BaseIndexParamsWithEmbeddingModel):
    id: ClassVar[str] = IndexStores.GRAPHRAG.get_model_id()
    llm_model: Optional[Text] = None
