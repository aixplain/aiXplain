from enum import Enum


class IndexStores(Enum):
    AIR = {"name": "air", "id": "66eae6656eb56311f2595011"}
    VECTARA = {"name": "vectara", "id": "655e20f46eb563062a1aa301"}
    GRAPHRAG = {"name": "graphrag", "id": "67dd6d487cbf0a57cf4b72f3"}
    ZERO_ENTROPY = {"name": "zeroentropy", "id": "6807949168e47e7844c1f0c5"}

    def __str__(self):
        return self.value["name"]

    def get_model_id(self):
        return self.value["id"]
