from pydantic import BaseModel, ConfigDict
from typing import Text, Optional, Tuple, Dict
from aixplain.enums import IndexStores, EmbeddingModel

class BaseIndexParams(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    name: Text
    description: Optional[Text] = ""

class VectaraParams(BaseIndexParams):
    pass

class ZeroEntropyParams(BaseIndexParams):
    pass

class AirParams(BaseIndexParams):
    embedding_model: Optional[EmbeddingModel] = EmbeddingModel.OPENAI_ADA002 # should allow all embedding model ids as this is not very scalable

class GraphRAGParams(BaseIndexParams):
    embedding_model: Optional[EmbeddingModel] = EmbeddingModel.OPENAI_ADA002
    llm_model: Optional[Text] = "669a63646eb56306647e1091" # Gpt-4o-mini

def get_model_id_and_payload(params: BaseIndexParams) -> Tuple[Text, Dict]:
    payload = params.model_dump()
    if isinstance(params, AirParams):
        model_id = IndexStores.AIR.get_model_id()
        payload["model"] = payload.pop("embedding_model")
    elif isinstance(params, GraphRAGParams):
        model_id = IndexStores.GRAPHRAG.get_model_id()
        payload["model"] = payload.pop("embedding_model")
    elif isinstance(params, VectaraParams):
        model_id = IndexStores.VECTARA.get_model_id()
    elif isinstance(params, ZeroEntropyParams):
        # model_id = IndexStores.ZERO_ENTROPY.get_model_id()
        raise ValueError("ZeroEntropy is not supported yet")
    else:
        raise ValueError(f"Invalid index params: {params}")
    return model_id, payload
