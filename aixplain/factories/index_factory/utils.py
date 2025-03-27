from pydantic import BaseModel, ConfigDict
from typing import Text, Optional, Tuple, Dict
from aixplain.enums import IndexStores, EmbeddingModel

class BaseIndexParams(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: Text
    description: Optional[Text] = ""

    def to_dict(self):
        return self.model_dump()
    
class IndexParamsWithEmbeddingModel(BaseIndexParams):
    
    embedding_model: Optional[EmbeddingModel] = EmbeddingModel.OPENAI_ADA002

    def to_dict(self):
        data = super().to_dict()
        data["model"] = data.pop("embedding_model").value
        return data

class VectaraParams(BaseIndexParams):
    
    def get_model_id(self):
        return IndexStores.VECTARA.get_model_id()
    

class ZeroEntropyParams(BaseIndexParams):
    
    def get_model_id(self):
        raise ValueError("ZeroEntropy is not supported yet")
        # return IndexStores.ZERO_ENTROPY.get_model_id()

class AirParams(IndexParamsWithEmbeddingModel):

    def get_model_id(self):
        return IndexStores.AIR.get_model_id()
    

class GraphRAGParams(IndexParamsWithEmbeddingModel):
    llm_model: Optional[Text] = "669a63646eb56306647e1091" # Gpt-4o-mini

    def get_model_id(self):
        return IndexStores.GRAPHRAG.get_model_id()
    
