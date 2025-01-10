from typing import Optional
from uuid import uuid4


class Record:
    def __init__(self, value: str, value_type: str = "text", id: Optional[str] = None, uri: str = "", attributes: dict = {}):
        self.value = value
        self.value_type = value_type
        self.id = id if id is not None else str(uuid4())
        self.uri = uri
        self.attributes = attributes

    def to_dict(self):
        return {
            "value": self.value,
            "value_type": self.value_type,
            "id": self.id,
            "uri": self.uri,
            "attributes": self.attributes,
        }
