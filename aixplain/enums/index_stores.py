from enum import Enum


class IndexStores(Enum):
    AIR = {"name": "air", "id": "66eae6656eb56311f2595011"}
    VECTARA = {"name": "vectara", "id": "655e20f46eb563062a1aa301"}
    # GRAPHRAG = {"name": "graphrag", "id": ""}
    # ZERO_ENTROPY = {"name": "zero_entropy", "id": ""}

    def __str__(self):
        return self.value["name"]

    def get_model_id(self):
        return self.value["id"]
