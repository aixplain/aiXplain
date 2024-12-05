from aixplain.modules.model import Model
from aixplain.modules.model.response import ModelResponse

class IndexModel(Model):

    def search(self, query: str, top_k: int = 10) -> ModelResponse:
        data = {
            "action": "search",
            "data": query,
            "payload": {
                "filters": {},
                "top_k": top_k
            }
        }
        return self.run(data=data)

    def ingest(self, documents: list) -> ModelResponse:
        payloads = [{"value": doc, "value_type": "text", "id": str(i)} for i, doc in enumerate(documents)]
        data = {
            "action": "ingest",
            "data": "",
            "payload": {
                "payloads": payloads
            }
        }
        return self.run(data=data)
