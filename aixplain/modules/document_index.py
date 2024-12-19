from typing import List

class DocumentIndex:
    def __init__(self, value: str, value_type: str = "text", id: int = 0, uri: str = "", attributes: dict = {}):
        self.value = value
        self.value_type = value_type
        self.id = id
        self.uri = uri
        self.attributes = attributes
    
    def from_list(documents: List[str]):
        return [DocumentIndex(value=doc, id=i) for i, doc in enumerate(documents)]
