from typing import Dict


class E2eSearchCost:
    def __init__(
        self,
        training: Dict,
        inference: Dict,
        hosting: Dict,
    ) -> None:
        """Create a e2eSearchCost object with training, inference, and hosting cost information.

        Args:
            training (Dict): Dictionary containing training cost information.
            inference (Dict): Dictionary containing inference cost information.
            hosting (Dict): Dictionary containing hosting cost information.
        """
        self.training = training
        self.inference = inference
        self.hosting = hosting

    def to_dict(self) -> Dict:
        """Convert the e2eSearchCost object to a dictionary.

        Returns:
            Dict: A dictionary representation of the e2eSearchCost object.
        """
        return {"trainingCost": self.training, "inferenceCost": self.inference, "hostingCost": self.hosting}
