from typing import List, Union, TYPE_CHECKING
from typing_extensions import Unpack, NotRequired

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
    dataset_list: List["Dataset"]
    model: Union["Model", str]
    prompt_template: NotRequired[str]
    hyperparameters: NotRequired["Hyperparameters"]
    train_percentage: NotRequired[float]
    dev_percentage: NotRequired[float]


class Finetune(
    BaseResource,
    CreateResourceMixin[FinetuneCreateParams, "Finetune"],
):
    """Resource for finetunes."""

    RESOURCE_PATH = "sdk/finetunes"

    @classmethod
    def create(
        cls,
        name: str,
        dataset_list: List[Union[Dataset, str]],
        model: Union[Model, str],
        prompt_template: str = None,
        hyperparameters: Hyperparameters = None,
        train_percentage: float = 100,
        dev_percentage: float = 0,
    ) -> "Finetune":
        from aixplain.factories import FinetuneFactory

        return FinetuneFactory.create(
            name,
            dataset_list,
            model,
            prompt_template=prompt_template,
            hyperparameters=hyperparameters,
            train_percentage=train_percentage,
            dev_percentage=dev_percentage,
        )
