from enum import Enum


class IndexStores(Enum):
    """Enumeration of available index store providers in the aiXplain system.

    This enum defines the different index store providers that can be used for
    storing and retrieving indexed data, along with their identifiers.

    Attributes:
        AIR (dict): AIR index store configuration with name and ID.
        VECTARA (dict): Vectara index store configuration with name and ID.
        GRAPHRAG (dict): GraphRAG index store configuration with name and ID.
        ZERO_ENTROPY (dict): Zero Entropy index store configuration with name and ID.
    """
    AIR = {"name": "air", "id": "66eae6656eb56311f2595011"}
    VECTARA = {"name": "vectara", "id": "655e20f46eb563062a1aa301"}
    GRAPHRAG = {"name": "graphrag", "id": "67dd6d487cbf0a57cf4b72f3"}
    ZERO_ENTROPY = {"name": "zeroentropy", "id": "6807949168e47e7844c1f0c5"}

    def __str__(self) -> str:
        """Return the name of the index store.

        Returns:
            str: The name value from the index store configuration.
        """
        return self.value["name"]

    def get_model_id(self) -> str:
        """Return the model ID of the index store.

        Returns:
            str: The ID value from the index store configuration.
        """
        return self.value["id"]
