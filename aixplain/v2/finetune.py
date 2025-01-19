from typing import List, Union
from typing_extensions import Unpack

from aixplain.v2.resource import (
    BaseResource,
    CreateResourceMixin,
    BareCreateParams,
)

from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model
from aixplain.modules.finetune import Hyperparameters


class FinetuneCreateParams(BareCreateParams):
    """Parameters for creating a finetune.

    Attributes:
        name: str: The name of the finetune.
        dataset_list: List[Dataset]: The list of datasets.
        model: Union[Model, str]: The model.
        prompt_template: str: The prompt template.
        hyperparameters: Hyperparameters: The hyperparameters.
        train_percentage: float: The train percentage.
        dev_percentage: float: The dev percentage.
    """

    name: str
    dataset_list: List[Dataset]
    model: Union[Model, str]
    prompt_template: str
    hyperparameters: Hyperparameters
    train_percentage: float
    dev_percentage: float


class Finetune(
    BaseResource,
    CreateResourceMixin[FinetuneCreateParams, "Finetune"],
):
    """Resource for finetunes."""

    RESOURCE_PATH = "sdk/finetunes"

    @classmethod
    def create(cls, **kwargs: Unpack[FinetuneCreateParams]) -> "Finetune":
        from aixplain.factories import FinetuneFactory

        return Finetune(FinetuneFactory.create(**kwargs))
